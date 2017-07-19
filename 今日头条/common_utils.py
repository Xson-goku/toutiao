# -*- coding: utf-8 -*-
import requests
import json
import urllib
import random
import socket
import time

###发送短信
def send_messag(mobile,content):
    resp = requests.post("http://sms-api.luosimao.com/v1/send.json",
                          auth=("api", "cd810819350051c73bf0aa0cf4d7a419"),
                          data={
	                           "mobile": mobile,
	                           "message": content + ",【6M】"
                                },timeout=3 , verify=False)
    status_resp = requests.get( "http://sms-api.luosimao.com/v1/status.json" ,
                         auth=("api", "cd810819350051c73bf0aa0cf4d7a419"),
                         timeout=5 , 
                         verify=False );
    result =  json.loads( resp.content )
    status_result = json.loads( status_resp.content )
    print 'send message for'+ mobile + ",result is:" + str(result)
    print 'account status is'+str(status_result)

###获取代理
def get_proxies():
    # 获取IP的API接口
    apiUrl = "http://api.ip.data5u.com/dynamic/get.html?order=5ebf055c7424fcb4ed5a6f2ffdef7b87"
    # 获取IP列表
    res = urllib.urlopen(apiUrl).read().strip("\n");
    # 按照\n分割获取到的IP
    ips = res.split("\n");
    while len(str(ips))>25:
        print ips
        time.sleep(3)
        print 'get proxies encountered one problems'
        res = urllib.urlopen(apiUrl).read().strip("\n");
        # 按照\n分割获取到的IP
        ips = res.split("\n");
    # 随机选择一个IP
    proxyip = random.choice(ips)
    proxies = {"http": "http://"+proxyip,"https": "http://"+proxyip}
    return proxies

###获取运行主机hostname
def get_hostname():
    hostname = socket.getfqdn(socket.gethostname(  ))
    print 'hostname:'+ str(hostname)
    return str(hostname)

##获取休眠时间
def get_sleep_time():
    current_time = int(time.strftime('%H',time.localtime(time.time())))
    intterval = random.randint(5,15)
    if current_time >0 and  current_time < 7 :
        intterval = random.randint(25,40)
    elif current_time >=7 and  current_time < 17:
        intterval = random.randint(10,25)
    return intterval
if __name__ == '__main__':
    send_messag('18561906132','test why no message')
