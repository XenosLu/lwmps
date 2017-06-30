﻿#!/usr/bin/python3
# -*- coding:utf-8 -*-
import os
import sys
import shutil
import sqlite3
import math
import json
import re
from urllib.parse import quote, unquote
from time import sleep, time
from threading import Thread

from bottle import route, post, template, static_file, abort, request, redirect, run  # pip install bottle  # 1.2

import dlnap  # https://github.com/ttopholm/dlnap

VIDEO_PATH = './static/mp4'  # mp4 file path
DLNAP = None
DLNA_STATE = None


class DLNA_Tracker(Thread):

    def __init__(self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        self.__flag = threading.Event()
        self.__flag.set()
        self.__running = threading.Event()
        self.__running.set()

    def run(self):
        while self.__running.isSet():
            self.__flag.wait()
            print(time.time())
            time.sleep(1)

    def pause(self):
        self.__flag.clear()

    def resume(self):
        self.__flag.set()

    def stop(self):
        self.__flag.set()
        self.__running.clear()  
        

def dlna_tracker():
    global DLNA_STATE
    stop = False
    while not stop:
        try:
            DLNA_STATE = dlnap._xpath(DLNAP.position_info(), 's:Envelope/s:Body/u:GetPositionInfoResponse')
            print(DLNA_STATE['TrackURI'])
            # DLNA_STATE['TrackURI'] = 
            src = unquote(re.sub('http://.*/video/', '', DLNA_STATE['TrackURI'][0]))
            save_history(src, time_to_second(DLNA_STATE['RelTime'][0]), time_to_second(DLNA_STATE['TrackDuration'][0]))
            for i in range(3):
                sleep(1)
                print('tick: %s' % time())
                # RelTime += 1
            state = dlnap._xpath(DLNAP.info(), 's:Envelope/s:Body/u:GetTransportInfoResponse/CurrentTransportState')  # PAUSED_PLAYBACK
            if state != 'PLAYING':
                stop = True
            # DLNAP.get_volume.CurrentVolume
        except Exception as e:
            print(e)


def start_dlna_tracker():
    t = Thread(target=dlna_tracker)
    t.setDaemon(True)
    t.start()

def discover_dlnap():
    global DLNAP
    if not DLNAP:
        allDevices = dlnap.discover(name='', ip='', timeout=2, st=dlnap.URN_AVTransport_Fmt, ssdp_version=1)
        if len(allDevices) > 0:
            DLNAP = allDevices[0]


def run_sql(sql, *args):
    with sqlite3.connect('player.db') as conn:
        try:
            cursor = conn.execute(sql, args)
            result = cursor.fetchall()
            cursor.close()
            if cursor.rowcount > 0:
                conn.commit()
        except Exception as e:
            print(str(e))
            result = ()
    return result


def second_to_time(second):  # turn seconds into hh:mm:ss time format
    m, s = divmod(second, 60)
    h, m = divmod(second/60, 60)
    return '%02d:%02d:%02d' % (h, m, s)


def time_to_second(time_str):  # turn hh:mm:ss time format into seconds
    return sum([int(i)*60**n for n,i in enumerate(str(time_str).split(':')[::-1])])


def get_size(*filename):
    size = os.path.getsize('%s/%s' % (VIDEO_PATH, ''.join(filename)))
    if size < 0:
        return 'Out of Range'
    if size < 1024:
        return '%dB' % size
    else:
        unit = ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'B')
        l = min(int(math.floor(math.log(size, 1024))), 9)
        return '%.1f%sB' % (size/1024.0**l, unit[l])


def load_history(name):
    position = run_sql('select POSITION from history where FILENAME=?', name)
    if len(position) == 0:
        return 0
    return position[0][0]


def save_history(src, position, duration):
    if position < 10 or duration < 10:
        return
    run_sql('''replace into history (FILENAME, POSITION, DURATION, LATEST_DATE)
               values(? , ?, ?, DateTime('now', 'localtime'));''', src, position, duration)


@route('/list')
def list_history():
    """Return play history list"""
    return json.dumps([{'filename': s[0], 'position': s[1], 'duration': s[2],
                        'latest_date': s[3], 'path': os.path.dirname(s[0])}
                       for s in run_sql('select * from history order by LATEST_DATE desc')])


@route('/')
def index():
    return template('player', mode='index', src='', position=0, title='Light mp4 Player')


@route('/play/<src:re:.*\.((?i)mp)4$>')
def play(src):
    """Video play page"""
    if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
        redirect('/')
    return template('player', mode='player', src=src, position=load_history(src), title=src)


@route('/dlna/<src:re:.*\.((?i)(mp4|mkv|avi))$>')
def dlna_load(src):
    """Video DLNA play page"""
    if not os.path.exists('%s/%s' % (VIDEO_PATH, src)):
        redirect('/')
    discover_dlnap()
    url = 'http://%s/video/%s' % (request.urlparts.netloc, quote(src))
    try:
        # if dlnap._xpath(DLNAP.position_info(), 's:Envelope/s:Body/u:GetPositionInfoResponse/TrackURI') != url:
            # print('url not the same')
        DLNAP.stop()
        sleep(0.75)
        DLNAP.set_current_media(url)
        DLNAP.play()
        position = load_history(src)
        if position:
            sleep(1.8)
            print(second_to_time(position))
            DLNAP.seek(second_to_time(position))
        start_dlna_tracker()
    except Exception as e:
        print(e)
    return template('player', mode='dlna', src=src, position=0, title='DLNA - %s' % src)


