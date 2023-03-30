#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request
from flask import redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

users = list()

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space
    
# creating a User class here
class User:
    # defining various functions within the class
    def obtain(self):
        return self.queue.get()

    def insert(self,user):
        self.queue.put_nowait(user)

    def __init__(self) :
        self.queue = queue.Queue()

def send_each (info):
    for each in users:
        each.insert(info)

def send_all_sigs (signals):
    send_each(json.dumps(signals))

# creating an object of the class World() 
myWorld = World()  

def set_listener( entity, data ):
    ''' do something with the update ! '''
    send_all_sigs({entity:data})

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    return redirect('/static/index.html', 301)

def read_ws(ws,user):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    # performing a try and accept block to catch an error
    try: 
        # running an infinite loop here
        while (1):
            # receiving the info here
            info = ws.receive()
            # printing the information received above
            print("The information is: " + info)
            if (info is None):
                break
            else :
                # loading the information received
                signals = json.loads(info)
                for each_key in signals:
                    each_value = signals[each_key]
                    # setting the respective values in the dict as a key-value pair
                    myWorld.set(each_key, each_value)  

                send_all_sigs(signals)

    # printing the error message if there is an error   
    except:
        print("Errror!!")

    return None

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    # ceate a new object of the class User
    user = User()
    # apending the object that got created above to the list called users
    users.append(user)
    gObj = gevent.spawn(read_ws, ws, user)

    try:
        while (1):
            # obtaining that user information
            info = user.obtain()
            ws.send(info)

    except Exception as error:
        # printing the error message here
        print("The Error is: " + error)

    # this block of code gets executed regardless if there is an exception or not
    finally:
        # removing that specific user from the list
        users.remove(user)
        # killing the gevent
        gevent.kill(gObj)

    return None

# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    # obtaining the returned data from the method flask_post_json()
    returnedData = flask_post_json()
    for key in returnedData:
        value = returnedData[key]
        # calling the update method of the World class to update the entity visa this interface
        myWorld.update(entity, key, value)
     # returning the updated entity when I get from the get() method in the World class
    return myWorld.get(entity)

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    # returning the world that is returned from the world() method in the World class
    return myWorld.world()

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    # returning the entity that I get from the get() method in the World class
    return myWorld.get(entity)

@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    # clearing the world by calling the clear method() in the World class
    myWorld.clear()
    # returning the cleared world by calling the world() method in the World class
    return myWorld.world()

if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()

