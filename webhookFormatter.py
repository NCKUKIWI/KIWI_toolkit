import sys
import cgi, json
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from urllib import parse

class HandlerClass(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        post_values = self.rfile.read(length)

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        decodedStr = post_values.decode()
        decodedDict = dict(parse.parse_qsl(decodedStr))
        bodyTxt = '[【{Name}】]({URL}) 狀態回報'.format(**decodedDict)
        del(decodedDict['Name'], decodedDict['URL'])
        connectInfoList = [{"title":k, "description": v} for k, v in decodedDict.items()]

        reqBody = {
            'body' : bodyTxt,
            "connectColor" : "#FAC11B", 
            "connectInfo" : connectInfoList
        }
        headers = {
            'Accept':'application/vnd.tosslab.jandi-v2+json',
            'Content-Type': 'application/json'
        }
        req = requests.post("https://wh.jandi.com/connect-api/webhook/15387725/9c62586f3f79fc3d36b123d4463bea98", json = reqBody, headers=headers)

httpd = HTTPServer(('localhost', 3030), HandlerClass)

sa = httpd.socket.getsockname()
print ("Serving HTTP on", sa[0], "port", sa[1], "...")
httpd.serve_forever()