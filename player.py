﻿#!/usr/bin/python3
# -*- coding:utf-8 -*-
# import os
import shutil
import sqlite3
# import sys
import math
import json

from bottle import *  # pip install bottle

# db = lambda: sqlite3.connect('player.db')  # define DB connection


def db():
    return sqlite3.connect('player.db')

# def time_format(time):#turn seconds into hh:mm:ss time format
    # m, s = divmod(time, 60)
    # h, m = divmod(time/60, 60)
    # return "%02d:%02d:%02d" % (h, m, s)


def get_size(filename):
    size = os.path.getsize('./static/mp4/%s' % filename)
    if size < 0:
        return 'Out of Range'
    if size < 1024:
        return '%dB' % size
    else:
        unit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'BB']
        l = min(int(math.floor(math.log(size, 1024))), 9)
        return '%.1f%s' % (size/1024.0**l, unit[l])


def init_db():  # initialize database by create history table
    conn = db()
    conn.execute('''create table if not exists history
                    (FILENAME TEXT PRIMARY KEY    NOT NULL,
                    TIME FLOAT NOT NULL,
                    DURATION FLOAT,
                    LATEST_DATE DATETIME NOT NULL);''')
    conn.close()
    return


def update_history_from_db(filename, time, duration):
    conn = db()
    conn.execute('''replace into history 
                    (FILENAME, TIME, DURATION, LATEST_DATE)
                     VALUES(? , ?, ?, DateTime('now'));''', (filename, time, duration))
    conn.commit()
    conn.close()
    return


def load_history_from_db(name):
    if not name:
        return
    conn = db()
    cursor = conn.execute('select TIME from history where FILENAME=?', (name,))
    try:
        progress = cursor.fetchone()[0]
    except Exception as e:
        print(str(e))
        progress = ''
    conn.close()
    return progress


def remove_history_from_db(name=None):
    conn = db()
    if name:
        conn.execute('delete from history where FILENAME= ?', (name,))
    else:
        conn.execute('delete from history')  # clear all
    conn.commit()
    conn.close()
    return


def history_list_json_from_db():
    conn = db()
    historys = conn.execute('select * from history order by LATEST_DATE desc').fetchall()
    conn.close()
    history = [{'filename': s[0], 'time': s[1], 'duration': s[2], 'latest_date': s[3],
                'path': os.path.dirname(s[0])} for s in historys]
                # 'path': '/' + os.path.dirname(s[0])} for s in historys]
    return json.dumps(history)


@route('/play/<src:re:.*\.((?i)mp)4$>')  # player page
def play(src):
    return template('player', src=src, progress=load_history_from_db(src), title=src)


@route('/')  # index page
def index():
    return template('player', src='', progress=0, title='Light mp4 Player')


@route('/move/<src>')
def move(src):
    file = './static/mp4/%s' % src
    dir_old = './static/mp4/%s/old' % os.path.dirname(src)
    if not os.path.exists(dir_old):
        os.mkdir(dir_old)
    try:
        shutil.move(file, dir_old)  # gonna do something when file is occupied
    except Exception as e:
        abort(404, str(e))
    return fs_folder(os.path.dirname(src)+'/')


@route('/list')  # list play history
def list():
    return history_list_json_from_db()

    
@route('/player.php')  # index
def video_player():
    action = request.query.action
    src = request.query.src
    if action == 'save':
        time = request.GET.get('time')
        duration = request.GET.get('duration')
        update_history_from_db(src, time, duration)
        return
    elif action == 'del':
        remove_history_from_db(src)
        return history_list_json_from_db()
    elif action == 'clear':
        remove_history_from_db()
        return history_list_json_from_db()
    elif action == 'list':
        return history_list_json_from_db()
    elif action == 'move':
        file = './static/mp4/%s' % src
        dir_old = './static/mp4/%s/old' % os.path.dirname(src)
        if not os.path.exists(dir_old):
            os.mkdir(dir_old)
        try:
            shutil.move(file, dir_old)  # gonna do something when file is occupied
        except Exception as e:
            abort(404, str(e))
        return folder(os.path.dirname(src))
    elif not os.path.exists('./static/mp4/%s' % src):
        redirect('/player.php')
    if src:
        title = os.path.basename(src)
    else:
        title = 'Light mp4 Player'
    return template('player', src=src, progress=load_history_from_db(src), title=title)


@route('/suspend.php')
def suspend():
    if sys.platform == 'win32':
        import ctypes
        dll = ctypes.WinDLL('powrprof.dll')
        if dll.SetSuspendState(0, 1, 0):
            return 'Suspending...'
        else:
            return 'Suspend Failure!'
    else:
        return 'OS not supported!'


@route('/shutdown.php')
def shutdown():
    if sys.platform == 'win32':
        os.system("shutdown.exe -f -s -t 0")
    else:
        os.system("sudo /sbin/shutdown -h now")


@route('/restart.php')
def restart():
    if sys.platform == 'win32':
        os.system("shutdown.exe -f -r -t 0")
    else:
        os.system("sudo /sbin/shutdown -r now")


