import requests
import multiprocessing as mp
import subprocess
import datetime
import configparser
from lib import *
from gui import GUI
import time
import tempfile
from bs4 import BeautifulSoup, Doctype
from pprint import pprint, pformat
import re
import shutil

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


    with GUI() as gui:
        series = gui.series
        date_selected = gui.date_selected
        scheduleDict = getSchedule(series, date_selected)

        pickedNames = gui.downloadPicker(scheduleDict)
        save_fmt = gui.fmt
        keep_mp4 = gui.keep_mp4

    if not pickedNames:
        logger.info('No shows picked, exiting...')
        return

    res = [] #pruned dict
    for dct in scheduleDict:
        if dct['name'] in pickedNames:
            res.append(dct)
    errors = downloader(res, download_folder, parallel=parallel)

    if errors:
        logger.error('Encountered partial errors while running. Please consult the logs.')

    if save_fmt == 'mp4':
        if errors:
            raise RuntimeError('Encountered partial errors while running. Please consult the logs.')
        return

    dvdStyler(pickedNames, config, save_fmt, keep_mp4)

def dvdStyler(names, config, fmt, keep_mp4):
    assert fmt in ['dvd','iso']
    logger.info('Converting %s files to %s', len(names), fmt)
    download_folder = config['DEFAULT']['DownloadFolder']
    dvd_styler_exe = config['DEFAULT']['DVDStyler']

    paths = [os.path.join(download_folder, f) for f in os.listdir(download_folder) if f.rsplit('.',1)[0] in names]

    mainTempFolder = tempfile.mkdtemp(prefix='DVDStyler_temp_folder')

    errors = []
    for path in paths:
        name = path.rsplit(os.sep,1)[1].rsplit('.',1)[0]
        tempFolder = tempfile.mkdtemp(dir=mainTempFolder, prefix=name[:12])
        cmd = [dvd_styler_exe, path, '--tempDir', tempFolder, '--start']
        if fmt == 'dvd':
            cmd.extend(['--outputDir', os.path.join(download_folder, name+'_dvd')])
        else:
            cmd.extend(['--isoFile', os.path.join(download_folder, name+'.iso')])

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            if proc.poll() or proc.returncode is not None:
                break
        if not proc.returncode:
            logger.info('Finished %s', name)
            if not keep_mp4:
                os.remove(path)
            shutil.rmtree(tempFolder, ignore_errors=True)
        else:
            stdout, stderr = proc.communicate()
            logger.error('Encountered error as follows')
            logger.error('STDOUT: \n%s', stdout)
            logger.error('STDERR: \n%s', stderr)
            errors.append(name)
    if not errors:
        shutil.rmtree(mainTempFolder, ignore_errors=True)


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
    download_folder = os.path.join(download_folder, '{name}.%(ext)s'.format(name=dct['name']))
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
    html = BeautifulSoup(r.text, "html.parser")

    html = stripHTML(html)
    
    res = parseSeries(html)# if 'series/print' in url else parseSchedule(html)

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
        subject = None
        try:
            # Remove empty entries
            if not ''.join(entry.text).strip():
                continue

            # subject = series, title = schedule
            subject = entry.find('span', attrs={'class': 'subject'}) or entry.find('span', attrs={'class': 'title'})
            a = subject.find('a')
            if a is None:
                # No links
                continue
            # runtime = series, length = schedule
            rres['runtime'] = (entry.find('span', attrs={'class':'runtime'}) or entry.find('span', attrs={'class':'length'})).text
            rres['abstract'] = entry.find('span', attrs={'class':'fullAbstract'}).text

            rres['url'] = a.get('href')
        except AttributeError:
            logger.exception('Encountered error while parsing html%s', (' for %s'%subject.text if subject else ''))
            continue
        rres['url'] = 'https://www' + rres['url'].split('www',1)[1]
        if not rres['url'].isascii():
            logger.error('!'*80)
            logger.error('Found a non ascii url, skipping')
            logger.error(rres['url'])
            logger.error('!'*80)
        if rres['url'] in tracked_urls:
            continue
        tracked_urls.append(rres['url'])

        rres['name'] = re.sub(r"[^\w\d\-_ ]", '', a.text)
        res.append(rres)
    return res


    

if __name__ == '__main__':

    main()
