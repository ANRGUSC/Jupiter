from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import json
import configparser

app = Flask('Global_Server')

# function of job_id response
@app.route('/post-id', methods=['POST'])
def request_id():
    print('Receive job id request')
    recv = request.get_json()
    class_image = recv['class_image']
    response = str(log[class_image-1].get_id())
    print(response)
    log[class_image-1].id_update()
    print(log[class_image-1].id)
    print(log[class_image-1].job_dict)
    return json.dumps(response)
    
# function of dictionary response
@app.route('/post-dict',methods=['POST'])
def request_dict():
    print('Receive job dictionary request')
    recv = request.get_json()
    print(recv['job_id'])
    print(recv['filename'])
    class_image = recv['class_image']
    log[class_image-1].dict_update(recv['job_id'],recv['filename'])
    print(log[class_image-1])
    response = log[class_image-1].get_dict()
    print(response)
    return json.dumps(response)


class EventLog(object):
        def __init__(self):
            self.id = 1
            self.job_dict = {'1':[]}
        def get_id(self):
            return self.id
        def id_update(self):
            self.id+=1
            self.job_dict[str(self.id)] = [] # when the new job comes, we add a list to the dictionary for this new job
        def get_dict(self):
            return self.job_dict
        def dict_update(self,job_id,filename):
            self.job_dict[job_id].append(filename) # update the received result to dictionary


if __name__ == '__main__':
    global FLASK_DOCKER

    INI_PATH = 'jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    FLASK_DOCKER  = int(config['PORT']['FLASK_DOCKER'])

    num_class = 2
    log = []
    for i in range(num_class):
        event = EventLog()
        log.append(event)
    app.run(threaded = True, host = '0.0.0.0',port = FLASK_DOCKER) #address
    # app.run(host = '0.0.0.0',port = FLASK_DOCKER) #address