import datetime
import re
from bs4 import BeautifulSoup as bs

ProcessName = "Init"

class MainPageCrawler:
    def __init__(self):
        self.errCtr = 0

    def do(self):
        initStartTime = datetime.datetime.now()
        print ('[{0}] Start!'.format(ProcessName))
        autoRetryRequest = AutoRetryRequest(ProcessName)
        res = autoRetryRequest.get("https://course.ncku.edu.tw/index.php?c=qry_all")
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
            return self.do()
        print ('[{0}] {1} depts! Spending Time = {2}'.format(ProcessName, len(deptList), datetime.datetime.now()-initStartTime))
        return deptList
        
if __name__ == '__main__':
    from AutoRetryRequest import AutoRetryRequest
    aCrawler = MainPageCrawler()
    result = aCrawler.do()
    print(result)
else:
    from lib.AutoRetryRequest import AutoRetryRequest