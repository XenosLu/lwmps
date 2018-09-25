﻿#!/usr/bin/python3
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

VIDEO_PATH = 'media'  # media file path
HISTORY_DB_FILE = '%s/.history.db' % VIDEO_PATH  # history db file


class DMRTracker(Thread):
    """DLNA Digital Media Renderer tracker thread with coroutine"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._loop = asyncio.new_event_loop()
        self._load_inprogess = Event()
        self.loop_playback = Event()
        self.state = {'CurrentDMR': 'no DMR'}  # DMR device state
        self.dmr = None  # DMR device object
        self.all_devices = []  # DMR device list
        self.url_prefix = None
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
                # self.url_prefix = re.sub('(http://.*/video/).*', '\\1', position_info['TrackURI'])
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
                        self.state = {'CurrentDMR': 'no DMR'}
                        self.dmr = None
                yield from asyncio.sleep(0.7)
                sleep(0.1)
            else:
                logging.debug('searching DMR')
                self.discover_dmr()
                yield from asyncio.sleep(2.5)

    def run(self):
        asyncio.set_event_loop(self._loop)
        task = self._loop.create_task(self.main_loop())
        self._loop.run_until_complete(task)

    def load(self, url):
        """Load video through DLNA from URL """
        logging.info('start loading')
        self._url = url
        self._load_inprogess.set()
        asyncio.run_coroutine_threadsafe(self.load_coroutine(url), self._loop)
        logging.info('coroutine loaded')

    @asyncio.coroutine
    def load_coroutine(self, url):
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
            else:
                failure += 1
                logging.info('load failure count: %s', failure)

    def loadnext(self):
        """load next video"""
        if not self.state.get('TrackURI'):
            return False
        next_file = get_next_file(self.state['TrackURI'])
        logging.info('next file recognized: %s', next_file)
        if next_file and self.url_prefix:
            url = '%s%s' % (self.url_prefix, quote(next_file))
            self.load(url)
            return True
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
            # while self.dmr.position_info().get('TrackDuration') == '00:00:00':
            while self._get_position_info() == '00:00:00':
                sleep(0.5)
                logging.info('Waiting for duration to be recognized correctly, url=%s', unquote(url))
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


def ls_dir(path):
    """list dir files in dict/json"""
    if path == '/':
        path = ''
    parent, list_folder, list_mp4, list_video, list_other = [], [], [], [], []
    if path:
        path = re.sub('([^/])$', '\\1/', path)  # make sure path end with '/'
        parent = [{'filename': '..', 'type': 'folder', 'path': '%s..' % path}]
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
    return {'filesystem': (parent + list_folder + list_mp4 + list_video + list_other)}


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


def get_size(*filename):
    """get file size in human read format from file"""
    size = os.path.getsize('%s/%s' % (VIDEO_PATH, ''.join(filename)))
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
            self.finish({'error': 'No DMR.'})
            return None
        return func(self, *args, **kwargs)
    return no_dmr


def get_next_file(src):  # not strict enough
    """get next related video file"""
    logging.info(src)
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
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        self.render('index.html')


class HistoryHandler(tornado.web.RequestHandler):
    """Return play history list"""
    def data_received(self, chunk):
        pass

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
                                  'latest_date': s[3], 'path': os.path.dirname(s[0]),
                                  'exist': os.path.exists('%s/%s' % (VIDEO_PATH, s[0]))}
                                 for s in run_sql('select * from history order by LATEST_DATE desc'
                                                 )]})


class FileSystemListHandler(tornado.web.RequestHandler):
    """Get static folder list in json"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        try:
            self.finish(ls_dir(kwargs.get('path')))
        except Exception as exc:
            raise tornado.web.HTTPError(404, reason=str(exc))


