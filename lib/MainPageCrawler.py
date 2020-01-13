import datetime
import MySQLdb as mysql
import queue, time, threading
import sys
import requests
import json as jsonpkg
import re
from bs4 import BeautifulSoup as bs

class MainPageCrawler:
    def __init__(self):
        self.errCtr = 0

    def do(self, session):
        initStartTime = datetime.datetime.now()
        print ('[Init] Start!')
        while self.errCtr < 3:
            try:
                res = session.get("https://course.ncku.edu.tw/index.php?c=qry_all", timeout = 30)
                if not res.status_code == 200:
                    print ('[ERR] Unexpected error code while requests, Job(INIT) Code : {0}!'.format(res.status_code))
                    continue
                res.close()
                res.encoding = "utf-8"
            except requests.Timeout as e:
                self.errCtr += 1
                print ('[Init] timeout!')# str(datetime.datetime.now() - st)
                continue
            except (requests.ConnectionError, ConnectionResetError) as e:
                self.errCtr += 1
                print ("[Init] connection error")# :" + str(datetime.datetime.now() - st)
                continue
            except Exception as e:
                self.errCtr += 1
                print ("\n!!! Unexpected error while requests !!!\n")
                continue
            else:
                print ('[Init] Get Main Page succeed!')
                btfs = bs(res.text, "html5lib")
                deptList = []
                for dept in btfs.select('div.hidden-xs li.btn_dept'):
                    deptTxt = re.match(r"\(([A-Z0-9]{2})\)(.*)", dept.text)
                    deptDict = {
                        'code': deptTxt.group(1),
                        'name': deptTxt.group(2).strip()
                    }
                    deptList.append(deptDict)
                if len(deptList) == 0:
                    self.errCtr += 1
                    return self.do(session)
                print ('[Init] {0} depts! Spending Time = {1}'.format(len(deptList), datetime.datetime.now()-initStartTime))
                return deptList
                break
        raise Exception("Retry Too Many Times")
        

if __name__ == '__main__':
    session = requests.Session()
    cookies={
        "name":'PHPSESSID',
        "value":'7146f90669566cdd9f4cb57dcbe6e4b1'
    }
    session.cookies.set(**cookies)
    aCrawler = MainPageCrawler()
    result = aCrawler.do(session)
    # print(result)