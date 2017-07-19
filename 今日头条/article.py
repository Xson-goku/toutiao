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

reload(sys)
sys.setdefaultencoding('utf8')

class CollectData():
    """头条号文章列表获取
        单个头条号文章列表获取地址：
        http://www.toutiao.com/c/user/article/?page_type=1&user_id=5757425042&max_behot_time=0&count=20
        文章详情URL
        http://www.toutiao.com/i6436147811783279105/
        文章评论URL
        http://www.toutiao.com/api/comment/list/?group_id=6436136664733024513&item_id=6436147811783279105&offset=0&count=20
    """
    def __init__(self,user_id,collection,crawl_date):
        self.user_id = user_id
        self.collection = collection
        self.crawl_date= crawl_date #设置爬虫日期
        self.logger = logging.getLogger('main.CollectData') #初始化日志

    ##构建获取头条号文章搜索链接
    def getArticleListURL(self,max_behot_time):
        return 'http://www.toutiao.com/c/user/article/?page_type=1&user_id='+str(self.user_id)+'&max_behot_time='+str(max_behot_time)+'&count=20'
    
    ##构建获取头条号文章搜索链接
    def getArticleURL(self,article_id):
        return 'http://www.toutiao.com/i'+str(article_id)+'/'
    
    ##构建评论url,最多获取20条评论
    def getCommentsURL(self,group_id,article_id):
        return 'http://www.toutiao.com/api/comment/list/?group_id='+str(group_id)+'&item_id='+str(article_id)+'&offset=0&count=20'
  
    ##爬取文章列表
    def download(self,max_behot_time, maxTryNum=4):
        article_list_url = self.getArticleListURL(max_behot_time)
        print '-----article_list_url: '+article_list_url
        for tryNum in range(maxTryNum):
            try:
                resp = requests.get(article_list_url, headers=headers,timeout=3, verify=False)
            except:
                 if tryNum < (maxTryNum-1):
                    time.sleep(5)
                 else:
                    print 'Internet Connect Error!'
                    redis_db.Uids.store_err_uid(self.user_id)
                    return
        try:
            json_data = resp.json()
        except:
           print '---------------------------------数据请求异常'
           redis_db.Uids.store_err_uid(self.user_id)
           return
        ###TODO 限定7日时需修改
        over_flag = False
        has_more = json_data['has_more']
        data_list = json_data['data']
        max_behot_time = json_data['next']['max_behot_time']
        for article_data in data_list:
            article_genre = article_data['article_genre']
            article_id = article_data['item_id']
            comments_count = article_data['comments_count']
            result = redis_db.Article.store_article_id(article_id)
            print '--article_id:'+str(article_id)+',result:'+str(result)
            article_data['crawl_date'] = self.crawl_date
            ###文章需要进入文章详情页，爬取文章的详细内容，以及评论
            if article_genre == 'article' and result > 0:
                group_id,content = self.download_article_detail(article_id)
                article_data['article-content'] = content
                if group_id and comments_count > 0:
                    comments = self.download_comments(group_id, article_id)
                    article_data['comments'] = comments
            self.collection.insert(article_data)
        if over_flag:
            has_more = False
        return has_more,max_behot_time
    
    ##爬取文章详情
    def download_article_detail(self,article_id, maxTryNum=4):
        time.sleep(random.randint(5,10))
        article_url = self.getArticleURL(article_id)
        print '-----article_url: '+article_url
        for tryNum in range(maxTryNum):
            try:
                resp = requests.get(article_url, headers=headers,timeout=3, verify=False)
            except:
                 if tryNum < (maxTryNum-1):
                    time.sleep(5)
                    #proxies = common_utils.get_proxies()
                 else:
                    print 'Internet Connect Error!'
                    redis_db.Article.store_err_article_id(article_id)
                    return None,None
        try:
            res_data = resp.content.decode('utf-8')
            print res_data
            soup = BeautifulSoup(res_data,"html.parser")
            group_soup = soup.find('link',attrs={'rel':'alternate'})
            group_id = group_soup['href'][17:-1]
            content_soup = soup.find('div',class_='article-content')
            content = content_soup.text.strip()
        except:
            print '---------------------------------爬取文章详情异常,article_id:'+str(article_id)
            redis_db.Article.store_err_article_id(article_id)
            return None,None
        return group_id,content
    
    ##爬取评论数据
    def download_comments(self, group_id, article_id, maxTryNum=4):
        comments_url = self.getCommentsURL(group_id,article_id)
        print '-----comments_url: '+comments_url
        for tryNum in range(maxTryNum):
            try:
                resp = requests.get(comments_url, headers=headers,timeout=3, verify=False)
            except:
                 if tryNum < (maxTryNum-1):
                    time.sleep(5)
                    #proxies = common_utils.get_proxies()
                 else:
                    print 'Internet Connect Error!'
                    return
        try:
            json_data = resp.json()
            comments = json_data['data']['comments']
        except:
           print '---------------------------------评论数据请求异常,article_id:'+str(article_id)
           return None	
        return comments

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
    collection=db['article']
    cd = CollectData(5757425042,collection,str(datetime.date.today()))
    has_more,max_behot_time= cd.download(1491871200)
    while has_more and max_behot_time>1483200000:
        has_more,max_behot_time= cd.download(max_behot_time)
        time.sleep(random.randint(10,20))
if __name__ == '__main__':
    main()
