
# coding: utf-8

import datetime
import MySQLdb as mysql
import queue, time, threading
import sys
import requests
import json as jsonpkg
from bs4 import BeautifulSoup as bs

# Modify thread amount here
thread_amount = 2

class Job:
	def __init__(self, name, dept, crawlerCtr):
		self.name = name
		self.dept = dept
		self.crawlerCtr = crawlerCtr
	def do(self, thisThdName):
		while True:
			st = datetime.datetime.now()
			try:
				resForClass = requests.get("http://course-query.acad.ncku.edu.tw/qry/" + self.dept['url'], timeout = 30)
				if not resForClass.status_code == 200:
					print ('[ERR] Unexpected error code while requests, Job({0}) Code : {1}!'.format(self.name, resForClass.status_code))
					continue
				resForClass.close()
				resForClass.encoding = "utf-8"
			except (requests.Timeout, TimeoutError) as e:
				print ('[Crawler] {0} timeout on {1}!'.format(self.name, thisThdName))# str(datetime.datetime.now() - st)
				continue
			except (requests.ConnectionError, ConnectionResetError) as e:
				print ("[Crawler] " + self.name + " error")# :" + str(datetime.datetime.now() - st)
				continue
			except Exception as e:
				print ("\n!!! Unexpected error while requests !!!\n")
				continue
			else:
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
				# 輸出至JSON
				lastKeyTmp ={}
				for classindex, classinfo in enumerate(bodys):
					keyTmp = {}
					for index, data in enumerate(classinfo):
						if data == u'查無課程資訊': break
						if heads[index] == 'dept_name':
							keyTmp[heads[index]] = data.strip().replace(' ', '')
						else:
							keyTmp[heads[index]] = data.strip()
					if 'serial' in keyTmp:
						try:
							keyTmp['course_name'].replace(',','、')
							if keyTmp['dept_name'] == "":
								keyTmp['dept_name'] = lastKeyTmp['dept_name']
							if keyTmp['dept_code'] == "":
								keyTmp['dept_code'] = lastKeyTmp['dept_code']
							if keyTmp['credit'] == "":
								keyTmp['credit'] = '0'
						except KeyError as e:
							logOutput = '[KeyERR] |' + datetime.datetime.today().isoformat() + '| ' + self.name + ": " + jsonpkg.dumps(keyTmp, ensure_ascii=False) + ' | ' + jsonpkg.dumps(lastKeyTmp, ensure_ascii=False) + '\n'
							with open('devLog', 'a') as f:
								f.write(logOutput)
							raise e
						try:
							int(keyTmp['extra_amount'])
						except ValueError as e:
							keyTmp['extra_amount'] = '0'
						if not keyTmp['serial'] == "":
							keyTmp['serial'] = keyTmp['dept_code'] + keyTmp['serial']
					if not keyTmp == {}:
						lastKeyTmp = keyTmp
						classARR.append(keyTmp)
				td = datetime.datetime.now() - st
				print ('[Crawler #{3}] Job({0}) is done by {2}! Spending time = {1}!'.format(self.name, td, thisThdName, self.crawlerCtr))
				break

def initer():
	initStartTime = datetime.datetime.now()
	print ('[Init] Start!')
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
	print ('[Init] Get Main Page succeed!')
	btfs = bs(res.text, "html.parser")
	jsonLink = {}
	for classes in btfs.select('div .dept'):
		for a in classes.find_all('a', href = True):
			textTmp = a.text
			jsonLink[textTmp[3:5]] = {
				'url':a['href'], 'name':textTmp.replace(u"）", ")").replace(" ","")
			}
	for classes in btfs.select('div .institute'):
		for a in classes.find_all('a', href = True):
			textTmp = a.text
			jsonLink[textTmp[3:5]] = {
				'url':a['href'], 'name':textTmp.replace(u"）", ")").replace(" ","")
			}
	if len(jsonLink) == 0:
		return initer()
	print ('[Init] {0} depts! Spending Time = {1}'.format(len(jsonLink), datetime.datetime.now()-initStartTime))
	return jsonLink

def queUpdater():
	global circleStartTime
	global queStartTime
	circleStartTime = datetime.datetime.now()
	jsonLink = initer()
	crawlerCtr = 1
	queStartTime = datetime.datetime.now()
	for num, dept in enumerate(jsonLink):
		# if num >= 4: break
		# print (dept)
		que.put(Job(dept, jsonLink[dept], crawlerCtr))
		crawlerCtr += 1
	print ("[Queueing] Queue size = {0}...!".format(que.qsize()))

