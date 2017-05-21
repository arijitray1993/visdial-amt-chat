from constants import * #TODO make the same as constants.py
import MySQLdb as mysql
import time
import redis
from peewee import *
from datetime import datetime
from createDatabase import * #TODO Centralize this so there aren't copies floating about
from flask import Flask, render_template, request, send_from_directory, send_file
from flask_socketio import SocketIO

print('AMTHits Table Exists: '+ str(AMTHits.table_exists()))
print(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))


app = Flask(__name__)
app.secret_key = b'Make this a good secret!' #TODO
app.config['DEBUG'] = True #TODO Remove
socketio = SocketIO(app)
APP_DIR = os.path.dirname(os.path.realpath(__file__))

activeUsers = {}
numUsers = 0
dummyId = 0

userQueue = []

@app.route('/semanticui/<path:path>')
def send_semanticui(path):
    return send_from_directory('semanticui', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('css', path)

# app.use(express.static(path)) #REVIEW?

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('js', path)

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/dist/<path:path>')
def send_dist(path):
    return send_from_directory('semanticui/dist', path)
# app.use(express.static(path + 'static/dataset/')) # TODO

@app.route('/')
def send_index():
    return send_file('index.html')

#node.js routing doesn't quite work for flask.
@app.route('/main.css')
def send_main_css():
    return send_from_directory('css','main.css')
@app.route('/holder.js')
def send_holder_js():
    return send_from_directory('js','holder.js')
@app.route('/countdown/countdown.js')
def send_countdown_js():
    return send_from_directory('js/countdown','countdown.js')
@app.route('/example.png')
def send_example():
    return send_file('example.png')
@app.route('/url.js')
def send_url_js():
    return send_from_directory('js','url.js')

def getUid():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=36))

#@socketio.on('connection')
#def on_connection(socket):
    #TODO, this method has no purpose
    #socket = {'id': request.sid}

#    print('a user connected')

    #socket["partnerId"] = ''
    #socket["noOfMsg1st"] = 0
    #socket["noOfMsg2nd"] = 0

