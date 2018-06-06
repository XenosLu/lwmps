﻿#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""xlmp"""
import math
import os
import re
import shutil
import sqlite3
import sys
import logging

from threading import Thread, Event
from urllib.parse import quote, unquote
from time import sleep, time
from concurrent.futures import ThreadPoolExecutor

import tornado.web
import tornado.websocket

from lib.dlnap import URN_AVTransport_Fmt, discover  # https://github.com/ttopholm/dlnap
os.chdir(os.path.dirname(os.path.abspath(__file__)))  # set file path as current
# sys.path = ['lib'] + sys.path  # added libpath
# from lib.dlnap import URN_AVTransport_Fmt, discover  # https://github.com/ttopholm/dlnap

VIDEO_PATH = 'media'  # media file path
HISTORY_DB_FILE = '%s/.history.db' % VIDEO_PATH  # history db file

# initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s [line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


class DMRTracker(Thread):
    """DLNA Digital Media Renderer tracker thread"""
    def __init__(self, *args, **kwargs):
        super(DMRTracker, self).__init__(*args, **kwargs)
        self._flag = Event()
        self._flag.set()
        self._running = Event()
        self._running.set()
        self.state = {}  # DMR device state
        self.dmr = None  # DMR device object
        self.all_devices = []  # DMR device list
        self._failure = 0
        self._load = None
        logging.info('DMR Tracker initialized.')

    def discover_dmr(self):
        """Discover DMRs from local network"""
        logging.debug('Starting DMR search...')
        if self.dmr:
            logging.info('Current DMR: %s', self.dmr)
        self.all_devices = discover(name='', ip='', timeout=3,
                                    st=URN_AVTransport_Fmt, ssdp_version=1)
        if self.all_devices:
            self.dmr = self.all_devices[0]
            logging.info('Found DMR device: %s', self.dmr)

    def set_dmr(self, str_dmr):
        """set one of the DMRs as current DMR"""
        for i in self.all_devices:
            if str(i) == str_dmr:
                self.dmr = i
                return True
        return False

    def get_transport_state(self):
        """get transport state through DLNA"""
        info = self.dmr.info()
        if info:
            self.state['CurrentTransportState'] = info.get('CurrentTransportState')
            return info.get('CurrentTransportState')
        return None

    def get_position_info(self):
        """get DLNA play position info"""
        position_info = self.dmr.position_info()
        if not position_info:
            return None
        for key in ('RelTime', 'TrackDuration'):
            self.state[key] = position_info[key]
        if self.state.get('CurrentTransportState') == 'PLAYING':
            if position_info['TrackURI']:
                self.state['TrackURI'] = unquote(
                    re.sub('http://.*/video/', '', position_info['TrackURI']))
                save_history(self.state['TrackURI'],
                             time_to_second(self.state['RelTime']),
                             time_to_second(self.state['TrackDuration']))
            else:
                logging.info('no Track uri')
        return position_info.get('TrackDuration')

    def run(self):
        while self._running.isSet():
            self._flag.wait()
            if self.dmr:
                self.state['CurrentDMR'] = str(self.dmr)
                self.state['DMRs'] = [str(i) for i in self.all_devices]
                if self.get_transport_state() and not sleep(0.1) and self.get_position_info():
                    if self._failure > 0:
                        logging.info('reset failure count from %d to 0', self._failure)
                        self._failure = 0
                else:
                    self._failure += 1
                    logging.warning('Losing DMR count: %d', self._failure)
                    if self._failure >= 3:
                        logging.info('No DMR currently.')
                        self.state = {}
                        self.dmr = None
                sleep(0.8)
            else:
                self.discover_dmr()
                sleep(2.5)

    def pause(self):
        """pause tracker thread"""
        self._flag.clear()

    def resume(self):
        """resume paused tracker thread"""
        self._flag.set()

    def stop(self):
        """stop tracker thread"""
        self._flag.set()
        self._running.clear()

    def loadonce(self, url):
        """load video through DLNA from url for once"""
        try:
            while self.get_transport_state() not in ('STOPPED', 'NO_MEDIA_PRESENT'):
                self.dmr.stop()
                logging.info('Waiting for DMR stopped...')
                sleep(0.85)
            if self.dmr.set_current_media(url):
                logging.info('Loaded %s', url)
            else:
                logging.warning('Load url failed: %s', url)
                return False
            time0 = time()
            while self.get_transport_state() not in ('PLAYING', 'TRANSITIONING'):
                self.dmr.play()
                logging.info('Waiting for DMR playing...')
                sleep(0.3)
                if (time() - time0) > 5:
                    logging.info('waiting for DMR playing timeout')
                    return False
            sleep(0.5)
            time0 = time()
            logging.info('checking duration to make sure loaded...')
            while self.dmr.position_info().get('TrackDuration') == '00:00:00':
                sleep(0.5)
                logging.info('Waiting for duration to be recognized correctly, url=%s', url)
                if (time() - time0) > 15:
                    logging.info('Load duration timeout')
                    return False
            logging.info(self.state)
        except Exception as exp:
            # logging.warning('DLNA load exception: %s' % exp, exc_info=True)
            logging.warning('DLNA load exception: %s', exp, exc_info=True)
            return False
        return True


