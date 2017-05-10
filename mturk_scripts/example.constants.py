import redis
from peewee import *
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
import sys

r = redis.StrictRedis(host='localhost', port=6380, db=0, password = 'REDIS_PASSWORD_HERE') # TODO

ACCESS_ID = 'AMT_ACCESS_ID' # TODO
SECRET_KEY = 'AMT_SECRET_KEY' # TODO
HOST = 'mechanicalturk.amazonaws.com'
SANDBOX_HOST = 'mechanicalturk.sandbox.amazonaws.com'

def getConnection(is_prod = False):
    if is_prod:
        mtc = MTurkConnection(aws_access_key_id=ACCESS_ID,
                      aws_secret_access_key=SECRET_KEY,
                      host=HOST)
    else:
        mtc = MTurkConnection(aws_access_key_id=ACCESS_ID,
                      aws_secret_access_key=SECRET_KEY,
                      host=SANDBOX_HOST)

    print mtc.get_account_balance()
    return mtc


url = "https://ENTER_HIT_URL/" # TODO
title = "Live Q/A to Determine an Image"
description = "Ask or Answer questions about an image with a fellow Turker."
keywords = ["image", "chat", "question", "answer"]
frame_height = "1200"
amountToPay = 0.15
