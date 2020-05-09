#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""xlmp main program"""
import math
import os
import re
import shutil
import sqlite3
import sys
import logging
import asyncio
import json
from threading import Thread, Event
from urllib.parse import quote, unquote
from time import sleep, time
from concurrent.futures import ThreadPoolExecutor

import tornado.web
import tornado.websocket

from lib.dlnap import URN_AVTransport_Fmt, discover  # https://github.com/ttopholm/dlnap

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # set file path as current

# initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s [line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

VIDEO_PATH = 'media'  # media file path
HISTORY_DB_FILE = '%s/.history.db' % VIDEO_PATH  # history db file


class DMRTracker(Thread):
    """DLNA Digital Media Renderer tracker thread with coroutine"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop = asyncio.new_event_loop()
        self._load_inprogess = Event()
        self.loop_playback = Event()
        self.state = {}  # DMR device state
        # self.state = {'CurrentDMR': 'no DMR'}  # DMR device state
        self.dmr = None  # DMR device object
        self.all_devices = []  # DMR device list
        self.url_prefix = None
        self._url = ''
        logging.info('DMR Tracker thread initialized.')

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

    def _get_transport_state(self):
        """get transport state through DLNA"""
        info = self.dmr.info()
        if info:
            self.state['CurrentTransportState'] = info.get('CurrentTransportState')
            return info.get('CurrentTransportState')
        logging.info('get info failed')
        return None

    def _get_position_info(self):
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

    def async_run(self, func, *args, **kwargs):
        """run block func in coroutine loop in thread"""
        async def job():
            return func(*args, **kwargs)
        future = asyncio.run_coroutine_threadsafe(job(), self._loop)
        # future.add_done_callback(callback)
        return future.result()  # block

    @asyncio.coroutine
    def main_loop(self):
        """main async loop"""
        failure = 0
        while True:
            if self.dmr:
                self.state['CurrentDMR'] = str(self.dmr)
                self.state['DMRs'] = [str(i) for i in self.all_devices]
                transport_state = self._get_transport_state()
                if transport_state:
                    sleep(0.1)
                    if transport_state == 'STOPPED' and self.loop_playback.isSet():
                        yield from asyncio.sleep(0.5)
                        if not self.loadnext():
                            self.loop_playback.clear()
                    yield
                    if self._get_position_info():
                        sleep(0.1)
                        if failure > 0:
                            logging.info('reset failure count from %d to 0', failure)
                            failure = 0
                else:
                    failure += 1
                    logging.warning('Losing DMR count: %d', failure)
                    if failure >= 3:
                        logging.info('No DMR currently.')
                        # self.state = {'CurrentDMR': 'no DMR'}
                        self.state = {}
                        self.dmr = None
                yield from asyncio.sleep(0.7)
                sleep(0.1)
            else:
                logging.debug('searching DMR')
                self.discover_dmr()
                if LinkWebSocketHandler.users:
                    sleep_time = 2
                else:
                    sleep_time = 5
                yield from asyncio.sleep(sleep_time)
                # yield from asyncio.sleep(2.5)

    def run(self):
        asyncio.set_event_loop(self._loop)
        task = self._loop.create_task(self.main_loop())
        self._loop.run_until_complete(task)

    def load(self, src):
        """Load video through DLNA from URL """
        logging.info('start loading')
        if not self.url_prefix:
            return False
        url = '%s%s' % (self.url_prefix, quote(src))
        self._url = url
        self._load_inprogess.set()
        asyncio.run_coroutine_threadsafe(self._load_coroutine(url), self._loop)
        logging.info('coroutine loaded')
        return True

    @asyncio.coroutine
    def _load_coroutine(self, url):
        """load videdo in coroutine"""
        failure = 0
        while failure < 3:
            sleep(0.4)
            if url != self._url or not self._load_inprogess.isSet():
                return
            if self.loadonce(url):
                logging.info('Loaded url: %s successed', unquote(url))
                src = unquote(re.sub('http://.*/video/', '', url))
                position = hist_load(src)
                if position:
                    self.dmr.seek(second_to_time(position))
                    logging.info('Loaded position: %s', second_to_time(position))
                logging.info('Load Successed.')
                self.state['CurrentTransportState'] = 'Load Successed.'
                if url == self._url:
                    self._load_inprogess.clear()
                if time_to_second(self.state.get('TrackDuration')) <= 600:
                    self.loop_playback.set()
                return
            failure += 1
            logging.info('load failure count: %s', failure)

    def loadnext(self, src=None):
        """load next video"""
        if not src:
            src = self.state.get('TrackURI')
        if not src:
            return False
        next_file = get_next_file(src)
        logging.info('next file recognized: %s', next_file)
        if next_file:
            return self.load(next_file)
        return False

    def loadonce(self, url):
        """load video through DLNA from url for once"""
        if not self.dmr:
            return False
        while self._get_transport_state() not in ('STOPPED', 'NO_MEDIA_PRESENT'):
            logging.info('send stop')
            self.dmr.stop()
            logging.info('Waiting for DMR stopped...')
            sleep(1)
        if self.dmr.set_current_media(url):
            logging.info('Loaded %s', unquote(url))
        else:
            logging.warning('Load url failed: %s', unquote(url))
            return False
        time0 = time()
        try:
            while self._get_transport_state() not in ('PLAYING', 'TRANSITIONING'):
                self.dmr.play()
                logging.info('send play')
                logging.info('Waiting for DMR playing...')
                sleep(0.3)
                if (time() - time0) > 10:
                    logging.info('waiting for DMR playing timeout')
                    return False
            sleep(0.5)
            time0 = time()
            logging.info('checking duration to make sure loaded...')
            while self._get_position_info() == '00:00:00':
                sleep(0.5)
                logging.info('Waiting for duration to be recognized correctly, url=%s',
                             unquote(url))
                if (time() - time0) > 15:
                    logging.info('Load duration timeout')
                    return False
            logging.info(self.state)
        except Exception as exc:
            logging.warning('DLNA load exception: %s', exc, exc_info=True)
            return False
        return True


def run_sql(sql, *args):
    """run sql through sqlite3"""
    with sqlite3.connect(HISTORY_DB_FILE) as conn:
        try:
            cursor = conn.execute(sql, args)
            ret = cursor.fetchall()
            cursor.close()
            if cursor.rowcount > 0:
                conn.commit()
        except Exception as exc:
            logging.warning(str(exc))
            ret = ()
    return ret


def second_to_time(second):
    """ Turn time in seconds into "hh:mm:ss" format

    second: int value
    """
    minute, sec = divmod(second, 60)
    hour, minute = divmod(second/60, 60)
    return '%02d:%02d:%06.3f' % (hour, minute, sec)


def time_to_second(time_str):
    """ Turn time in "hh:mm:ss" format into seconds

    time_str: string like "hh:mm:ss"
    """
    return sum([float(i)*60**n for n, i in enumerate(str(time_str).split(':')[::-1])])


def get_size(path):
    """get file size in human read format from file"""
    size = os.path.getsize(path)
    if size < 0:
        return 'Out of Range'
    if size < 1024:
        return '%dB' % size
    unit = ' KMGTPEZYB'
    power = min(int(math.floor(math.log(size, 1024))), 9)
    return '%.1f%sB' % (size/1024.0**power, unit[power])


def hist_load(name):
    """load history from database"""
    position = run_sql('select POSITION from history where FILENAME=?', name)
    if position:
        return position[0][0]
    return 0


def check_dmr_exist(func):
    """Decorator: check DMR is available before do something relate to DLNA"""
    def wrapper(*args, **kwargs):
        """check if DMR exist"""
        if TRACKER.dmr:
            return func(*args, **kwargs)
        return 'No DMR.'
    wrapper.__name__ = func.__name__
    return wrapper


class IndexHandler(tornado.web.RequestHandler):
    """index web page"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        self.render('index.html')


