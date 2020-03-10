import requests
import re

class AutoRetryRequest:
    session = requests.Session()
    cookies={
        "name":'PHPSESSID',
        "value":'435e04667cc3d0304f50ad7a77fc160e'
    }
    session.cookies.set(**cookies)
    default_options = {
        "timeout": 30
    }

    def __init__(self, req_name, retry_times = 3):
        self.reqName = req_name
        self.retryCtr = 0
        self.retryTimes = retry_times

    def get(self, url, set_options = {}):
        options = {**set_options, **AutoRetryRequest.default_options}
        def request():
            return AutoRetryRequest.session.get(url, **options)
        return self.autoRetry(request)

    def post(self, url, set_options = {}):
        options = {**set_options, **AutoRetryRequest.default_options}
        def request():
            return AutoRetryRequest.session.post(url, **options)
        return self.autoRetry(request)

    def autoRetry(self, request):
        while self.retryCtr < self.retryTimes:
            try:
                res = request()
                if not res.status_code == 200:
                    print ('[ERR] Unexpected error code while requests, Job({1}) Code : {0}!'.format(res.status_code, self.reqName))
                    continue
            except requests.Timeout as e:
                self.retryCtr += 1
                print ('[{0}] timeout!'.format(self.reqName))# str(datetime.datetime.now() - st)
                continue
            except (requests.ConnectionError, ConnectionResetError) as e:
                self.retryCtr += 1
                print ("[{0}] connection error".format(self.reqName))# :" + str(datetime.datetime.now() - st)
                continue
            except Exception as e:
                self.retryCtr += 1
                print ("\n!!! Unexpected error while requests !!!\n")
                continue
            else:
                res.close()
                res.encoding = "utf-8"
                if len(re.findall(r"(RobotCheck)", res.text)) is not 0:
                    raise Exception("超過流量，請到網站 https://course.ncku.edu.tw/index.php?c=qry_all 輸入驗證碼，再將 cookies 裡的 PHPSESSID 貼到 AutoRetryRequest")
                return res
        raise Exception("Retry Too Many Times")