class FileSystemMoveHandler(tornado.web.RequestHandler):
    """Move file to '.old' folder"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        src = kwargs.get('src')
        filename = '%s/%s' % (VIDEO_PATH, src)
        dir_old = '%s/%s/.old' % (VIDEO_PATH, os.path.dirname(src))
        if not os.path.exists(dir_old):
            os.mkdir(dir_old)
        try:
            shutil.move(filename, dir_old)  # gonna do something when file is occupied
        except Exception as exc:
            logging.warning('move file failed: %s', exc)
            raise tornado.web.HTTPError(404, reason=str(exc))
        self.finish(ls_dir('%s/' % os.path.dirname(src)))


class SaveHandler(tornado.web.RequestHandler):
    """Save play history"""
    executor = ThreadPoolExecutor(5)

    def data_received(self, chunk):
        pass

    @tornado.concurrent.run_on_executor
    def post(self, *args, **kwargs):
        arguments = json.loads(self.request.body.decode())
        # position = arguments.get('position', 0)
        # duration = arguments.get('duration', 0)
        # position = self.get_argument('position', 0)
        # duration = self.get_argument('duration', 0)
        # save_history(kwargs.get('src'), position, duration)
        save_history(kwargs.get('src'), **arguments)


class DlnaLoadHandler(tornado.web.RequestHandler):
    """DLNA load file web interface"""
    def data_received(self, chunk):
        pass

    @check_dmr_exist
    def get(self, *args, **kwargs):
        src = kwargs.get('src')
        srv_host = self.request.headers['Host']
        if srv_host.startswith('127.0.0.1'):
            self.finish('should not use 127.0.0.1 as host to load throuh DLNA')
            return
        if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
            logging.warning('File not found: %s', src)
            self.finish('Error: File not found.')
            return
        logging.info('start loading...tracker state:%s', TRACKER.state.get('CurrentTransportState'))
        TRACKER.url_prefix = 'http://%s/video/' % srv_host
        url = 'http://%s/video/%s' % (srv_host, quote(src))
        TRACKER.load(url)
        self.finish('loading %s' % src)


class DlnaNextHandler(tornado.web.RequestHandler):
    """DLNA jump to next video file web interface"""
    def data_received(self, chunk):
        pass

    @check_dmr_exist
    def get(self, *args, **kwargs):
        if not TRACKER.loadnext():
            self.finish({'warning': "Can't get next file"})


class DlnaHandler(tornado.web.RequestHandler):
    """DLNA operation web interface"""
    def data_received(self, chunk):
        pass

    @check_dmr_exist
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        if opt in ('play', 'pause', 'stop'):
            if opt == 'stop':
                TRACKER.loop_playback.clear()
            method = getattr(TRACKER.dmr, opt)
            ret = method()
        elif opt == 'seek':
            ret = TRACKER.dmr.seek(kwargs.get('progress'))
        elif opt == 'playtoggle':
            if TRACKER.state.get('CurrentTransportState') == 'PLAYING':
                ret = TRACKER.dmr.pause()
            else:
                ret = TRACKER.dmr.play()
        else:
            return
        if ret:
            self.finish({'success': 'opt: %s ' % opt})
        if not ret:
            self.finish({'error': 'Failed!'})


class DlnaVolumeControlHandler(tornado.web.RequestHandler):
    """Tune volume through DLNA web interface"""
    def data_received(self, chunk):
        pass

    @check_dmr_exist
    def get(self, *args, **kwargs):
        opt = kwargs.get('opt')
        vol = int(TRACKER.dmr.get_volume())
        if opt == 'up':
            vol += 1
        elif opt == 'down':
            vol -= 1
        if not 0 <= vol <= 100:
            self.finish({'warning':'volume range exceeded'})
        elif TRACKER.dmr.volume(vol):
            self.finish(str(vol))
        else:
            self.finish({'error': 'failed'})


class SystemCommandHandler(tornado.web.RequestHandler):
    """some system maintainence command web interface"""
    def data_received(self, chunk):
        pass

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
            raise tornado.web.HTTPError(403, reason='no such operation')


class SetDmrHandler(tornado.web.RequestHandler):
    """set dmr web interface"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        if TRACKER.set_dmr(kwargs.get('dmr')):
            self.finish('Done.')
        else:
            self.finish('Error: Failed!')


class SearchDmrHandler(tornado.web.RequestHandler):
    """Mannually search DMR web interface"""
    def data_received(self, chunk):
        pass

    def get(self, *args, **kwargs):
        TRACKER.discover_dmr()