class DlnaPlayToggleHandler(tornado.web.RequestHandler):
    """DLNA operation web interface"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        if not TRACKER.dmr:
            self.finish({'error': 'No DMR.'})
            return
        if TRACKER.state.get('CurrentTransportState') == 'PLAYING':
            ret = TRACKER.dmr.pause()
        else:
            ret = TRACKER.dmr.play()
        if ret:
            self.finish({'result': 'success'})
        if not ret:
            self.finish({'error': 'Failed!'})


class LinkWebSocketHandler(tornado.websocket.WebSocketHandler):
    """DLNA info retriever use web socket"""
    users = set()
    last_message = None

    def data_received(self, chunk):
        pass

    def open(self, *args, **kwargs):
        logging.info('ws connected: %s', self.request.remote_ip)
        self.users.add(self)
        self.on_pong()

    def on_message(self, message):
        logging.info('received ws message: %s', message)
        result = JsonRpc.run(message)
        logging.info('result: %s', result)
        self.write_message(result)

    def on_pong(self, data=None):
        if self.last_message != TRACKER.state:
            logging.debug(TRACKER.state)
            self.write_message(TRACKER.state)
            self.last_message = TRACKER.state.copy()

    def on_close(self):
        logging.info('ws close: %s', self.request.remote_ip)
        self.users.remove(self)


class ApiHandler(tornado.web.RequestHandler):
    # executor = ThreadPoolExecutor(99)
    """api test"""
    def data_received(self, chunk):
        pass

    # @tornado.concurrent.run_on_executor
    def post(self, *args, **kwargs):
        json_data = self.request.body.decode()
        result = JsonRpc.run(json_data)
        logging.info('result: %s', result)
        self.finish(result)


class JsonRpc():
    """Json RPC class follow JSON-RPC 2.0 Specification
    Usage: JsonRpc.run(json_data)
    @JsonRpc.method
    def foo():
        pass
    """
    methods = {}
    @classmethod
    def run(cls, json_data):
        """test method"""
        val = {'jsonrpc': '2.0', 'id': None}
        try:
            obj = json.loads(json_data)
        except json.decoder.JSONDecodeError:
            logging.debug(json_data)
            val['error'] = {'code': -32700, 'message': 'Parse error'}
            return val
        if isinstance(obj, dict):
            return cls._run(obj)
        if isinstance(obj, list):
            return [cls._run(item) for item in obj]
        val['error'] = {'code': -32600, 'message': 'Invalid Request'}
        return val

    @classmethod
    def _run(cls, obj):
        """run RPC method"""
        val = {'jsonrpc': '2.0'}
        logging.info(obj)
        val['id'] = obj.get('id')
        method = obj.get('method')
        params = obj.get('params')
        args = params if isinstance(params, list) else []
        kwargs = params if isinstance(params, dict) else {}
        if not method in cls.methods:
            val['error'] = {'code': -32601, 'message': 'Method not found'}
            return val
        try:
            result = cls.methods[method](*args, **kwargs)
            if val['id'] is None:
                return ''
            if result is True:
                result = 'Success'
            elif result is False:
                result = 'Failed'
            val['result'] = result
        except TypeError as exc:
            logging.warning(exc, exc_info=True)
            val['error'] = {'code': -32602, 'message': 'Invalid params'}
        except Exception as exc:
            logging.warning(exc, exc_info=True)
            val['error'] = {'code': -1, 'message': str(exc)}
        return val

    @classmethod
    def method(cls, func):
        """Decorator: register a function as json rpc method"""
        if func.__name__.startswith('rpc.'):
            logging.warning('Method name "%s" begin with rpc. is reserved for system extension',
                            func.__name__)
        elif func.__name__ in cls.methods:
            logging.warning('Method name "%s" has been occupied in JsonRpc', func.__name__)
        else:
            cls.methods[func.__name__] = func
            logging.debug('JsonRpc method registered: %s', func.__name__)
        return func


@JsonRpc.method
@check_dmr_exist
def dlna_vol(opt):
    """dlna volume adjuster"""
    vol = int(TRACKER.dmr.get_volume())
    if opt == 'up':
        vol += 1
    elif opt == 'down':
        vol -= 1
    if not 0 <= vol <= 100:
        return 'Volume range exceeded'
    if TRACKER.dmr.volume(vol):
        return str(vol)
    return False


@JsonRpc.method
@check_dmr_exist
def dlna_next(src=None, host=None):
    """dlna load next media"""
    if host:
        TRACKER.url_prefix = 'http://%s/video/' % host
    return TRACKER.loadnext(src=src)


@JsonRpc.method
@check_dmr_exist
def dlna(opt):
    """dlna commands"""
    if opt in ('play', 'pause', 'stop'):
        if opt == 'stop':
            TRACKER.loop_playback.clear()
        method = getattr(TRACKER.dmr, opt)
        return method()
    return 'option not exist'


@JsonRpc.method
@check_dmr_exist
def dlna_seek(position):
    """dlna seek to new position"""
    return TRACKER.dmr.seek(position)


@JsonRpc.method
def dlna_search():
    """search dlna DMR"""
    return TRACKER.discover_dmr()


@JsonRpc.method
def dlna_set_dmr(dmr):
    """dlna set a DMR as current"""
    return TRACKER.set_dmr(dmr)


@JsonRpc.method
def save_history(src, position, duration):
    """save play history to database"""
    if float(position) < 10:
        return
    run_sql('''replace into history (FILENAME, POSITION, DURATION, LATEST_DATE)
               values(? , ?, ?, DateTime('now', 'localtime'));''', src, position, duration)


@JsonRpc.method
def list_history():
    """get play history"""
    return [
        {'filename': os.path.basename(s[0]), 'fullpath': s[0], 'position': s[1], 'duration': s[2],
         'latest_date': s[3], 'path': os.path.dirname(s[0]),
         'exist': os.path.exists('%s/%s' % (VIDEO_PATH, s[0]))}
        for s in run_sql('select * from history order by LATEST_DATE desc')]


# @JsonRpc.method
def clear_history():
    """clear all history, no longer needed"""
    run_sql('delete from history')
    return list_history()


@JsonRpc.method
def remove_history(src):
    """remove an item from history"""
    logging.info(src)
    run_sql('delete from history where FILENAME=?', unquote(src))
    return list_history()


@JsonRpc.method
@check_dmr_exist
def dlna_load(src, host):
    """load a video through DMR"""
    if host.startswith('127.0.0.1'):
        return 'should not use 127.0.0.1 as host to load throuh DLNA'
    if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
        logging.warning('File not found: %s', src)
        return 'Error: File not found.'
    logging.info('start loading...tracker state:%s', TRACKER.state.get('CurrentTransportState'))
    TRACKER.url_prefix = 'http://%s/video/' % host
    TRACKER.load(src)
    return 'loading %s' % src


@JsonRpc.method
def file_move(src):
    """move file to .old folder and hide it"""
    filename = '%s/%s' % (VIDEO_PATH, src)
    dir_old = '%s/%s/.old' % (VIDEO_PATH, os.path.dirname(src))
    if not os.path.exists(dir_old):
        os.mkdir(dir_old)
    try:
        shutil.move(filename, dir_old)  # gonna do something when file is occupied
    except Exception as exc:
        logging.warning('move file failed: %s', exc)
        return False
    return file_list('%s/' % os.path.dirname(src))


@JsonRpc.method
def self_update():
    """develop method: self update"""
    def restart():
        sleep(1)
        python = sys.executable
        os.execl(python, python, *sys.argv)
    executor = ThreadPoolExecutor(1)
    result = os.system('git pull')
    executor.submit(restart)
    if result == 0:
        return 'git pull done, waiting for restart'
    return 'git pull failed, restart anyway'


@JsonRpc.method
def db_backup():
    """backup database file"""
    return shutil.copyfile(HISTORY_DB_FILE, '%s.bak' % HISTORY_DB_FILE)


@JsonRpc.method
def db_restore():
    """restore from database backup file"""
    return shutil.copyfile('%s.bak' % HISTORY_DB_FILE, HISTORY_DB_FILE)


@JsonRpc.method
def test():
    """test function"""
    return 'test message'


def get_next_file(src):  # not strict enough
    """get next related video file"""
    logging.info(src)
    fullname = '%s/%s' % (VIDEO_PATH, src)
    filepath = os.path.dirname(fullname)
    files = sorted([i for i in os.listdir(filepath)
                    if not i.startswith('.') and os.path.isfile('%s/%s' % (filepath, i))])
    if os.path.basename(src) in files:
        next_index = files.index(os.path.basename(src)) + 1
    else:
        next_index = 0
    if next_index < len(files):
        return '%s/%s' % (os.path.dirname(src), files[next_index])
    return None


@JsonRpc.method
def file_list(path=''):
    """list dir files in dict/json"""
    if path == '/':
        path = ''
    parent, list_folder, list_mp4, list_video, list_other = [], [], [], [], []
    if path:
        parent = [{'filename': '..', 'type': 'folder', 'path': os.path.dirname(path)}]
        logging.info(path)
        path = re.sub('([^/])$', '\\1/', path)  # make sure path end with '/'
    dir_list = sorted(os.listdir('%s/%s' % (VIDEO_PATH, path)))
    for filename in dir_list:
        if filename.startswith('.'):
            continue
        rel_path = '%s%s' % (path, filename)
        fullpath = '%s/%s' % (VIDEO_PATH, rel_path)
        if os.path.isdir(fullpath):
            list_folder.append({'filename': filename, 'type': 'folder', 'path': rel_path})
        elif re.match('.*\\.((?i)mp)4$', filename):
            list_mp4.append({'filename': filename, 'type': 'mp4',
                             'path': rel_path, 'size': get_size(fullpath)})
        elif re.match('.*\\.((?i)(mkv|avi|flv|rmvb|wmv))$', filename):
            list_video.append({'filename': filename, 'type': 'video',
                               'path': rel_path, 'size': get_size(fullpath)})
        else:
            list_other.append({'filename': filename, 'type': 'other', 'path': rel_path})
    return parent + list_folder + list_mp4 + list_video + list_other


HANDLERS = [
    (r'/', IndexHandler),
    (r'/api', ApiHandler),
    (r'/link', LinkWebSocketHandler),
    (r'/playtoggle', DlnaPlayToggleHandler),
    (r'/video/(.*)', tornado.web.StaticFileHandler, {'path': VIDEO_PATH}),
]

SETTINGS = {
    'static_path': 'static',
    'template_path': '',
    'gzip': True,
    # 'debug': True,
    'websocket_ping_interval': 0.2,
}

APP = tornado.web.Application(HANDLERS, **SETTINGS)

# initialize dlna threader
TRACKER = DMRTracker()

if __name__ == '__main__':
    # initialize DataBase
    run_sql('''create table if not exists history
                    (FILENAME text PRIMARY KEY not null,
                    POSITION float not null,
                    DURATION float, LATEST_DATE datetime not null);''')
    TRACKER.start()
    # if sys.platform == 'win32':
        # os.system('start http://127.0.0.1:8888/')
    print('Listen on http://127.0.0.1:8888')
    APP.listen(8888, xheaders=True)
    tornado.ioloop.IOLoop.instance().start()