# when the client emits 'add user', this listens and executes
@socketio.on('add user')
def on_add_user(msg):
    socket = {'id': request.sid}

    # we store the username in the socket session for this client
    # socket["username"] = msg['personName']
    if (msg['workerId'] == None):
        socket["workerId"] = str(dummyId)
        dummyId = dummyId + 1
        socket["assignmentId"] = socket["workerId"]
        socket["hitId"] = socket["workerId"]
    else:
        socket["workerId"] = msg['workerId']
        socket["assignmentId"] = msg['assignmentId']
        socket["hitId"] = msg['hitId']
    socket["partnerId"] = ''
    socket["noOfMsg1st"] = 0
    socket["noOfMsg2nd"] = 0
    socket["role"] = ''

    print('WorkerId: ' + socket["workerId"])
    print('AssignmentId: ' + socket["assignmentId"])
    # add the client's username to the global list
    activeUsers[socket["id"]] = socket
    numUsers += 1

    isPaired = False

    if (len(userQueue) == 0):
        socket["role"] = 'question'
        userQueue.append(socket["id"])
        print('First User in the queue: '+ socket["workerId"])
    else:
        flag = 0
        i = 0
        while(i < len(userQueue)):
            userPairId = ''
            userPairId = userQueue.pop(0)
            if(activeUsers[userPairId]==None): # If there is only one user in the queue.
                #time.sleep(1)
                break
            if(activeUsers[userPairId]["workerId"] == socket["workerId"]):
                # Checking if the same user is try to connect to itself. In which case don't connect and add him back to the queue.
                print('Worker 1: ' + socket["workerId"])
                print('Worker 2: ' + activeUsers[userPairId]["workerId"])
                i= i+1
                userQueue.append(userPairId)
                continue
            print('Separate Worker 1: ' + socket["workerId"])
            print('Separate Worker 2: ' + activeUsers[userPairId]["workerId"])

            if(userPairId in activeUsers):
                activeUsers[userPairId]["partnerId"] = socket["id"]
                activeUsers[userPairId]["key"] = socket["id"] + userPairId
                activeUsers[userPairId]["image_name"] = 'sample'
                activeUsers[userPairId]["role"]    = 'answer'

                socket["partnerId"] = userPairId

                activeUsers[socket["id"]]["partnerId"] = userPairId
                activeUsers[socket["id"]]["key"] = socket["id"] + userPairId
                activeUsers[socket["id"]]["image_name"] = 'sample'
                activeUsers[socket["id"]]["role"]    = 'question'

                isPaired = True
                image_url=""
                found_image = False
                foundFlag = False
                for _ in range(60):
                    if(foundFlag == False):    # Pop from the queue and check if either user has done that image before.
                        res = client.rpop(REDIS_LIST)
                        resp = (AMTHits.select(AMTHits)
                                .join(Image)
                                .where((AMTHits.workerId << [activeUsers[userPairId]["workerId"], socket["workerId"]])\
                                       & (Image.imageName == res))
                                .count())
                        #print(resp)
                        #print('Image Name: ' + res)
                        print('SQL Check: ' + resp)
                        if(resp!=0):
                            client.lpush(REDIS_LIST, res)
                            continue
                        foundFlag = True
                        image_url = res

                        print('Image: ' + res)

                        #knex.select('image.imageId').from('image').where('image.imageName', '=', res)
                        cap = (ObjectPool.select(ObjectPool.objectName, ObjectPool.image.id)
                               .join(Image)
                               .where(Image.imageName == res)
                               .order_by(fn.Rand())
                               .limit(1))[0]
                        print('Create pool of images')
                        try:
                            ImagePool.where(ImagePool.assignmentId == socket["assignmentId"]).delete()
                        except:
                            pass
                        print('Insert correct image for first turker')

                        # Select random 19 add to res for the image pool.
                        ImagePool.create(assignmentId=socket["assignmentId"],
                                         image=cap.image)
                        print('Insert correct image for second turker')
                        ImagePool.create(assignmentId=activeUsers[userPairId]["assignmentId"],
                                         image=cap.image)
                        print('Select the rest of the images')
                        # print('Transaction complete.')
                        poolItems = (ObjectPool.select(ObjectPool.image.id)
                                     .join(Image)
                                     .where((ObjectPool.image.imageSubType == 'train2014')
                                            & (ObjectPool.image.id != cap.image.id)
                                            & ((random.random() < 0.5) or (ObjectPool.objectName == cap.objectName))
                                           )
                                     .order_by(fn.Rand())
                                     .limit(19))
                        print(poolItems.length)
                        emitNeeded = True
                        for item in poolItems:
                            ImagePool.create(assignmentId=socket["assignmentId"],
                                             image_id=item.image.id)
                            ImagePool.create(assignmentId=activeUsers[userPairId]["assignmentId"],
                                             image_id=item.image.id)

                        # print('Finding pool of image urls')
                        if (emitNeeded):
                            pool = []
                            urls = (ImagePool.select(ImagePool.image.id, ImagePool.image.imageName)
                                    .join(Image)
                                    .where(ImagePool.assignmentId == socket["assignmentId"])
                                    .order_by(fn.Rand()))
                            for item in urls:
                                #print(item['imageName'])
                                pool.append({id: item['image_id'],
                                             img: 'train2014/' + item['imageName']})
                            # add the first person's HIT details
                            emitNeeded = False
                            AMTHits.create(socketId=socket["key"],
                                           image_id=cap.image.id,
                                           workerId=socket["workerId"],
                                           assignmentId=socket["assignmentId"],
                                           hitId=socket["hitId"],
                                           approve='notApprove',
                                           status='started',
                                           created_at=int(time.time())
                                          )
                            # add the second person's HIT details
                            AMTHits.create(socketId=activeUsers[userPairId]["key"],
                                           image_id=cap.image.id,
                                           workerId=activeUsers[userPairId]["workerId"],
                                           assignmentId=activeUsers[userPairId]["assignmentId"],
                                           hitId=activeUsers[userPairId]["hitId"],
                                           approve='notApprove',
                                           status='started',
                                           created_at=int(time.time())
                                          )
                            # finally, emit the messages.
                            activeUsers[userPairId]["image_name"] = image_url
                            activeUsers[socket["id"]]["image_name"] = image_url
                            activeUsers[socket["id"]]["push"] = True
                            socketio.emit('paired', {
                                'partnerId' : userPairId,
                                'key' : socket["id"] + userPairId,
                                'image_url': 'train2014/' + image_url,
                                'role': 'question',
                                'pool': pool
                            }, room=socket['id'], include_self=False)

                            socketio.emit('paired', {
                                'partnerId' :socket["id"],
                                'key' : socket["id"] + userPairId,
                                'role': 'answer',
                                'pool': pool
                            }, room=activeUsers[userPairId], include_self=False)
                            print('assignmentId:' + socket["assignmentId"])
                flag = 1
                break
                if( flagfound==False):
                    print('All images tried by this user: ' + socket["workerId"])
                    socketio.emit('error', {errorMsg: "You completed tasks for all the images in the database. Thank you for all your work. Please try again later."},
                                  room=socket['id'], include_self=False
                                 )
        if (flag==0):
            userQueue.append(socket["id"])