class DLNALoader(Thread):
    """Load url through DLNA"""
    def __init__(self, *args, **kwargs):
        super(DLNALoader, self).__init__(*args, **kwargs)
        self._running = Event()
        self._running.set()
        self._flag = Event()
        self._failure = 0
        self._url = ''
        logging.info('DLNA URL loader initialized.')

    def run(self):
        while self._running.isSet():
            self._flag.wait()
            TRACKER.pause()
            sleep(0.5)
            url = self._url
            if TRACKER.loadonce(url):
                logging.info('Loaded url: %s successed', url)
                src = unquote(re.sub('http://.*/video/', '', url))
                position = hist_load(src)
                if position:
                    TRACKER.dmr.seek(second_to_time(position))
                    logging.info('Loaded position: %s', second_to_time(position))
                logging.info('Load Successed.')
                TRACKER.state['CurrentTransportState'] = 'Load Successed.'
                if url == self._url:
                    self._flag.clear()
            else:
                self._failure += 1
                if self._failure >= 3:
                    self._flag.clear()
            TRACKER.resume()
            logging.info('tracker resume')

    def stop(self):
        """stop loader thread"""
        self._flag.set()
        self._running.clear()

    def load(self, url):
        """Load video through DLNA from URL """
        self._url = url
        self._failure = 0
        self._flag.set()


def run_sql(sql, *args):
    """run sql through sqlite3"""
    with sqlite3.connect(HISTORY_DB_FILE) as conn:
        try:
            cursor = conn.execute(sql, args)
            ret = cursor.fetchall()
            cursor.close()
            if cursor.rowcount > 0:
                conn.commit()
        except Exception as exp:
            logging.warning(str(exp))
            ret = ()
    return ret


def ls_dir(path):
    """list dir files in dict/json"""
    if path == '/':
        path = ''
    up, list_folder, list_mp4, list_video, list_other = [], [], [], [], []
    if path:
        up = [{'filename': '..', 'type': 'folder', 'path': '%s..' % path}]  # path should be path/
        if not path.endswith('/'):
            path = '%s/' % path
    dir_list = sorted(os.listdir('%s/%s' % (VIDEO_PATH, path)))
    for filename in dir_list:
        if filename.startswith('.'):
            continue
        if os.path.isdir('%s/%s%s' % (VIDEO_PATH, path, filename)):
            list_folder.append({'filename': filename, 'type': 'folder',
                                'path': '%s%s' % (path, filename)})
        elif re.match('.*\\.((?i)mp)4$', filename):
            list_mp4.append({'filename': filename, 'type': 'mp4',
                             'path': '%s%s' % (path, filename), 'size': get_size(path, filename)})
        elif re.match('.*\\.((?i)(mkv|avi|flv|rmvb|wmv))$', filename):
            list_video.append({'filename': filename, 'type': 'video',
                               'path': '%s%s' % (path, filename), 'size': get_size(path, filename)})
        else:
            list_other.append({'filename': filename, 'type': 'other',
                               'path': '%s%s' % (path, filename)})
    return {'filesystem': (up + list_folder + list_mp4 + list_video + list_other)}


def second_to_time(second):
    """ Turn time in seconds into "hh:mm:ss" format

    second: int value
    """
    m, s = divmod(second, 60)
    h, m = divmod(second/60, 60)
    return '%02d:%02d:%06.3f' % (h, m, s)


