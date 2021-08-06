import requests
import multiprocessing as mp
import subprocess
import datetime

from configs import *
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
    if DOWNLOAD_FOLDER is None:
        logger.error('Need to set download folder in config.py!')
        raise ValueError('Need to set download folder in config.py!')
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.mkdir(DOWNLOAD_FOLDER)
    logger.info('Downloading all files to %s' % DOWNLOAD_FOLDER)
    logger.info("You can change the download location in configs.py")
    series = seriesPickerMain()
    date_selected = datePicker()
    scheduleDict = getSchedule(series, date_selected)
    pickedNames = downloadPckerMain(scheduleDict)
    res = [] #pruned dict
    for dct in scheduleDict:
        if dct['name'] in pickedNames:
            res.append(dct)
    downloader(res)
    logger.info('Done')

    return

def downloader(res):

    for dct in res:
        _download_child(dct)

        
def _download_child(dct):
    logger.info('downloading %s via %s', dct['name'], dct['url'])
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(dir_path, 'youtube-dl.exe')
    download_folder = os.path.join(DOWNLOAD_FOLDER, '%(title)s-%(id)s.%(ext)s')
    cmd = [filepath, dct['url'], '--output', download_folder]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        if proc.poll() or proc.returncode is not None:
            break
        line = proc.stdout.readline()
        if not line:
            time.sleep(3)
        else:
            print(line.strip(), end='\r')
    if not proc.returncode:
        logger.info('done')
    else:
        stdout, stderr = proc.communicate()
        logger.error('Encountered error as follows')
        logger.error('STDOUT: \n%s', stdout)
        logger.error('STDERR: \n%s', stderr)




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
