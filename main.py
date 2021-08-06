import requests
import multiprocessing as mp
import subprocess
import datetime
import configparser
from lib import *
from gui import seriesPickerMain, datePicker, downloadPckerMain
import time
from bs4 import BeautifulSoup, Doctype
from pprint import pprint, pformat


import os
import sys
import logging


logging.basicConfig(
     filename='log.log',
     level=logging.INFO, 
     format="%(asctime)s [%(levelname)s] %(message)s",
     datefmt='%H:%M:%S'
 )

# set up logging to console
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

logger = logging.getLogger(__name__)


# Need youtube-dl.exe in the same dir as this
# Need ffmpeg installed in C:\ffmpeg
# Need C:\ffmpeg\bin in PATH

def main():
    config = configparser.ConfigParser()
    config.read('config.cfg')
    download_folder = config['DEFAULT']['DownloadFolder']
    parallel = config['DEFAULT'].getboolean('ParallelDownloads')
    if not download_folder:
        logger.error('Need to set download folder in config.cfg!')
        raise ValueError('Need to set download folder in config.cfg!')
    if not os.path.exists(download_folder):
        os.mkdir(download_folder)
    logger.info('Downloading all files to %s' % download_folder)
    logger.info("You can change the download location in configs.py")
    series = seriesPickerMain()
    if not series:
        print("Goodbye!")
        return
    date_selected = datePicker()
    if not date_selected:
        print('Goodbye!')
        return
    scheduleDict = getSchedule(series, date_selected)
    pickedNames = downloadPckerMain(scheduleDict)
    if not pickedNames:
        logger.info('No shows picked, exiting...')
        return

    res = [] #pruned dict
    for dct in scheduleDict:
        if dct['name'] in pickedNames:
            res.append(dct)
    errors = downloader(res, download_folder, parallel=parallel)


    if errors:
        raise RuntimeError('Encountered partial errors while running. Please consult the logs.')


def downloader(res, download_folder, parallel=False):
    download_errors = []
    if parallel:
        logger.warning("Using parallel downloads. If any errors occur, they'll be harder to debug.")
        logger.warning("This setting can be turned off in config.cfg")
        ncount = min(mp.cpu_count(), len(res))
        with mp.Pool(processes=ncount) as pool:
            download_errors = set(pool.starmap(_download_child, [(dct, download_folder) for dct in res])) - {None}
    else:
        for dct in res:
            download_res = _download_child(dct, download_folder)
            if download_res is not None:
                download_errors.append(download_res)

    logger.info('Downloaded %d/%d files', len(res)-len(download_errors), len(res))

    if download_errors:
        logger.info('Encountered errors while downloading the following:')
        logger.info('\n'.join(download_errors))
        logger.info('Check the log file for stderr')
    return len(download_errors)
        
def _download_child(dct, download_folder):
    logger.info('downloading %s via %s', dct['name'], dct['url'])
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(dir_path, 'youtube-dl.exe')
    download_folder = os.path.join(download_folder, '%(title)s-%(id)s.%(ext)s')
    cmd = [filepath, dct['url'], '--output', download_folder]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        if proc.poll() or proc.returncode is not None:
            break
        line = proc.stdout.readline()
        if not line:
            time.sleep(3)
        else:
            line = line.strip()
            if '%' in line:
                # download percentage
                print(line, end='\r')
            else:
                print(line)
    if not proc.returncode:
        logger.info('Finished %s', dct['name'])
    else:
        stdout, stderr = proc.communicate()
        logger.error('Encountered error as follows')
        logger.error('STDOUT: \n%s', stdout)
        logger.error('STDERR: \n%s', stderr)
        return dct['name'], stderr



def getSchedule(series, date):
    date = date.strftime('%Y-%m-%d')
    url = getURL(series, date=date)
    logger.info('Using %s to grab the schedule for %s on %s' % (url, series, date,))
    r = requests.get(url)
    assert r.status_code == 200
    html = BeautifulSoup(r.text, "html.parser" )

    html = stripHTML(html)
    
    res = parseSeries(html) if 'series/print' in url else parseSchedule(html)

    return res


def stripHTML(html):
    # Strip out all the crap we don't care about
    for item in html.contents:
        if isinstance(item, (Doctype)):
            item.extract()
    for s in html(['script', 'style']):
        s.extract()
    for item in html.findAll('span', attrs={'class':'sponsor'}):
        item.decompose()
    for item in html.findAll('span', attrs={'class':'time'}):
        item.decompose()
    for item in html.findAll('span', attrs={'class':'dispFullAbstract'}):
        item.decompose()
    for item in html.findAll('span', attrs={'class':'abstract'}):
        item.decompose()

    return html


def parseSchedule(html):
    raise RuntimeError('TODO!')

def parseSeries(html):
    html = html.find('table')

    res = []
    tracked_urls = []
    
    for entry in html(['td']):
        rres = {}
        rres['runtime'] = entry.find('span', attrs={'class':'runtime'}).text
        rres['abstract'] = entry.find('span', attrs={'class':'fullAbstract'}).text
        a = entry.find('span', attrs={'class':'subject'}).find('a')
        rres['url'] = a.get('href')
        rres['url'] = 'https://www' + rres['url'].split('www',1)[1]
        
        if rres['url'] in tracked_urls:
            continue
        tracked_urls.append(rres['url'])
        rres['name'] = a.text
        res.append(rres)
    return res


    

if __name__ == '__main__':

    main()