def time_to_second(time_str):
    """ Turn time in "hh:mm:ss" format into seconds

    time_str: string like "hh:mm:ss"
    """
    return sum([float(i)*60**n for n, i in enumerate(str(time_str).split(':')[::-1])])


def get_size(*filename):
    """get file size in human read format from file"""
    size = os.path.getsize('%s/%s' % (VIDEO_PATH, ''.join(filename)))
    if size < 0:
        return 'Out of Range'
    elif size < 1024:
        return '%dB' % size
    unit = ' KMGTPEZYB'
    l = min(int(math.floor(math.log(size, 1024))), 9)
    return '%.1f%sB' % (size/1024.0**l, unit[l])


def hist_load(name):
    """load history from database"""
    position = run_sql('select POSITION from history where FILENAME=?', name)
    # if len(position) == 0:
    if not position:
        return 0
    return position[0][0]


def save_history(src, position, duration):
    """save play history to database"""
    if float(position) < 10:
        return
    run_sql('''replace into history (FILENAME, POSITION, DURATION, LATEST_DATE)
               values(? , ?, ?, DateTime('now', 'localtime'));''', src, position, duration)


def check_dmr_exist(func):
    """Decorator: check DMR is available before do something relate to DLNA"""
    def no_dmr(self, *args, **kwargs):
        """check if DMR exist"""
        if not TRACKER.dmr:
            self.finish('Error: No DMR.')
            return None
        return func(self, *args, **kwargs)
    return no_dmr


def get_next_file(src):  # not strict enough
    """get next related video file"""
    fullname = '%s/%s' % (VIDEO_PATH, src)
    filepath = os.path.dirname(fullname)
    dirs = sorted([i for i in os.listdir(filepath)
                   if not i.startswith('.') and os.path.isfile('%s/%s' % (filepath, i))])
    if os.path.basename(fullname) in dirs:
        next_index = dirs.index(os.path.basename(fullname)) + 1
    else:
        next_index = 0
    if next_index < len(dirs):
        return '%s/%s' % (os.path.dirname(src), dirs[next_index])
    return None


class IndexHandler(tornado.web.RequestHandler):
    """index web page"""
    def get(self, *args, **kwargs):
        if TRACKER.dmr:
            dlna_style = 'btn-success'
        else:
            dlna_style = ''
        self.render('index.tpl', dlna_style=dlna_style)


class DlnaPlayerHandler(tornado.web.RequestHandler):
    """DLNA player page"""
    def get(self, *args, **kwargs):
        if TRACKER.dmr:
            dlna_style = 'btn-success'
        else:
            dlna_style = ''
        self.render('dlna.tpl', dlna_style=dlna_style)


class WebPlayerHandler(tornado.web.RequestHandler):
    """Video play page"""
    def get(self, *args, **kwargs):
        src = kwargs.get('src')
    # def get(self, src):
        if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
            self.redirect('/')
        self.render('player.tpl', dlna_style='', src=src, position=hist_load(src))


class HistoryHandler(tornado.web.RequestHandler):
    """Return play history list"""
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        if opt == 'ls':
            pass
        elif opt == 'clear':
            run_sql('delete from history')
        elif opt == 'rm':
            run_sql('delete from history where FILENAME=?', unquote(kwargs.get('src')))
        else:
            raise tornado.web.HTTPError(404, reason='illegal operation')
        self.finish({'history': [{'filename': s[0], 'position': s[1], 'duration': s[2],
                                  'latest_date': s[3], 'path': os.path.dirname(s[0])}
                                 for s in run_sql('select * from history order by LATEST_DATE desc'
                                                 )]})


class FileSystemListHandler(tornado.web.RequestHandler):
    """Get static folder list in json"""
    def get(self, *args, **kwargs):
        try:
            self.finish(ls_dir(kwargs.get('path')))
        except Exception as exp:
            raise tornado.web.HTTPError(404, reason=str(exp))


class FileSystemMoveHandler(tornado.web.RequestHandler):
    """Move file to '.old' folder"""
    def get(self, *args, **kwargs):
        src = kwargs.get('src')
        filename = '%s/%s' % (VIDEO_PATH, src)
        dir_old = '%s/%s/.old' % (VIDEO_PATH, os.path.dirname(src))
        if not os.path.exists(dir_old):
            os.mkdir(dir_old)
        try:
            shutil.move(filename, dir_old)  # gonna do something when file is occupied
        except Exception as exp:
            logging.warning('move file failed: %s', exp)
            raise tornado.web.HTTPError(404, reason=str(exp))
        self.finish(ls_dir('%s/' % os.path.dirname(src)))


