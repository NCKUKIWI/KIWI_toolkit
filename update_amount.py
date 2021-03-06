
# coding: utf-8

import datetime
import MySQLdb as mysql
import queue, time, threading
import sys
import requests
import json as jsonpkg
from bs4 import BeautifulSoup as bs

# Modify thread amount here
THREAD_AMOUNT = 4

class Job:
	def __init__(self, name, dept):
		self.name = name
		self.dept = dept
	def do(self, thisThdName):
		while True:
			st = datetime.datetime.now()
			try:
				resForClass = requests.get("http://course-query.acad.ncku.edu.tw/qry/" + self.dept['url'], timeout = 30)
				if (resForClass.status_code != 200):
					print ('[ERR] Unexpected error code while requests, Job({0}) Code : {1}!'.format(self.name, resForClass.status_code))
					continue
			except requests.Timeout as e:
				print ('[Crawler] {0} timeout on {1}!'.format(self.name, thisThdName))# str(datetime.datetime.now() - st)
				continue
			except requests.ConnectionError as e:
				print (self.name + " error")# :" + str(datetime.datetime.now() - st)
				continue
			except Exception as e:
				print ("Unexpected error while requests")
				continue
			else:
				resForClass.encoding = "utf-8"
				resForClass.close()
				btfsClass = bs(resForClass.text, "html.parser")
				# 抽取課程內容
				bodys = []
				bodys.append([])
				colctr = 0
				rowctr = 0
				for body in btfsClass.find_all('td'):
					if not int(colctr/len(heads)) == rowctr: # 確認換列 colctr/len(heads) 為應該所在之行數
						bodys.append([])
						rowctr += 1
					bodys[rowctr].append(body.text) # 一格一格填
					colctr += 1
				# 輸出至newDataPool
				for classindex, classinfo in enumerate(bodys):
					key = ""
					keyTmp = {}
					for index, data in enumerate(classinfo):
						if data == u'查無課程資訊': break
						if heads[index] == 'dept_name':
							keyTmp[heads[index]] = data.strip().replace(' ', '')
						else:
							keyTmp[heads[index]] = data.strip()
						if index == 1 or index == 2: 
							key += data
					try:
						int(keyTmp['extra_amount'])
					except ValueError as e:
						keyTmp['extra_amount'] = '0'
					except KeyError as e:
						logOutput = '[KeyERR] |' + datetime.datetime.today().isoformat() + '| ' + self.name + ": " + jsonpkg.dumps(classinfo, ensure_ascii=False) + ' | ' + jsonpkg.dumps(keyTmp) + '\n'
						with open('devLog', 'a') as f:
							f.write(logOutput)
					if not key == "":
						newDataPool[key] = keyTmp
				td = datetime.datetime.now() - st
				print("[Crawler] Job({0}) is done by {2}! Spending time = {1}!".format(self.name, td, thisThdName))
				break

def queUpdater():
	global followedCourseDict
	global circleStartTime
	cnxTmp = mysql.connect(**db_config)
	cursorTmp = cnxTmp.cursor(mysql.cursors.DictCursor)
	query = ("SELECT * FROM follow")
	cursorTmp.execute(query)
	followedList = []
	for row in cursorTmp:
		if row['hadNotify'] == 0 and not row['course_id'] == -1:
			followedList.append(row['serial'])
	cnxTmp.close()
	# cursorTmp.close()
	deptList = []
	serialDictByDept = {}
	for text in followedList:
		if len(text) == 5:
			if not text[0:2] in serialDictByDept:
				serialDictByDept[text[0:2]] = []
				serialDictByDept[text[0:2]].append(text)
				deptList.append(text[0:2])
			else:
				if not text in serialDictByDept[text[0:2]]:
					serialDictByDept[text[0:2]].append(text)
	# print deptList
	# print serialDictByDept
	for num, dept in enumerate(deptList):
		# if num >= 4: break
		# print dept
		que.put(Job(dept, deptDict[dept]))
	print("[Queueing] Queue size = {0}... Circle time = {1}!".format(que.qsize(), datetime.datetime.now()-circleStartTime))
	followedCourseDict = serialDictByDept
	circleStartTime = datetime.datetime.now()