# when a chat message is sent. This is emmitted by $(send) in index.html
@socketio.on('chat message')
def on_chat_message(msg):
    socket = activeUsers[request.sid]
    f = 'chatmsg : '
    socket["noOfMsg1st"] = socket["noOfMsg1st"] + 1
    print(JSON.stringify(msg))
    ig = socket["image_name"]
    print(ig)
    if (socket["partnerId"] in activeUsers):
        activeUsers[socket["partnerId"]]["noOfMsg2nd"] = activeUsers[socket["partnerId"]]["noOfMsg2nd"] + 1
        socketio.emit('receive message', {'message' : msg['msg'], 'noOfMsg': socket["noOfMsg1st"]},
                      room=activeUsers[socket["partnerId"]], include_self=False)
        print(f + 'message count: ' + socket["noOfMsg2nd"] + socket["noOfMsg1st"])
        ig = activeUsers[socket["partnerId"]]["image_name"]

    hitResult = (AMTHits.select(AMTHits.id)
                 .where((AMTHits.id == msg['hitId'])
                 & (AMTHits.assignmentId == msg['assignmentId'])
                 & (AMTHits.workerId == msg['workerId'])
                 & (AMTHits.socketId == socket["key"])))
    img = Image.select(Image.id, Image.numHitsFinished).where(Image.imageName == ig)
    print(JSON.stringify(img))

    if(msg['role'] == 'question'):
        print(f + 'in question')
        Question.create(question=msg['msg'],
                        image_id=img[0].id, #TODO
                        annotationId_id=hitResult[0].id,
                        sequenceId=msg['seqId'],
                        socketId=socket["key"],
                        sourceId=socket["id"],
                        destId=socket["partnerId"],
                        created_at=int(time.time())
                       )

    else:
        print(f + 'in answer')
        quesResult = (Question.select(Question.id, Question.image.id)
                      .where((Question.socketId == socket["key"]))
                      & (Question.sequenceId == msg['seqId']))
        if(quesResult.length == 0): #questioner disconnected, so you won't have any question for this answ
            Answer.create(answer=msg['msg'],
                          question_id='',
                          image_id=img[0].id,
                          annotationId_id=hitResult[0].id,
                          sequenceId=msg['seqId'],
                          socketId=socket["key"],
                          sourceId=socket["id"],
                          destId=socket["partnerId"],
                          created_at=int(time.time())
                         )
        else:     #question exists
            # print(quesResult[0])
            Answer.create(answer=msg['msg'],
                          question_id=quesResult[0].id, #select the question id of the last question asked.
                          image_id=img[0].id,
                          annotationId_id=hitResult[0].id,
                          sequenceId=msg['seqId'],
                          socketId=socket["key"],
                          sourceId=socket["id"],
                          destId=socket["partnerId"],
                          created_at=int(time.time())
                         )