@route('/static/<filename:re:.*>')  # static files access
def static(filename):
    return static_file(filename, root='./static')


@route('/fs/<filename:re:.*\.((?i)mp)4$>')  # mp4 static files access.
# to support larger files(>2GB), you should use apache "AliasMatch"
def fs_mp4(filename):
    return static_file(filename, root='./static/mp4')


@route('/<filename:re:.*\.((?i)mp)4$>')  # mp4 static files access.
# to support larger files(>2GB), you should use apache "AliasMatch"
def mp4(filename):
    return static_file(filename, root='./static/mp4')


@route('/fs/<path:re:.*>')  # static folder access
def fs_folder(path):
    try:
        fs_list, fs_list_folder, fs_list_mp4, fs_list_other = [], [], [], []
        if path != '':
            fs_list.append({'type': 'folder', 'path': '/%s..' % path, 'filename': '..'})
        for file in os.listdir('./static/mp4/%s' % path):
            if os.path.isdir('./static/mp4/%s%s' % (path, file)):
                fs_list_folder.append({'filename': file, 'type': 'folder', 'path': '/%s%s' % (path, file)})
            elif re.match('.*\.((?i)mp)4$', file):
                fs_list_mp4.append({'filename': file, 'type': 'mp4',
                                    'path': '%s%s' % (path, file), 'size': get_size(path + file)})
            else:
                fs_list_other.append({'filename': file, 'type': 'other',
                                      'path': '%s%s' % (path, file), 'size': get_size(path + file)})

            # fs_list = fs_list + fs_list_folder+fs_list_mp4+fs_list_other
        # return json.dumps(fs_list)
        return json.dumps(fs_list + fs_list_folder+fs_list_mp4+fs_list_other)
    except Exception as e:
        abort(404, str(e))

    
# @route('/<path:re:.*>')  # static folder access
# def folder(path):
    # try:
        # html_dir, html_mp4, html_files = '', '', ''
        # if path != '':
            # dirs = path.split('/')
            # html_dir = '''
            # <tr><td colspan=3>
            # <ol class="breadcrumb">
              # <li>
                # <span class="filelist folder">
                  # <i class="glyphicon glyphicon-home" title="/"></i>
                # </span>
              # </li>
              # '''
            # for n, i in enumerate(dirs[:-1:], 1):
                # print("/%s %s" % ('/'.join(dirs[0:n]), i))
                # html_dir += '''
                # <li><span class="filelist folder" title="/%s">%s</span>
                # </li>''' % ('/'.join(dirs[0:n]), i)
            # html_dir += '''
              # <li class="active">%s</li>
            # </ol>
            # </td></tr>''' % dirs[-1]
            # path = '%s/' % path.strip('/')
            # html_dir += '''
            # <tr>
              # <td><i class="glyphicon glyphicon-folder-close"></i></td>
              # <td class="filelist folder" colspan=2 title="/%s..">..</td>
            # </tr>''' % path
        # for file in os.listdir('./static/mp4/%s' % path):
            # if os.path.isdir('./static/mp4/%s%s' % (path, file)):
                # html_dir += '''
                # <tr>
                  # <td><i class="glyphicon glyphicon-folder-close"></i></td>
                  # <td class="filelist folder" title="/%s%s">%s</td>
                  # <td class="move" title="%s%s">
                    # <i class="glyphicon glyphicon-remove-circle" title="%s%s"></i>
                  # </td>
                # </tr>''' % (path, file, file, path, file, path, file)
            # elif re.match('.*\.((?i)mp)4$', file):
                # html_mp4 += '''
                # <tr>
                  # <td><i class="glyphicon glyphicon-film"></i></td>
                  # <td class="filelist mp4" title="?src=%s%s">
                    # %s<br><small>%s</small>
                  # </td>
                  # <td class="move" title="%s%s">
                    # <i class="glyphicon glyphicon-remove-circle" title="%s%s"></i>
                  # </td>
                # </tr>
                # ''' % (path, file, file, get_size(path + file), path, file, path, file)
            # else:
                # html_files += '''
                # <tr>
                  # <td><i class="glyphicon glyphicon-file"></i></td>
                  # <td>
                    # <span class="filelist other">%s</span>
                    # <br><small>%s</small>
                  # </td>
                  # <td class="move" title="%s%s">
                    # <i class="glyphicon glyphicon-remove-circle" title="%s%s"></i>
                  # </td>
                # </tr>''' % (file, get_size(path + file), path, file, path, file)
        # return ''.join([html_dir, html_mp4, html_files])
    # except Exception as e:
        # abort(404, str(e))

os.chdir(os.path.dirname(os.path.abspath(__file__)))  # set file path as current
init_db()

if __name__ == '__main__':
    os.system('start http://127.0.0.1:8081/')  # open the page automatic
    # os.system('start http://127.0.0.1:8081/player.php')  # open the page automatic
    # os.system('start http://127.0.0.1:8081/fs/')  # open the page automatic
    run(host='0.0.0.0', port=8081, debug=True)  # you can change port here