class SaveHandler(tornado.web.RequestHandler):
    """Save play history"""
    executor = ThreadPoolExecutor(9)
    @tornado.gen.coroutine
    @tornado.concurrent.run_on_executor
    def post(self, *args, **kwargs):
        position = self.get_argument('position', 0)
        duration = self.get_argument('duration', 0)
        save_history(kwargs.get('src'), position, duration)


class DlnaLoadHandler(tornado.web.RequestHandler):
    """DLNA load file web interface"""
    @check_dmr_exist
    def get(self, *args, **kwargs):
        src = kwargs.get('src')
    # def get(self, src):
        if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
            logging.warning('File not found: %s', src)
            self.finish('Error: File not found.')
            return
        logging.info('start loading...tracker state:%s', TRACKER.state.get('CurrentTransportState'))
        url = 'http://%s/video/%s' % (self.request.headers['Host'], quote(src))
        LOADER.load(url)
        self.finish('loading %s' % src)


class DlnaNextHandler(tornado.web.RequestHandler):
    """DLNA jump to next video file web interface"""
    @check_dmr_exist
    def get(self, *args, **kwargs):
        if not TRACKER.state.get('TrackURI'):
            self.finish('No current url')
            return
        next_file = get_next_file(TRACKER.state['TrackURI'])
        logging.info('next file recognized: %s', next_file)
        if next_file:
            url = 'http://%s/video/%s' % (self.request.headers['Host'], quote(next_file))
            LOADER.load(url)
        else:
            self.finish("Can't get next file")


class DlnaHandler(tornado.web.RequestHandler):
    """DLNA operation web interface"""
    @check_dmr_exist
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        # progress = kwargs.get('progress')
    # def get(self, opt, progress):
        # print(progress)
        self.write('opt: %s' % opt)
        if opt in ('play', 'pause', 'stop'):
            method = getattr(TRACKER.dmr, opt)
            ret = method()
        elif opt == 'seek':
            # ret = TRACKER.dmr.seek(progress)
            ret = TRACKER.dmr.seek(kwargs.get('progress'))
        else:
            return
        if ret:
            self.finish('Done.')
        else:
            self.finish('Error: Failed!')


class DlnaInfoHandler(tornado.web.RequestHandler):
    """old version of DLNA info retrieve web interface replaced by web socket"""
    def get(self, *args, **kwargs):
        self.finish(TRACKER.state)


class DlnaVolumeControlHandler(tornado.web.RequestHandler):
    """Tune volume through DLNA web interface"""
    @check_dmr_exist
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        vol = int(TRACKER.dmr.get_volume())
        if opt == 'up':
            vol += 1
        elif opt == 'down':
            vol -= 1
        if not 0 <= vol <= 100:
            self.finish('volume range exceeded')
        elif TRACKER.dmr.volume(vol):
            self.finish(str(vol))
        else:
            self.finish('failed')


class SystemCommandHandler(tornado.web.RequestHandler):
    """some system maintainence command web interface"""
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        if opt == 'update':
            if sys.platform == 'linux':
                if os.system('git pull') == 0:
                    self.finish('git pull done, waiting for restart')
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
                    # os._exit(1)
                else:
                    self.finish('execute git pull failed')
            else:
                self.finish('not supported')
        elif opt == 'backup':  # backup history
            self.finish(shutil.copyfile(HISTORY_DB_FILE, '%s.bak' % HISTORY_DB_FILE))
        elif opt == 'restore':  # restore history
            self.finish(shutil.copyfile('%s.bak' % HISTORY_DB_FILE, HISTORY_DB_FILE))
        else:
            self.finish('no such operation')
# @post('/suspend')
# def suspend():
    # """Suepend server"""
    # if sys.platform == 'win32':
        # import ctypes
        # dll = ctypes.WinDLL('powrprof.dll')
        # if dll.SetSuspendState(0, 1, 0):
            # return 'Suspending...'
        # else:
            # return 'Suspend Failure!'
    # else:
        # return 'OS not supported!'


