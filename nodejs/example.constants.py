import redis
from peewee import *
from boto.mturk.connection import MTurkConnection
from boto.mturk.question import ExternalQuestion
import sys

client = redis.StrictRedis(host='localhost', port=6380, db=0, password = "REDIS_PASSWORD_HERE")

ACCESS_ID = 'AMT_ACCESS_ID' # TODO
SECRET_KEY = 'AMT_SECRET_KEY' # TODO
HOST = 'mechanicalturk.sandbox.amazonaws.com'

REDIS_LIST = "v20q_queue"

root = '/path/to/v20q/nodejs/' #TODO

mtc = MTurkConnection(aws_access_key_id=ACCESS_ID,
                      aws_secret_access_key=SECRET_KEY,
                      host=HOST)

url = "https://godel.ece.vt.edu/v20q_chat"
title = "Live Q/A about to Determine an Image"
description = "Ask or Answer questions about an image with a fellow Turker."
keywords = ["image", "chat", "question", "answer"]
frame_height = "1200"
amount = 0.15

form = ExternalQuestion(url, frame_height)

QUES_HITS_FILE = 'amthitsQues.csv'
ANS_HITS_FILE = 'amthitsAns.csv'
QUES_REJECTS_FILE = 'amthitsReviewRejectQues.csv'
ANS_REJECTS_FILE = 'amthitsReviewRejectAns.csv'