def doJob(*args):
	global queUpdaterWorking
	queueing = args[0]
	thdName = args[1]
	while True:
		if queueing.qsize() == 0:
			if not queUpdaterWorking:
				queUpdaterWorking = True
				queUpdater()
				queUpdaterWorking = False
			else:
				time.sleep(1)
		if queueing.qsize() > 0:
			job = que.get()
			job.do(thdName)

def doJobA9():
	while True:
		job = Job('A9', deptDict['A9'])
		job.do('Thd[9]')

while True:
	try:
		res = requests.get("http://course-query.acad.ncku.edu.tw/qry/", timeout = 30)
		if not res.status_code == 200:
			print ('[ERR] Unexpected error code while requests, Job(INIT) Code : {0}!'.format(res.status_code))
			continue
		res.close()
		res.encoding = "utf-8"
	except requests.Timeout as e:
		print ('[Init] timeout!')# str(datetime.datetime.now() - st)
		continue
	except (requests.ConnectionError, ConnectionResetError) as e:
		print ("[Init] connection error")# :" + str(datetime.datetime.now() - st)
		continue
	except Exception as e:
		print ("\n!!! Unexpected error while requests !!!\n")
		continue
	else:
		break
print ("[Init] Get Main Page Succeed")
btfs = bs(res.text, "html.parser")
deptDict = {}
for classes in btfs.select('div .dept'): # Undergraduate
    for a in classes.find_all('a', href = True):
        textTmp = a.text
        deptDict[textTmp[3:5]] = {
            'url':a['href'], 'name':textTmp.strip()
        }
for classes in btfs.select('div .institute'): # Graduate
    for a in classes.find_all('a', href = True):
        textTmp = a.text
        deptDict[textTmp[3:5]] = {
            'url':a['href'], 'name':textTmp.strip()
        }
print ("[Init] {0} depts".format(len(deptDict)))

# general_course is the new feature at 2019-09
heads = ['dept_name', 'dept_code', 'serial', 'course_code', 'class_code', 'class_type',
'grade', 'type', 'group', 'english', 'general_course', 'course_name', 'subject_type', 'credit', 'teacher', 
'choosed_amount', 'extra_amount', 'time', 'classroom', 'description', 'condition',
'expert', 'attribute_code', 'cross_master', 'Moocs']

db_config = {}

with open( 'config.crawler.json') as f:
	db_config = jsonpkg.load(f)['db_py']

cnx = mysql.connect(**db_config)
cursor = cnx.cursor(mysql.cursors.DictCursor)
que = queue.Queue()
followedCourseDict = {}
newDataPool = {}
queUpdaterWorking = False

circleStartTime = datetime.datetime.now()
queUpdater()

try:
	thread_arr = []
	for i in range(THREAD_AMOUNT):
		thread_arr.append(threading.Thread(target=doJob, name='Thd' + str(i+1), args=(que,'Thd[' + str(i+1) + ']')))
		thread_arr[i].daemon = True
	for i in range(THREAD_AMOUNT):
		thread_arr[i].start()
	thdA9 = threading.Thread(target=doJobA9, name='Thd9', args=())
	thdA9.daemon = True
	thdA9.start()
	while True:
		print ('[Update] Start query to update Extra Amount!')
		queryStartTime = datetime.datetime.now()
		queryCtr = 0
		for aDept in followedCourseDict:
			for serial in followedCourseDict[aDept]:
				if serial in newDataPool:
					balance = newDataPool[serial]["extra_amount"]
					while True:
						try:
							cursor.execute ("""
							 UPDATE course_new
							 SET `餘額`=%s
							 WHERE `選課序號`=%s
							""", (balance, serial))
						except Exception:
							print ('Error on exec [ {0} : {1} ]'.format(serial, balance))
							continue
						else:
							queryCtr += 1
							newDataPool.pop(serial, None)
							cnx.commit()
							break
		print ('[Update] Query Finish! Amount = {1}! Spending time = {0}!'.format(datetime.datetime.now()-queryStartTime, queryCtr))
		if not thdA9.is_alive():
			raise Exception('Thread Dead')
		for i in range(THREAD_AMOUNT):
			if not thread_arr[i].is_alive():
				raise Exception('Thread Dead')
		time.sleep(5)
except (KeyboardInterrupt, SystemExit):
	print ('\n!!! Received keyboard interrupt, quitting threads. !!!\n')
except:
	print (sys.exc_info())
	print ('\n!!! A thread dead, stop all. !!!\n')
finally:
	cursor.close()
	cnx.close()