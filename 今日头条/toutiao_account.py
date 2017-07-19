# coding: utf-8

__version__ = '1.1.0'
__author__ = 'chenmin (1019717007@qq.com)'

'''
以关键词收集新浪微博
'''
from bs4 import BeautifulSoup
import json
import time
import datetime
import random
import logging
import sys
import redis_db
from headers import headers
import pymongo
import requests
import common_utils
from urllib import quote

reload(sys)
sys.setdefaultencoding('utf8')

class CollectData():
    """单条微博及用户信息收集类

        大体思路：利用微博API获取单条微博内容、评论数、点赞数、转发数、第一页评论、作者信息等内容

        单条微博内容获取地址：https://m.weibo.cn/status/4110221791827771
        http://www.toutiao.com/search_content/?offset=0&format=json&keyword=海&autoload=true&count=20&cur_tab=4
    """
    def __init__(self,keyword,collection,crawl_date):
        self.keyword = keyword
        self.collection = collection
        self.crawl_date= crawl_date #设置爬虫日期
        self.logger = logging.getLogger('main.CollectData') #初始化日志

    ##构建获取头条号用户搜索链接
    def getUserURL(self,num):
        return 'http://www.toutiao.com/search_content/?offset='+str(num)+'&format=json&keyword='+quote(self.keyword)+'&autoload=true&count=20&cur_tab=4'
    ##爬取具体数据
    def download(self,num, maxTryNum=4):
        user_url = self.getUserURL(num)
        print '-----user_url: '+user_url
        for tryNum in range(maxTryNum):
            try:
                resp = requests.get(user_url, headers=headers,timeout=3, verify=False)
            except:
                 if tryNum < (maxTryNum-1):
                    time.sleep(5)
                    #proxies = common_utils.get_proxies()
                 else:
                    print 'Internet Connect Error!'
                    redis_db.Keywords.store_keyword(self.keyword)
                    ###########增加短信验证码
                    ###hostname = common_utils.get_hostname()
                    ###message_content = 'url:'+str(weibo_url)
                    ###common_utils.send_messag("18561906132",message_content)
                    ##print "I'll sleep 30s..."
                    ###time.sleep(30)
                    return
        try:
            json_data = resp.json()
            #print json_data
        except:
           print '---------------------------------数据请求异常'
           redis_db.Keywords.store_keyword(self.keyword)
           time.sleep(10)
           return
        return_count = json_data['return_count']
        has_more = json_data['has_more']
        ###return_count 返回条数
        if return_count>0:
            user_list = json_data['data']
            for toutiao_user in user_list:
                is_pgc = toutiao_user['is_pgc']
                ###is_pac=1，代表此用户为头条号
                if is_pgc == 1:
                    user_id = toutiao_user['id']
                    j = redis_db.Uids.store_uid(user_id)
                    print '----------j:'+str(j)
                    ###数据插入成功，代表是新的头条号
                    if j == 1:
                        toutiao_user['_id'] = user_id
                        print '--------user_id:' + str(user_id)
                        toutiao_user['crawl_date']=self.crawl_date
                        self.collection.save(toutiao_user)
        return has_more

#####准备爬虫
def crawlData(set_name,collection):
    mid_keys = redis_db.Mids.fetch_mid(set_name)
    if mid_keys is not None:
       crawlDate = str(datetime.date.today()) 
       brand_id = mid_keys[0]
       mid = mid_keys[1]
       ##实例化收集类，收集指定关键字和起始时间的微博
       cd = CollectData(brand_id,mid,collection,crawlDate)
       cd.download()
def main():
    logger = logging.getLogger('main')
    logFile = './run_collect.log'
    logger.setLevel(logging.DEBUG)
    filehandler = logging.FileHandler(logFile)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)
    client = pymongo.MongoClient("139.129.222.132", 27017)
    db=client['toutiao_db']
    collection=db['account']
    fo = open('keywords.txt')
    keyword_str = fo.read()
    keyword_list = keyword_str.split('\n')
    print len(keyword_list)
    for key_word in keyword_list:
        print '----------key_word:'+key_word
        has_more = 1
        i = 0
        while has_more == 1:
            cd = CollectData(key_word.strip(),collection,str(datetime.date.today()))
            has_more = cd.download(i*20)
            i = i +1
            time.sleep(random.randint(10,20))
if __name__ == '__main__':
    main()