def dbUpdater():
	global classARR
	localClassARR = classARR
	classARR = []
	closedCourseIdList = []
	followedList = []
	tmpOriCourses = {}
	gotErr = False
	logOutput = ""
	
	global cnx
	global cursor
	cnx = mysql.connect(**db_config)
	cursor = cnx.cursor(mysql.cursors.DictCursor)

	print ('[Selecter] Start Select! Select Size = {0}'.format(len(localClassARR)))
	startTime = datetime.datetime.utcnow()
	errCtr = 0
	while True:
		if errCtr < 5:
			try:
				cursor.execute(""" SELECT * FROM course_new; """)
			except Exception as e:
				print ("error on exec SELECT ori_course : {0}".format(e))
				errCtr += 1
				continue
			else:
				for row in cursor:
					tmpKey = row['系號'] + '-' + row['選課序號']  + '-' + row['課程碼'] + '-' + row['分班碼'] + '-' + row['組別'] + '-' + row['類別'] + '-' + row['班別']
					tmpOriCourses[tmpKey] = row['id']
				break
		else:
			raise Exception("Retry Too Many Times")
	for aCourse in localClassARR:
		tmpKey = aCourse['dept_code'] + '-' + aCourse['serial']  + '-' + aCourse['course_code'] + '-' + aCourse['class_code'] + '-' + aCourse['group'] + '-' + aCourse['type'] + '-' + aCourse['class_type']
		aCourse['id'] = tmpOriCourses.get(tmpKey, -1)
		if aCourse['id'] == -1:
			logOutput += '[NEW] |' + datetime.datetime.today().isoformat() + '| ' + tmpKey + '\n'
	print ('[Selecter] Finish Select! Spending time = {0}!'.format(datetime.datetime.utcnow()-startTime))

	print ('[Selecter] Start Getting Followed List!')
	startTime = datetime.datetime.utcnow()
	errCtr = 0
	while True:
		if errCtr < 5:
			try:
				cursor.execute("SELECT * FROM follow;")
			except Exception as e:
				print ("error on exec SELECT follow list : {0}".format(e))
				errCtr += 1
				continue
			else:
				for row in cursor:
					if row['hadNotify'] == 0 and not row['course_id'] == -1:
						followedList.append(row['serial'])
				break
		else:
			raise Exception("Retry Too Many Times")
	print ('[Selecter] Finish Select! Spending time = {0}!'.format(datetime.datetime.utcnow()-startTime))

	print ('[Updater] Start Update and Insert!')
	timeStamp = datetime.datetime.utcnow()
	for aCourse in localClassARR:
		if not aCourse['id'] == -1:
			if aCourse['serial'] in followedList:
				try:
					cursor.execute("""
					UPDATE course_new
					SET `英語授課`=%s, `學分`=%s, `老師`=%s, `已選課人數`=%s, `時間`=%s, `教室`=%s, `備註`=%s, `限選條件`=%s, 
					`業界參與`=%s, `屬性碼`=%s, `跨領域學分學程`=%s, `Moocs`=%s, `updateTime`=%s WHERE `id`=%s;
					""", (aCourse['english'], float(aCourse['credit']), aCourse['teacher'], int(aCourse['choosed_amount']),
					aCourse['time'], aCourse['classroom'], aCourse['description'], aCourse['condition'], aCourse['expert'],
					aCourse['attribute_code'], aCourse['cross_master'], aCourse['Moocs'], datetime.datetime.utcnow(), aCourse['id']))
				except Exception as e:
					print ("error on exec UPDATE [ {0} ] : {1}".format(aCourse, e))
					gotErr = True
			else:
				try:
					cursor.execute("""
					UPDATE course_new
					SET `英語授課`=%s, `學分`=%s, `老師`=%s, `已選課人數`=%s, `餘額`=%s, `時間`=%s, `教室`=%s, 
					`備註`=%s, `限選條件`=%s, `業界參與`=%s, `屬性碼`=%s, `跨領域學分學程`=%s, `Moocs`=%s, `updateTime`=%s
					WHERE `id`=%s;
					""", (aCourse['english'], float(aCourse['credit']), aCourse['teacher'], int(aCourse['choosed_amount']),
					aCourse['extra_amount'], aCourse['time'], aCourse['classroom'], aCourse['description'],
					aCourse['condition'], aCourse['expert'], aCourse['attribute_code'], aCourse['cross_master'],
					aCourse['Moocs'], datetime.datetime.utcnow(), aCourse['id']))
				except Exception as e:
					print ("error on exec UPDATE [ {0} ] : {1}".format(aCourse, e))
					gotErr = True
		else:
			try:
				cursor.execute("""
				INSERT INTO course_new (`系所名稱`,`系號`,`選課序號`,`課程碼`,`分班碼`,`班別`,`年級`,`類別`,`組別`,`英語授課`,`課程名稱`,
				`選必修`,`學分`,`老師`,`已選課人數`,`餘額`,`時間`,`教室`,`備註`,`限選條件`,`業界參與`,`屬性碼`,`跨領域學分學程`,`Moocs`,`updateTime`)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
				""", (aCourse['dept_name'], aCourse['dept_code'], aCourse['serial'], aCourse['course_code'], aCourse['class_code'],
				aCourse['class_type'], aCourse['grade'], aCourse['type'], aCourse['group'], aCourse['english'], aCourse['course_name'],
				aCourse['subject_type'], float(aCourse['credit']), aCourse['teacher'], int(aCourse['choosed_amount']), aCourse['extra_amount'],
				aCourse['time'], aCourse['classroom'], aCourse['description'], aCourse['condition'], aCourse['expert'],
				aCourse['attribute_code'], aCourse['cross_master'], aCourse['Moocs'], datetime.datetime.utcnow()))
			except Exception as e:
				print ("error on exec INSERT [ {0} ] : {1}".format(aCourse, e))
	cnx.commit()
	print ('[Updater] Finish Update and Insert! Spending time = {0}!'.format(datetime.datetime.utcnow()-timeStamp))
	
	if not gotErr:
		print ('[Select] Start Select non-update!')
		startTime = datetime.datetime.now()
		try:
			query = "SELECT * FROM course_new WHERE `updateTime` < '{0}';".format(timeStamp)
			cursor.execute(query)
		except Exception as e:
			print ("error on exec SELECT non-update : {0}".format(e))
		else:
			tmpLog = ""
			for row in cursor:
				closedCourseIdList.append(row['id'])
				tmpKey = str(row['id']) + '-' + row['系號'] + '-' + row['課程碼'] + '-' + row['分班碼'] + '-' + row['組別'] + '-' + row['類別'] + '-' + row['班別']
				tmpLog += '[OLD] |' + datetime.datetime.today().isoformat() + '| '  + tmpKey + '\n'
		print ('[Select] Finish Select non-update! Spending time = {0}!'.format(datetime.datetime.now()-startTime))
		
		if len(closedCourseIdList) >= 10:
			logOutput += "[ERR] |" + datetime.datetime.today().isoformat() + "| !!! Unexpected [" + str(len(closedCourseIdList)) + "] Closed Course !!!\n"
		elif len(closedCourseIdList) > 0:
			logOutput += tmpLog
			print ('[Delete] Start Clean non-update! Amount: {0}'.format(len(closedCourseIdList)))
			startTime = datetime.datetime.now()
			for aCourse in closedCourseIdList:
				try:
					query = "DELETE FROM course_new WHERE id = {0};".format(aCourse)
					cursor.execute(query)
				except Exception as e:
					print ("error on exec DELETE non-update [ {0} ] : {1}".format(aCourse, e))
				else:
					print ("[Delete] Course Close [ {0} ]".format(aCourse))
			cnx.commit()
			print ('[Delete] Finish Clean non-update! Spending time = {0}!'.format(datetime.datetime.now()-startTime))

			print ('[ModFollow] Start Modify Follow! Amount: {0}'.format(len(closedCourseIdList)))
			startTime = datetime.datetime.now()
			for aCourse in closedCourseIdList:
				try:
					query = "UPDATE follow SET course_id=-1 WHERE course_id={0};".format(aCourse)
					cursor.execute(query)
				except Exception as e:
					print ("error on exec UPDATE closedCourse Follow [ {0} ] : {1}".format(aCourse, e))
			cnx.commit()
			print ('[ModFollow] Finish Modify Follow! Spending time = {0}!'.format(datetime.datetime.now()-startTime))

	cursor.close()
	cnx.close()
	with open('devLog', 'a') as f:
		f.write(logOutput)

