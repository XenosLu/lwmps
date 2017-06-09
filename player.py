﻿#!/usr/bin/python3
# -*- coding:utf-8 -*-
import os
import sys
import shutil
import sqlite3
import math
import json
import re

# from bottle import *  # pip install bottle  # 1.2
from bottle import route, run, template, static_file, abort, request, redirect  # pip install bottle  # 1.2

MP4_PATH = './static/mp4'  # mp4 file path


def db():
    return sqlite3.connect('player.db')  # define DB connection


def run_sql(sql, *args):  # run SQL
    conn = db()
    try:
        cursor = conn.execute(sql, args)
        result = cursor.fetchall()
        cursor.close()
        if cursor.rowcount > 0:
            conn.commit()
    except Exception as e:
        print(str(e))
        result = []
    # print('%s %d' % (sql,cursor.rowcount))
    # for i in ['delete', 'replace']:
        # if sql.lower().startswith(i):
            # conn.commit()
            # break
    # if not result:
        # conn.commit()
    finally:
        conn.close()
    return result


def get_size(filename):
    size = os.path.getsize('%s/%s' % (MP4_PATH, filename))
    if size < 0:
        return 'Out of Range'
    if size < 1024:
        return '%dB' % size
    else:
        unit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB', 'BB']
        l = min(int(math.floor(math.log(size, 1024))), 9)
        return '%.1f%s' % (size/1024.0**l, unit[l])


def init_db():  # initialize database by create history table
    run_sql('''create table if not exists history
                    (FILENAME text PRIMARY KEY not null,
                    TIME float not null,
                    DURATION float, LATEST_DATE datetime not null);''')
    return


def update_from_history_db(filename, time, duration):
    run_sql('''replace into history (FILENAME, TIME, DURATION, LATEST_DATE)
                     values(? , ?, ?, DateTime('now', 'localtime'));''', filename, time, duration)
    return


def load_from_history_db(name):
    if not name:
        return 0
    # conn = db()
    # cursor = conn.execute('select TIME from history where FILENAME=?', (name,))
    progress = run_sql('select TIME from history where FILENAME=?', name)
    # progress = cursor.fetchone()
    # cursor.close()
    # conn.close()
    # return str(len(progress))
    if len(progress) == 0:
        return 0
    # else
    return str(progress[0][0])
    # if progress:
        # return progress[0][0]
    # return 0
    # try:
        # progress = cursor.fetchone()[0]
    # except Exception as e:
        # print(str(e))
        # progress = ''


def remove_from_history_db(name=None):
    # conn = db()
    if name:
        run_sql('delete from history where FILENAME= ?', name)
        # conn.execute('delete from history where FILENAME= ?', (name,))
    else:
        # conn.execute('delete from history')  # clear all
        run_sql('delete from history')  # clear all
    # conn.commit()
    # conn.close()
    return


@route('/list')  # list play history
def list_from_history_db():
    # conn = db()
    # historys = conn.execute('select * from history order by LATEST_DATE desc').fetchall()
    historys = run_sql('select * from history order by LATEST_DATE desc')
    # conn.close()
    history = [{'filename': s[0], 'time': s[1], 'duration': s[2], 'latest_date': s[3],
                'path': os.path.dirname(s[0])} for s in historys]
    return json.dumps(history)


@route('/')  # index page
def index():
    return template('player', src='', progress=0, title='Light mp4 Player')


@route('/play/<src:re:.*\.((?i)mp)4$>')  # player page
def play(src):
    if not os.path.exists('%s/%s' % (MP4_PATH, src)):
        redirect('/')
    return template('player', src=src, progress=load_from_history_db(src), title=src)


@route('/clear')  # clear play history
def clear():
    remove_from_history_db()
    return list_from_history_db()


@route('/remove/<src:path>')  # clear from play history
def remove(src):
    remove_from_history_db(src)
    return list_from_history_db()


@route('/move/<src:path>')  # move file to old folder
def move(src):
    file = '%s/%s' % (MP4_PATH, src)
    dir_old = '%s/%s/old' % (MP4_PATH, os.path.dirname(src))
    if not os.path.exists(dir_old):
        os.mkdir(dir_old)
    try:
        shutil.move(file, dir_old)  # gonna do something when file is occupied
    except Exception as e:
        print(str(e))
        abort(404, str(e))
    return fs_dir('%s/' % os.path.dirname(src))


@route('/save/<src:path>')  # save play progress
def save(src):
    # src = request.query.src
    progress = request.GET.get('progress')
    duration = request.GET.get('duration')
    update_from_history_db(src, progress, duration)
    return


@route('/suspend')  # suspend the server
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


@route('/shutdown')  # shutdown the server
def shutdown():
    if sys.platform == 'win32':
        os.system("shutdown.exe -f -s -t 0")
    else:
        os.system("sudo /sbin/shutdown -h now")
    return 'shutting down...'


@route('/restart')  # restart the server
def restart():
    if sys.platform == 'win32':
        os.system("shutdown.exe -f -r -t 0")
    else:
        os.system("sudo /sbin/shutdown -r now")
    return 'restarting...'


@route('/static/<filename:path>')  # static files access
def static(filename):
    return static_file(filename, root='./static')


@route('/mp4/<filename:re:.*\.((?i)mp)4$>')  # mp4 static files access.
# to support larger files(>2GB), you should use web server to deal with static files like apache "AliasMatch"
def static_mp4(filename):
    return static_file(filename, root=MP4_PATH)


@route('/fs/<path:re:.*>')  # get static folder json list
def fs_dir(path):
    try:
        fs_list, fs_list_folder, fs_list_mp4, fs_list_other = [], [], [], []
        if path != '':
            fs_list.append({'type': 'folder', 'path': '/%s..' % path, 'filename': '..'})
        for file in os.listdir('%s/%s' % (MP4_PATH, path)):
            if os.path.isdir('%s/%s%s' % (MP4_PATH, path, file)):
                fs_list_folder.append({'filename': file, 'type': 'folder', 'path': '/%s%s' % (path, file)})
            elif re.match('.*\.((?i)mp)4$', file):
                fs_list_mp4.append({'filename': file, 'type': 'mp4',
                                    'path': '%s%s' % (path, file), 'size': get_size(path + file)})
            else:
                fs_list_other.append({'filename': file, 'type': 'other',
                                      'path': '%s%s' % (path, file), 'size': get_size(path + file)})
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

if __name__ == '__main__':  # for debug

    os.system('start http://127.0.0.1:8081/')  # open the page automatic
    run(host='0.0.0.0', port=8081, debug=True)  # run demo server
