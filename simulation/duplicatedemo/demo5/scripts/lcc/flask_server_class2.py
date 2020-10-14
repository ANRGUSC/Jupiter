from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import json

app = Flask('Server_class2')

@app.route('/log', methods=['GET'])
def print_log_callback():
    response = jsonify(log.get())
    return response

# function of job_id response
@app.route('/post-id', methods=['POST'])
def request_id():
    payload = request.get_json()
    response = str(log.get_id())
    log.id_update()
    return json.dumps(response)

# function of dictionary response
@app.route('/post-dict',methods=['POST'])
def request_dict():
    recv = request.get_json()
    response = log.get_dict()
    log.dict_update(recv['job_id'],recv['filename'])
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
    log = EventLog()
    app.run(threaded = True, host = '0.0.0.0') #address