def doJob(*args):
	global queUpdaterWorking
	global waiting
	queue = args[0]
	thdName = args[1]
	waitingID = args[2]
	while True:
		if queue.qsize() == 0:
			waiting[waitingID] = True
			if (not False in waiting) and (not queUpdaterWorking):
				queUpdaterWorking = True
				global circleStartTime
				global queStartTime
				print ('[Queueing] Done que! Spending time = {0}!'.format(datetime.datetime.now()-queStartTime))
				dbUpdater()
				print ('[ALL] Done all! Spending time = {0}!'.format(datetime.datetime.now()-circleStartTime))
				queUpdater()
				queUpdaterWorking = False
			else:
				time.sleep(5)
		if queue.qsize() > 0:
			job = que.get()
			job.do(thdName)
			waiting[waitingID] = False

heads = ['dept_name', 'dept_code', 'serial', 'course_code', 'class_code', 'class_type',
'grade', 'type', 'group', 'english', 'course_name', 'subject_type', 'credit', 'teacher', 
'choosed_amount', 'extra_amount', 'time', 'classroom', 'description', 'condition',
'expert', 'attribute_code', 'cross_master', 'Moocs']

db_config = {}

with open( 'config.crawler.json') as f:
	db_config = jsonpkg.load(f)['db_py']

que = queue.Queue()
classARR = []
waiting = []
circleStartTime = 0
queStartTime = 0
queUpdaterWorking = False
queUpdater()
for i in range(thread_amount):
	waiting.append(False)

try:
	thread_arr = []
	for i in range(thread_amount):
		thread_arr.append(threading.Thread(target=doJob, name='Thd' + str(i+1), args=(que,'Thd[' + str(i+1) + ']', i)))
		thread_arr[i].daemon = True
	for i in range(thread_amount):
		thread_arr[i].start()
	while True:
		for i in range(thread_amount):
			if not thread_arr[i].is_alive():
				raise Exception('Thread Dead')
		time.sleep(10)
except (KeyboardInterrupt, SystemExit):
	print ('\n!!! Received keyboard interrupt, quitting threads. !!!\n')
except:
	print (sys.exc_info())
	print ('\n!!! A thread dead, stop all. !!!\n')
else:
	cursor.close()
	cnx.close()