@socketio.on('finish hit')
def on_finish_hit(msg):
    socket = activeUsers[request.sid]

    print('HIT submitted')
    if('push' in socket):
        if(socket['push']==True):
            socket['push'] = False
    img = Image.select(Image.id).where(Image.imageName == socket["image_name"])
    # print(JSON.stringify(img))
    (AMTHits.where((AMTHits.image.id == img[0].id)
     & (AMTHits.assignmentId == socket["assignmentId"])
     & (AMTHits.hitId == socket["hitId"])
     & (AMTHits.workerId == socket["workerId"])
     & (AMTHits.socketId == socket["key"]))
     .update(status='finished',
             completed_at=int(time.time())
            ))     # Increment the number of hits finished.
    print('Status: Finished')

    cnt = AMTHits.count(AMTHits.id).where((image_id == img[0].id)
                                          & (AMTHits.status == 'finished'))
    cnt = (cnt + 1)/2
    Image.where(Image.id == img[0].id).update(numHitsFinished=str(cnt))
    Feedback.create(workerId=msg['workerId'],
                    hitId=msg['hitId'],
                    assignmentId=msg['assignmentId'],
                    sequenceId=socket["key"],
                    feedback=msg['feedback']
                   )

@socketio.on('disconnect')
def on_disconnect():
    socket = activeUsers[request.sid]
    print('Got disconnected!')
    print(socket["partnerId"])
    if('push' in socket):
        if(socket['push'] == True):
             client.lpush(REDIS_LIST, socket['image_name'])
    # ToDo: Finish HIT here!
    if(socket["partnerId"] !='' or socket["partnerId"]==None):
        if(socket["partnerId"] in activeUsers):
            activeUsers[socket["partnerId"]]["partnerId"] = ''
            socketio.emit('disconnected partner', {'disable':'True'},
                          room=activeUsers[socket["partnerId"]], include_self=False)
    del activeUsers[socket["id"]]

@socketio.on('selected guess')
def on_selected_guess(msg):
    socket = activeUsers[request.sid]
    print('Guess selected!')
    print(msg['id'])
    img = Image.select(Image.id).where(Image.imageName == socket["image_name"])
    (AMTHits.where((AMTHits.image_id == img[0].id)
        & (AMTHits.assignmentId == socket["assignmentId"])
        & (AMTHits.id == socket["hitId"])
        & (AMTHits.workerId == socket["workerId"])
        & (AMTHits.socketId == socket["key"]))
        .update(guess=msg['id']))
    (AMTHits.where((AMTHits.image.id == img[0].id)
        & (AMTHits.assignmentId == activeUsers[socket["partnerId"]]["assignmentId"])
        & (AMTHits.id == activeUsers[socket["partnerId"]]["hitId"])
        & (AMTHits.workerId == activeUsers[socket["partnerId"]]["workerId"])
        & (AMTHits.socketId == activeUsers[socket["partnerId"]]["key"]))
        .update(guess=msg['id']))
    socketio.emit('selected', {guess: msg['img'], truth: 'train2014/' + socket["image_name"]},
                  room=socket['id'], include_self=False
                 )
    socketio.emit('selected', {guess: msg['img'], truth: 'train2014/' + socket["image_name"]},
                  room=activeUsers[socket["partnerId"]], include_self=False)
    socketio.emit('guess', msg,
                  room=activeUsers[socket["partnerId"]], include_self=False)

@socketio.on("typing")
def on_typing(message):
    socket = activeUsers[request.sid]
    if (socket["partnerId"] in activeUsers):
        if(message):
            socketio.emit('is typing', {isTyping: 'yes'},
                          room=activeUsers[socket["partnerId"]], include_self=False)
        else:
             socketio.emit('is typing', {isTyping: 'no'},
                           room=activeUsers[socket["partnerId"]], include_self=False)

if __name__ == '__main__':
    socketio.run(app, port=5001)
