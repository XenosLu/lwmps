﻿#!/usr/bin/python3
# -*- conding:utf-8 -*-
import os
import shutil
import sqlite3
import sys
import math

from bottle import *#pip install bottle

db = lambda: sqlite3.connect('player.db')#define DB connection
def time_format(time):#turn seconds into hh:mm:ss time format
	m, s = divmod(time, 60)
	h, m = divmod(time/60, 60)
	return "%02d:%02d:%02d" % (h, m, s)

def get_size(file):
	size = os.path.getsize('./static/mp4/%s' % file)
	if size < 0:
		return 'Out of Range'
	if size < 1024:
		return '%dB' % size
	else:
		unit = ['B','KB','MB','GB','TB','PB','EB','ZB','YB','BB']
		l = int(math.floor(math.log(size,1024)))
		if l > 9:
			l=9
		return '%.1f%s' % (size/1024.0**l,unit[l])

def InitDB():#initialize database by create history table
	conn = db()
	conn.execute('''create table if not exists history
		(FILENAME TEXT PRIMARY KEY	NOT NULL,
		TIME FLOAT NOT NULL,
		DURATION FLOAT,
		LATEST_DATE DATETIME NOT NULL);''')
	conn.close()
	return

def update_history_from_db(filename, time, duration):
	conn = db()
	conn.execute('''replace into history 
		(FILENAME, TIME, DURATION, LATEST_DATE)
		VALUES(? , ?, ?, DateTime('now'));''',(filename, time, duration))
	conn.commit()
	conn.close()
	return

def load_history_from_db(name):
	if not name:
		return
	conn = db()
	cursor=conn.execute("select TIME from history where FILENAME=?",(name,))
	try:
		time = cursor.fetchone()[0]
	except Exception as e:
		print(str(e))
		time = ''
	conn.close()
	return time

def remove_history_from_db(name=None):
	conn = db()
	if name:
		conn.execute("delete from history where FILENAME=?",(name,))
	else:
		conn.execute("delete from history")#clearall
	conn.commit()
	conn.close()
	return

def list_history_from_db():
	conn = db()
	historys=conn.execute('''
		select * from history order by LATEST_DATE desc''').fetchall()
	conn.close()
	html=['''
		<tr>
		  <td><i onclick="ajax('/%s')"class='icono-video'></i></td>
		  <td class='filelist'><a href='?src=%s'>%s</a>
		  <br><small>%s | %s/%s</small></td>
		  <td><i class='icono-trash del'>%s</i></td>
		</tr>''' % (#<td><i class='icono-trash' onclick="ajax('?action=del&src=%s')"></i></td>
		os.path.dirname(s[0]), s[0], s[0], s[3], time_format(s[1]),\
		time_format(s[2]),s[0])
		for s in historys]
	
	if html:
		return '''%s
		<tr>
		  <td colspan=3>
			<button id='clear' style='font-size: 1.2em;'>Clear History</button>
		  </td>
		</tr>''' % ''.join(html)
		#</tr>''' % html
	else:
		return '<tr><td>Empty...</td></tr>'

@route('/player.php')#index
def videoplayer():
	action = request.query.action
	src = request.query.src
	if action == 'save':
		time = request.GET.get('time')
		duration = request.GET.get('duration')
		update_history_from_db(src, time, duration)
		return list_history_from_db()
	elif action == 'del':
		remove_history_from_db(src)
		return list_history_from_db()
	elif action == 'clear':
		remove_history_from_db()
		return list_history_from_db()
	elif action == 'list':
		return list_history_from_db()
	elif action == 'move':
		file='./static/mp4/%s' % src
		dir_old='./static/mp4/%s/old' % os.path.dirname(src)
		if not os.path.exists(dir_old):
			os.mkdir(dir_old)
		try:
			shutil.move(file,dir_old)#gonna do something when file is occupied
		except Exception as e:
			abort(404,str(e))
		return folder(os.path.dirname(src))
	elif not os.path.exists('./static/mp4/%s' % src):
		#remove_history_from_db(src)
		redirect('/player.php')
	if src:
		title=os.path.basename(src)
	else:
		title='Light mp4 Player'
	return template(
	'player', src=src, progress=load_history_from_db(src), title=title)

@route('/suspend.php')
def suspend():
	if sys.platform == 'win32':
		import ctypes
		dll = ctypes.WinDLL('powrprof.dll')
		# os.system("psshutdown.exe /accepteula -d -t 0")
		if dll.SetSuspendState(0,1,0):
			return 'Suspending...'
		else:
			return 'Suspend Failure!'
	else:
		# os.system("sudo /sbin/shutdown -h now")
		return 'OS not supported!'

@route('/<file:re:.*\.((?i)mp)4$>')#mp4 static files access. to support larger files(>2GB), you should use apache "AliasMatch"
def static(file):
	return static_file(file, root='./static/mp4')

@route('/<dir:re:.*>')#static folder access
def folder(dir):
	try:
		html_dir,html_mp4,html_files='','',''
		if dir!='':
			dir='%s/' % dir.strip('/')
			html_dir+='''
			<tr>
			  <td><i class="icono-folder"></i></td>
			  <td class="filelist" colspan=2 onclick="ajax('/%s..')">..</td>
			</tr>''' % dir
		for file in os.listdir('./static/mp4/%s' % dir):
			if os.path.isdir('./static/mp4/%s%s' % (dir,file)):
				html_dir+='''
				<tr>
				  <td><i class="icono-folder"></i></td>
				  <td class="filelist folder" title="/%s%s">%s</td>
				  <td><i class="icono-trash move">%s%s</i></td>
				</tr>''' % (dir,file,file,dir,file)
			elif re.match('.*\.((?i)mp)4$',file):
				html_mp4+='''
				<tr>
				  <td><i class="icono-video"></i></td>
				  <td>
					<a href="/player.php?src=%s%s">%s</a>
					<br><small>%s</small>
				  </td>
				  <td><i class="icono-trash move">%s%s</i></td>
				</tr>''' % (dir,file,file,get_size(dir+file),dir,file)
			else:
				html_files+='''
				<tr>
				  <td></td>
				  <td>
					<span style="color:grey">%s</span>
					<br><small>%s</small>
				  </td>
				  <td><i class="icono-trash move">%s%s</i></td>
				</tr>''' % (file,get_size(dir+file),dir,file)
		return "".join([html_dir,html_mp4,html_files])
	except Exception as e:
		abort(404,str(e))

os.chdir(os.path.dirname(os.path.abspath(__file__)))#set file path as current path
InitDB()

if __name__=="__main__":
	os.system('start http://127.0.0.1:8081/player.php')#open the page automatic
	run(host='0.0.0.0', port=8081, debug=True)#you can change port here