@route('/dlnaplay')
def dlna_play():
    """Play video through DLNA"""
    discover_dlnap()
    DLNAP.play()
    start_dlna_tracker()


@route('/dlnapause')
def dlna_pause():
    """Pause video through DLNA"""
    discover_dlnap()
    DLNAP.pause()


@route('/dlnastop')
def dlna_stop():
    """Stop video through DLNA"""
    discover_dlnap()
    DLNAP.stop()


@route('/dlnainfo')
def dlna_info():
    """Get play info through DLNA"""
    return DLNA_STATE
    discover_dlnap()
    # state = dlnap._xpath(DLNAP.info(), 's:Envelope/s:Body/u:GetTransportInfoResponse/CurrentTransportState')  # PAUSED_PLAYBACK, PLAYING
    try:
        dic = dlnap._xpath(DLNAP.position_info(), 's:Envelope/s:Body/u:GetPositionInfoResponse')
        src = unquote(re.sub('http://.*/video/', '', dic['TrackURI'][0]))
        save_history(src, time_to_second(dic['RelTime'][0]), time_to_second(dic['TrackDuration'][0]))
        return dic
    except Exception as e:
        print(e)


@route('/dlnavolume/<v>')
def dlna_volume(v):
    """Set volume through DLNA"""
    discover_dlnap()
    DLNAP.volume(v)


@route('/dlnaseek/<position>')
def dlna_seek(position):
    """Seek video through DLNA"""
    discover_dlnap()
    DLNAP.seek(position)


@route('/clear')
def clear():
    """Clear play history list"""
    run_sql('delete from history')
    return list_history()


@route('/remove/<src:path>')
def remove(src):
    """Remove from play history list"""
    run_sql('delete from history where FILENAME= ?', src)
    return list_history()


@route('/move/<src:path>')
def move(src):
    """Move file to 'old' folder"""
    file = '%s/%s' % (VIDEO_PATH, src)
    dir_old = '%s/%s/old' % (VIDEO_PATH, os.path.dirname(src))
    if not os.path.exists(dir_old):
        os.mkdir(dir_old)
    try:
        shutil.move(file, dir_old)  # gonna do something when file is occupied
    except Exception as e:
        print(str(e))
        abort(404, str(e))
    return fs_dir('%s/' % os.path.dirname(src))


@post('/save/<src:path>')
def save(src):
    """Save play position"""
    position = request.forms.get('position')
    duration = request.forms.get('duration')
    save_history(src, position, duration)


@post('/suspend')
def suspend():
    """Suepend server"""
    if sys.platform == 'win32':
        import ctypes
        dll = ctypes.WinDLL('powrprof.dll')
        if dll.SetSuspendState(0, 1, 0):
            return 'Suspending...'
        else:
            return 'Suspend Failure!'
    else:
        return 'OS not supported!'


@post('/shutdown')
def shutdown():
    """Shutdown server"""
    if sys.platform == 'win32':
        os.system("shutdown.exe -f -s -t 0")
    else:
        os.system("sudo /sbin/shutdown -h now")
    return 'shutting down...'


@post('/restart')
def restart():
    """Restart server"""
    if sys.platform == 'win32':
        os.system('shutdown.exe -f -r -t 0')
    else:
        os.system('sudo /sbin/shutdown -r now')
    return 'restarting...'


@route('/static/<filename:path>')
def static(filename):
    """Static file access"""
    return static_file(filename, root='./static')


@route('/video/<src:re:.*\.((?i)(mp4|mkv|avi))$>')
def static_video(src):
    """video file access
       To support large file(>2GB), you should use web server to deal with static files.
       For example, you can use 'AliasMatch' or 'Alias' in Apache
    """
    return static_file(src, root=VIDEO_PATH)


@route('/fs/<path:re:.*>')
def fs_dir(path):
    """Get static folder list in json"""
    try:
        up, list_folder, list_mp4, list_video, list_other = [], [], [], [], []
        if path:
            up = [{'filename': '..', 'type': 'folder', 'path': '/%s..' % path}]
        for file in os.listdir('%s/%s' % (VIDEO_PATH, path)):
            if os.path.isdir('%s/%s%s' % (VIDEO_PATH, path, file)):
                list_folder.append({'filename': file, 'type': 'folder', 'path': '/%s%s' % (path, file)})
            elif re.match('.*\.((?i)mp)4$', file):
                list_mp4.append({'filename': file, 'type': 'mp4',
                                'path': '%s%s' % (path, file), 'size': get_size(path, file)})
            elif re.match('.*\.((?i)(mkv|avi))$', file):
                list_video.append({'filename': file, 'type': 'video',
                                'path': '%s%s' % (path, file), 'size': get_size(path, file)})
            else:
                list_other.append({'filename': file, 'type': 'other',
                                  'path': '%s%s' % (path, file), 'size': get_size(path, file)})
        return json.dumps(up + list_folder + list_mp4 + list_video + list_other)
    except Exception as e:
        abort(404, str(e))

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # set file path as current
# Initialize DataBase
run_sql('''create table if not exists history
                (FILENAME text PRIMARY KEY not null,
                POSITION float not null,
                DURATION float, LATEST_DATE datetime not null);''')

if __name__ == '__main__':  # for debug
    # os.system('start http://127.0.0.1:8081/')  # open the page automatic
    # os.system('start http://127.0.0.1:8081/dlna/test.mp4')  # open the page automatic
    # run(host='0.0.0.0', port=8081, debug=True, reloader=True)  # run demo server
    run(host='0.0.0.0', port=8081, debug=True)  # run demo server
