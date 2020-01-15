import requests



class AutoRetryRequest:
    session = requests.Session()
    cookies={
        "name":'PHPSESSID',
        "value":'7146f90669566cdd9f4cb57dcbe6e4b1'
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
        while self.retryCtr < 3:
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
                return res
        raise Exception("Retry Too Many Times")