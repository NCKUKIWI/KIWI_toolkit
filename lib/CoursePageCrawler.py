import datetime
import re
import html
from bs4 import BeautifulSoup as bs

class CoursePageCrawler:
    def __init__(self, deptInfo, crawlerCtr):
        self.deptInfo = deptInfo
        self.crawlerCtr = crawlerCtr
    
    def do(self, threadID):
        st = datetime.datetime.now()
        process_name = "Thread #{0}|Crawler #{1}|Dept \"{2}\"".format(threadID, self.crawlerCtr, self.deptInfo['name'])
        autoRetryRequest = AutoRetryRequest(process_name)
        req_options_token = {'data': {'dept_no': self.deptInfo['code']}}
        res_token = autoRetryRequest.post("https://course.ncku.edu.tw/index.php?c=qry_all&m=result_init", req_options_token)
        token = res_token.json()['id']
        req_options_course = {'headers': {'referer': 'https://course.ncku.edu.tw/index.php?c=qry_all'}}
        res_course = autoRetryRequest.get("https://course.ncku.edu.tw/index.php?c=qry_all&m=result&i={0}".format(token), req_options_course)

        courseHtml = res_course.text
        css_class_invalid_tokens = re.findall(r"(\.\w{33})\s*\{\s*display:none;\s*\}",courseHtml)
        btfsClass = bs(courseHtml, "html5lib")
        for invalidToken in css_class_invalid_tokens:
            toDel = btfsClass.select(invalidToken)
            for tag in toDel:
                tag.decompose()
        rows = btfsClass.select("div#result tbody tr")
        courseList = []
        for aRow in rows:
            try:
                columns = aRow.select("td")
                course_serial = columns[1].select_one("div.dept_seq")
                course_serial_txt = course_serial.text.replace("-","").strip()
                course_name = columns[4].select_one(".course_name").text.strip()
                if course_serial_txt is "" or course_name is "":
                    continue
                course_numbers = columns[7].text.split("/")
                extra_amount = course_numbers[1].strip()
                description = ""
                cross_master = ""
                classroom = ""
                english = "N"
                expert = "否"
                moocs = "否"
                if columns[4].select_one("i.fa-file-text-o") is not None:
                    description = columns[4].select_one("i.fa-file-text-o").next_sibling.strip()
                if columns[4].select_one(".label-success") is not None:
                    cross_master = columns[4].select_one(".label-success").text.strip()
                if columns[4].select_one(".label-danger") is not None:
                    english = "Y"
                if columns[4].select_one(".label-warning") is not None:
                    moocs = "是"
                if columns[4].select_one(".label-info") is not None:
                    expert = "是"
                if columns[8].a is not None:
                    classroom = columns[8].a.text
                try:
                    extra_amount = int(extra_amount)
                except:
                    extra_amount= 0
                aCourse = {}
                aCourse['dept_name'] = columns[0].text.strip()
                aCourse['dept_code'] = self.deptInfo['code']
                aCourse['serial'] = course_serial_txt
                aCourse['course_code'] = course_serial.next_sibling.strip()[0:7]
                aCourse['class_code'] = course_serial.next_sibling.strip()[7:].replace("-","")
                aCourse['attribute_code'] = re.search(r"\[(\w*)\]", columns[1].text).group(1)
                aCourse['grade'] = columns[2].contents[0].strip()
                aCourse['class_type'] = columns[2].contents[2].strip()
                aCourse['group'] = columns[2].contents[4].strip()
                aCourse['type'] = columns[3].text.strip()
                aCourse['course_name'] = course_name
                aCourse['description'] = description
                aCourse['condition'] = columns[4].select_one(".cond").text.strip()
                aCourse['credit'] = float(columns[5].contents[0].strip())
                aCourse['subject_type'] = columns[5].contents[2].strip()
                aCourse['teacher'] = ", ".join(map(lambda ele: html.unescape(ele), filter(lambda ele: isinstance(ele, str), columns[6].contents)))
                aCourse['choosed_amount'] = int(course_numbers[0])
                aCourse['extra_amount'] = extra_amount
                aCourse['time'] = columns[8].contents[0].strip()
                aCourse['classroom'] = classroom
                aCourse['english'] = english
                aCourse['expert'] = expert
                aCourse['cross_master'] = cross_master
                aCourse['Moocs'] = moocs
                aCourse['admit'] = None
                for key in aCourse:
                    if (isinstance(aCourse[key], str)):
                        aCourse[key] = html.unescape(aCourse[key])
            except Exception as e:
                print(aRow)
                raise e
            else:
                courseList.append(aCourse)

        td = datetime.datetime.now() - st
        print('[{0}]:({1}) is done! Spending time = {2}!'.format(process_name, len(courseList), td))
        return courseList

if __name__ == '__main__':
    from AutoRetryRequest import AutoRetryRequest
    dept = {'code': 'A9', 'name': '通識中心 GE'}
    aCrawler = CoursePageCrawler(dept, 1)
    deptResult = aCrawler.do(0)
    print(deptResult)
else:
    from lib.AutoRetryRequest import AutoRetryRequest