# @post('/shutdown')
# def shutdown():
    # """Shutdown server"""
    # if sys.platform == 'win32':
        # os.system("shutdown.exe -f -s -t 0")
    # else:
        # os.system("sudo /sbin/shutdown -h now")
    # return 'shutting down...'


class SetDmrHandler(tornado.web.RequestHandler):
    """set dmr web interface"""
    def get(self, *args, **kwargs):
    # def get(self, dmr):
        if TRACKER.set_dmr(kwargs.get('dmr')):
            self.finish('Done.')
        else:
            self.finish('Error: Failed!')


class SearchDmrHandler(tornado.web.RequestHandler):
    """Mannually search DMR web interface"""
    def get(self, *args, **kwargs):
        TRACKER.discover_dmr()


class TestHandler(tornado.web.RequestHandler):
    """test only"""
    # @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        # self.set_header('Access-Control-Allow-Origin', '*')
        # self.set_header('Content-Type', 'text/event-stream')
        # self.set_header('Cache-Control', 'no-cache')
        logging.info(self.request.headers)
        logging.info(self.request.remote_ip)
        # self.write('data: xxx %s\n\n' % time())
        # yield self.flush()
        self.write('test')


class DlnaWebSocketHandler(tornado.websocket.WebSocketHandler):
    """DLNA info retriever use web socket"""
    executor = ThreadPoolExecutor(9)
    _running = True
    @tornado.gen.coroutine
    @tornado.concurrent.run_on_executor
    def open(self, *args, **kwargs):
        logging.info('ws connected: %s', self.request.remote_ip)
        last_message = ''
        while self._running:
            # logging.info(self.executor._work_queue.unfinished_tasks)
            if last_message != TRACKER.state:
                self.write_message(TRACKER.state)
                # logging.info(TRACKER.state.get('RelTime'))
                last_message = TRACKER.state.copy()
            sleep(0.2)

    def on_message(self, message):
        pass
        # logging.info('receive: %s' % message)

    def on_close(self):
        logging.info('ws close: %s', self.request.remote_ip)
        self._running = False
# context arrangement (to-do)
# /sys/
# /fs/
# /dlna/
# /wp/ # web player

Handlers = [
    (r'/', IndexHandler),
    (r'/dlna', DlnaPlayerHandler),
    (r'/fs/(?P<path>.*)', FileSystemListHandler),
    (r'/move/(?P<src>.*)', FileSystemMoveHandler),
    (r'/hist/(?P<opt>\w*)/?(?P<src>.*)', HistoryHandler),
    (r'/sys/(?P<opt>\w*)', SystemCommandHandler),
    (r'/test', TestHandler),  # test
    (r'/dlnalink', DlnaWebSocketHandler),
    (r'/dlnainfo', DlnaInfoHandler),
    (r'/setdmr/(?P<dmr>.*)', SetDmrHandler),
    (r'/searchdmr', SearchDmrHandler),
    (r'/dlnavol/(?P<opt>\w*)', DlnaVolumeControlHandler),
    (r'/dlna/next', DlnaNextHandler),
    (r'/dlna/load/(?P<src>.*)', DlnaLoadHandler),
    (r'/dlna/(?P<opt>\w*)/?(?P<progress>.*)', DlnaHandler),
    (r'/save/(?P<src>.*)', SaveHandler),
    (r'/play/(?P<src>.*)', WebPlayerHandler),
    (r'/video/(.*)', tornado.web.StaticFileHandler, {'path': VIDEO_PATH}),
]

SETTINGS = {
    'static_path': 'static',
    'template_path': 'views',
    'gzip': True,
    # "debug": True,
}
application = tornado.web.Application(Handlers, **SETTINGS)
# initialize DataBase
run_sql('''create table if not exists history
                (FILENAME text PRIMARY KEY not null,
                POSITION float not null,
                DURATION float, LATEST_DATE datetime not null);''')
# initialize dlna threader
TRACKER = DMRTracker()
TRACKER.start()
LOADER = DLNALoader()
LOADER.start()


if __name__ == "__main__":
    if sys.platform == 'win32':
        os.system('start http://127.0.0.1:8888/')
    application.listen(8888, xheaders=True)
    tornado.ioloop.IOLoop.instance().start()
