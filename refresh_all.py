# coding: utf-8
# brew install mysql-connector-c
	# https://github.com/PyMySQL/mysqlclient-python
	# modify the mysql_config and pip3 install it.

import datetime
import MySQLdb as mysql
import queue, time, threading
import sys
import json as jsonpkg

from lib.MainPageCrawler import MainPageCrawler
from lib.CoursePageCrawler import CoursePageCrawler

# Modify thread amount here
thread_amount = 4

db_config = {}
with open( 'config.crawler.json') as f:
	db_config = jsonpkg.load(f)['db_py']

que = queue.Queue()
allCourseList = []
waiting = []
circleStartTime = 0
queStartTime = 0
queUpdaterWorking = False

def getNewJobFromQueue(*args):
	global queUpdaterWorking
	global allCourseList
	global waiting
	queue = args[0]
	threadID = args[1]
	waitingID = args[2]
	while True:
		if queue.qsize() == 0:
			waiting[waitingID] = True
			if (not False in waiting) and (not queUpdaterWorking):
				queUpdaterWorking = True
				# print(allCourseList)
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
			coursePageCrawler = que.get()
			newCourseList = coursePageCrawler.do(threadID)
			allCourseList += newCourseList
			waiting[waitingID] = False

def queUpdater():
	global circleStartTime
	global queStartTime
	circleStartTime = datetime.datetime.now()
	deptList = MainPageCrawler().do()
	crawlerCtr = 1
	queStartTime = datetime.datetime.now()
	for dept in deptList:
		# if num >= 4: break
		# print (dept)
		que.put(CoursePageCrawler(dept, crawlerCtr))
		crawlerCtr += 1
	print ("[Queueing] Queue size = {0}...!".format(que.qsize()))
	
def dbUpdater():
	global allCourseList
	localAllCourseList = allCourseList
	allCourseList = []
	closedCourseIdList = []
	followedList = []
	tmpOriCourses = {}
	gotErr = False
	logOutput = ""
	
	global cnx
	global cursor
	cnx = mysql.connect(**db_config)
	cursor = cnx.cursor(mysql.cursors.DictCursor)

	print ('[Selecter] Start Select! Select Size = {0}'.format(len(localAllCourseList)))
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
	for aCourse in localAllCourseList:
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
	for aCourse in localAllCourseList:
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
				`選必修`,`學分`,`老師`,`已選課人數`,`餘額`,`時間`,`教室`,`備註`,`限選條件`,`業界參與`,`屬性碼`,`跨領域學分學程`,`Moocs`,`admit`,`updateTime`)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
				""", (aCourse['dept_name'], aCourse['dept_code'], aCourse['serial'], aCourse['course_code'], aCourse['class_code'],
				aCourse['class_type'], aCourse['grade'], aCourse['type'], aCourse['group'], aCourse['english'], aCourse['course_name'],
				aCourse['subject_type'], float(aCourse['credit']), aCourse['teacher'], int(aCourse['choosed_amount']), aCourse['extra_amount'],
				aCourse['time'], aCourse['classroom'], aCourse['description'], aCourse['condition'], aCourse['expert'],
				aCourse['attribute_code'], aCourse['cross_master'], aCourse['Moocs'], aCourse['admit'], datetime.datetime.utcnow()))
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

		# Comment Below to delete old courses
		# -----------------------------------
		if len(closedCourseIdList) >= 10:
			logOutput += "[ERR] |" + datetime.datetime.today().isoformat() + "| !!! Unexpected [" + str(len(closedCourseIdList)) + "] Closed Course !!!\n"
		elif len(closedCourseIdList) > 0:
		# -----------------------------------

		# Comment Below for general using
		# -----------------------------------
		# if(True):
		# -----------------------------------

			logOutput += tmpLog
			print ('[Delete] Start Clean non-update! Amount: {0}'.format(len(closedCourseIdList)))
			startTime = datetime.datetime.now()
			closedCourseIdTxt = ",".join(closedCourseIdList)
			try:
				query = "DELETE FROM course_new WHERE id IN ({0});".format(closedCourseIdTxt)
				cursor.execute(query)
			except Exception as e:
				print ("error on exec DELETE non-update: {1}".format(e))
			cnx.commit()
			print ('[Delete] Finish Clean non-update! Spending time = {0}!'.format(datetime.datetime.now()-startTime))

			print ('[ModFollow] Start Modify Follow! Amount: {0}'.format(len(closedCourseIdList)))
			startTime = datetime.datetime.now()
			try:
				query = "UPDATE follow SET course_id=-1 WHERE course_id IN ({0});".format(closedCourseIdTxt)
				cursor.execute(query)
			except Exception as e:
				print ("error on exec UPDATE closedCourse Follow: {1}".format(e))
			cnx.commit()
			print ('[ModFollow] Finish Modify Follow! Spending time = {0}!'.format(datetime.datetime.now()-startTime))

	cursor.close()
	cnx.close()
	with open('devLog', 'a') as f:
		f.write(logOutput)

queUpdater()
for i in range(thread_amount):
	waiting.append(False)

try:
	thread_arr = []
	for i in range(thread_amount):
		threadID = i + 1
		thread_arr.append(threading.Thread(target=getNewJobFromQueue, name='Thd' + str(threadID), args=(que, threadID, i)))
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