class DlnaWebSocketHandler(tornado.websocket.WebSocketHandler):
    """DLNA info retriever use web socket"""
    users = set()
    last_message = {}

    def data_received(self, chunk):
        pass

    def open(self, *args, **kwargs):
        logging.info('ws connected: %s', self.request.remote_ip)
        self.users.add(self)
        self.on_pong()

    def on_message(self, message):
        pass

    def on_pong(self, data=None):
        if self.last_message != TRACKER.state:
            logging.debug(TRACKER.state)
            self.write_message(TRACKER.state)
            self.last_message = TRACKER.state.copy()

    def on_close(self):
        logging.info('ws close: %s', self.request.remote_ip)
        self.users.remove(self)


class TestHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(99)
    """test only"""
    def data_received(self, chunk):
        pass

    def test(self):
        sleep(1)
        return 'test sleep 1'

    @tornado.concurrent.run_on_executor
    def get(self, *args, **kwargs):
        x = TRACKER.async_run(self.test)
        logging.info(x)
        self.write(x)


class ApiHandler(tornado.web.RequestHandler):
    # executor = ThreadPoolExecutor(99)
    """api test"""
    def data_received(self, chunk):
        pass

    # @tornado.concurrent.run_on_executor
    def post(self, *args, **kwargs):
        json_obj = self.request.body.decode()
        result = JsonRpc.run(json_obj)
        logging.info('result: %s', result)
        self.write(result)


class JsonRpc():
    """Json RPC class"""
    @classmethod
    def run(cls, json_obj):
        """run RPC method"""
        logging.info(json_obj)
        val = {'jsonrpc': '2.0'}
        try:
            obj = json.loads(json_obj)
        except json.decoder.JSONDecodeError as exc:
            logging.info(exc, exc_info=True)
            val['error'] = {"code": -32700, 'message': 'Parse error'}
            return val
        logging.info(obj)
        method = obj.get('method')
        params = obj.get('params')
        val['id'] = obj.get('id')
        args = params if isinstance(params, list) else []
        kwargs = params if isinstance(params, dict) else {}
        logging.info('running method: %s with params: %s', method, params)
        try:
            result = getattr(cls, method)(*args, **kwargs)
            if result is True:
                result = 'Success'
            elif result is False:
                result = 'Failed'
            val['result'] = result
        except AttributeError as exc:
            val['error'] = {"code": -32601, 'message': 'Method not found'}
        except TypeError as exc:
            val['error'] = {"code": -32602, 'message': 'Invalid params'}
        except Exception as exc:
            logging.warning(exc, exc_info=True)
            val['error'] = {"code": -1, 'message': str(exc)}
        return val

    @classmethod
    def test(cls):
        return 'test'

HANDLERS = [
    (r'/', IndexHandler),
    (r'/test', TestHandler),  # test
    (r'/api', ApiHandler),
    (r'/fs/ls/(?P<path>.*)', FileSystemListHandler),
    (r'/fs/move/(?P<src>.*)', FileSystemMoveHandler),
    (r'/hist/(?P<opt>\w*)/?(?P<src>.*)', HistoryHandler),
    (r'/sys/(?P<opt>\w*)', SystemCommandHandler),
    (r'/link', DlnaWebSocketHandler),
    (r'/dlna/setdmr/(?P<dmr>.*)', SetDmrHandler),
    (r'/dlna/searchdmr', SearchDmrHandler),
    (r'/dlna/vol/(?P<opt>\w*)', DlnaVolumeControlHandler),
    (r'/dlna/next', DlnaNextHandler),
    (r'/dlna/load/(?P<src>.*)', DlnaLoadHandler),
    (r'/dlna/(?P<opt>\w*)/?(?P<progress>.*)', DlnaHandler),
    (r'/wp/save/(?P<src>.*)', SaveHandler),
    (r'/video/(.*)', tornado.web.StaticFileHandler, {'path': VIDEO_PATH}),
]

SETTINGS = {
    'static_path': 'static',
    'template_path': 'views',
    'gzip': True,
    'debug': True,
    'websocket_ping_interval': 0.2,
}

# initialize logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s [line:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
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
    APP.listen(8888, xheaders=True)
    tornado.ioloop.IOLoop.instance().start()
