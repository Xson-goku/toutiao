# coding:utf-8
import datetime
import json
import redis
import time
from config.conf import get_redis_args
import common_utils

redis_args = get_redis_args()

class Keywords(object):
    rd_con = redis.StrictRedis(host=redis_args.get('host'), port=redis_args.get('port'),
                               password=redis_args.get('password'), db=redis_args.get('urls'))
    ###存储关键词和brand_id
    @classmethod
    def store_keyword(cls, keyword):
        cls.rd_con.sadd('tt:keywords', keyword)
	###获取一个关键词
    @classmethod
    def fetch_keyword(cls,set_name):
        keyword = cls.rd_con.spop(set_name)
        return keyword

class Uids(object):
    rd_con = redis.StrictRedis(host=redis_args.get('host'), port=redis_args.get('port'),
                               password=redis_args.get('password'), db=redis_args.get('urls'))
    ###存储user_id
    @classmethod
    def store_uid(cls, user_id):
        return cls.rd_con.sadd('tt:uids', user_id)
def main():
    cd = Key_words()
    cd.move_keyword()
if __name__ == '__main__':
    main()
