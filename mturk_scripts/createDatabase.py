import MySQLdb as mdb
import datetime
import sys
import os
from peewee import *
import glob
from collections import defaultdict
import json
import shortuuid
import random
from datetime import datetime

import PIL
from PIL import Image
from PIL import ImageFilter
from os import listdir
from os.path import isfile, join
from shutil import copyfile
import numpy

config = json.load(open('config.json', 'r'))

con = mdb.connect(host="localhost", user=config['db_user'], db=config['db_name'], passwd=config['db_pass'])
database = MySQLDatabase(config['db_name'], user=config['db_user'], password=config['db_pass'])
class BaseModel(Model):
    class Meta:
        database=database

class Image(BaseModel):
    imageId = CharField(primary_key=True, index=True)
    imageName = CharField()
    imageType = CharField()
    imageSubType = CharField()
    numHitsFinished = CharField()

class AMTHits(BaseModel):
    id = CharField(primary_key=True)
    socketId = CharField()
    assignmentId = CharField()
    workerId = CharField()
    approve = CharField(default='notApprove')
    hitId = CharField()
    status = CharField()
    isPaid = BooleanField(default='0')
    bonus = IntegerField(default=0)
    hitIden = CharField()
    comment = CharField()
    image = ForeignKeyField(Image)
    guess = IntegerField(default=-1)
    created_at = IntegerField(default=int(datetime.now().strftime('%s')))
    completed_at = IntegerField(default=0)

class Feedback(BaseModel):
    workerId = CharField()
    hitId = CharField()
    assignmentId = CharField()
    sequenceId = CharField()
    feedback = TextField()

class Question(BaseModel):
    id = CharField(primary_key=True, index=True)
    question = CharField()
    image = ForeignKeyField(Image)
    annotationId = ForeignKeyField(AMTHits)
    sequenceId = CharField()
    socketId = CharField()
    sourceId = CharField()
    destId = CharField()
    created_at = IntegerField(default=int(datetime.now().strftime('%s')))

class Answer(BaseModel):
    id = CharField(primary_key=True, index=True)
    answer = CharField()
    question = ForeignKeyField(Question)
    image = ForeignKeyField(Image)
    annotationId = ForeignKeyField(AMTHits)
    sequenceId = CharField()
    socketId = CharField()
    sourceId = CharField()
    destId = CharField()
    created_at = IntegerField(default=int(datetime.now().strftime('%s')))

class ImagePool(BaseModel):
    id = CharField(primary_key=True)
    assignmentId = CharField()
    image = ForeignKeyField(Image)

class ObjectPool(BaseModel):
    id = CharField(primary_key=True)
    objectName = CharField()
    image = ForeignKeyField(Image)


def createDatabaseTables():
    database.connect()

    if False:
        if Image.table_exists():
            database.drop_table(Image)
        if Caption.table_exists():
            database.drop_table(Caption)
        if AMTHits.table_exists():
            database.drop_table(AMTHits)
        if Feedback.table_exists():
            database.drop_table(Feedback)
        if Question.table_exists():
            database.drop_table(Question)
        if Answer.table_exists():
            database.drop_table(Answer)
        if ImagePool.table_exists():
            database.drop_table(ImagePool)
        if ObjectPool.table_exists():
            database.drop_table(ObjectPool)

    if not Image.table_exists():
        database.create_table(Image)
    if not AMTHits.table_exists():
        database.create_table(AMTHits)
    if not Feedback.table_exists():
        database.create_table(Feedback)
    if not Question.table_exists():
        database.create_table(Question)
    if not Answer.table_exists():
        database.create_table(Answer)
    if not ImagePool.table_exists():
        database.create_table(ImagePool)
    if not ObjectPool.table_exists():
        database.create_table(ObjectPool)
    print "All database tables created."

def fillPilotData():

    split = 'train2014' # TODO
    print 'Loading objects ' + split + ' data...'

    cocoPath = '/path/to/visdial-amt-chat/nodejs/static/dataset/' # TODO
    objectsPath = '/path/to/visdial-amt-chat/nodejs/static/annotations/' # TODO

    f = open(os.path.join(objectsPath, 'instances_' + split + '.json'))
    objectData = json.loads(f.read())
    f.close()
    imdir='COCO_%s_%012d.jpg'
    subtype = split

    image_path = cocoPath + subtype + '/'
    image_list = glob.glob(image_path + '*.jpg')

    query = "SELECT * FROM image WHERE imageSubType = '" + split + "'"
    print(query)

    with con:
        cur = con.cursor()
        cur.execute(query)

        c = 0
        for i in range(cur.rowcount):
            row = cur.fetchone()
            if (image_path + row[1]) in image_list:
                image_list.remove(image_path + row[1])
                c +=1

        print c

    count = 0
    new_list = []
    for name in image_list:
        new_list.append(name[len(image_path):])
        count = count +1

    print len(new_list)

    obj = defaultdict(list)
    for cap in objectData['annotations']:
        image_name = imdir%(subtype, cap['image_id'])
        obj[image_name].append(cap)

    imageData = []
    for imname in new_list:
        imgid = obj[imname][0]['image_id']
        imageData.append({'imageId':str(imgid), 'imageName':imname, 'imageType':'mscoco', 'imageSubType':subtype, 'numHitsFinished':'0'})

    with database.atomic():
        for idx in range(0, len(imageData), 200):
            print(idx)
            s = idx
            e = min(idx+200, len(imageData))
            Image.insert_many(imageData[s:e]).execute()

    objects = {}
    for idx in objectData['categories']:
        objects[str(idx['id'])] = idx['name']
    print objects

    c = 0
    objData = []
    ids = set()
    for imname in new_list:
        c = c+1
        try:
            imgid = obj[imname][0]['image_id']
            image = Image.get(Image.imageId == str(imgid))
            for cap in obj[imname]:
                if cap['id'] not in ids:
                    objData.append({'id': cap['id'], 'objectName': objects[str(cap['category_id'])], 'image': image})
                    ids.add(cap['ids'])
                else:
                    print("duplicate id " + str())
        except:
            pass

    with database.atomic():
        for idx in range(0, len(objData), 200):
            print(idx)
            s = idx
            e = min(idx+200, len(objData))
            ObjectPool.insert_many(objData[s:e]).execute()

    print "Objects table for " + split + " created."

def createRedisQueue():
    print "createRedisQueue called."

    import redis
    r = redis.StrictRedis(host='localhost', port=6380, password='REDIS_PASSWORD_HERE', db=0) # TODO

    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM image WHERE imageSubType = 'train2014' AND numHitsFinished = 0")
        r.delete('v20q_queue')
        count = 0
        for i in range(cur.rowcount):
            row = cur.fetchone()
            if(count < 5000): # push 5k images into queue
                print row[1], row[4]
                r.rpush('v20q_queue', row[1])
                count += 1

        print count

## ------------------------------------------------------------------------------------------------------
