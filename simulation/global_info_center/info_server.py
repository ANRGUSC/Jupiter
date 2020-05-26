from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import json
import configparser

import collections

app = Flask('Global_Server')

### Krishna
@app.route('post-prediction-resnet', methods=['POST'])
def request_resnet_prediction():
    print('Receive the prediction from resnet for job id')
    recv = request.get_json()
    job_id = recv['job_id']
    prediction = recv['msg']
    resnet_task_num = recv['resnet_task_num']
    collagejobs.put_resnet_pred(job_id, prediction, resnet_task_num)
    response = ""
    return json.dumps(response)

@app.route('post-predictions-collage', methods=['POST'])
def request_collage_prediction():
    print('Receive the prediction from resnet for job id')
    recv = request.get_json()
    job_id = recv['job_id']
    final_preds = recv['msg']
    collagejobs.put_collage_preds(job_id, final_preds)
    response = ""
    return json.dumps(response)

@app.route('post-id-master', methods=['POST'])
def request_id_master():
    recv = request.get_json()
    response = collagejobs.get_id()
    return json.dumps(response)

@app.route('post-files-master', methods=['POST'])
def request_post_files():
    recv = request.get_json()
    job_id = recv['job_id']
    filelist = recv['filelist']
    response = collagejobs.put_files(job_id, filelist)
    return json.dumps(response)

@app.route('post-get-images-master', methods=['POST'])
def request_post_get_images():
    recv = request.get_json()
    response = collagejobs.get_missing_dict() 
    return json.dumps(response)
    
class collageJobs(object):
    def __init__(self):
        self.job_id = 0
        self.num_tasks = 9
        self.job_files_dict = collections.defaultdict(list)
        self.job_resnet_preds_dict = {}
        self.job_collage_preds_dict = collections.defaultdict(list)
    def get_id(self):
        return self.job_id
    def put_files(self, job_id, filelist): 
        self.job_files_dict[job_id] = filelist
        self.job_id += 1
        return self.job_id
    def put_resnet_pred(self, job_id, pred, task_num):
        if job_id not in self.job_resnet_preds_dict: 
            self.job_resnet_preds_dict[job_id] = [-1] * self.num_tasks
        self.job_resnet_preds_dict[job_id][task_num] = pred
    def put_collage_preds(self, job_id, preds):
        self.job_collage_preds_dict[job_id] = preds
    def get_collage_preds(self, job_id):
        return self.job_collage_preds_dict[job_id]
    def get_resnet_preds(self, job_id):
        return self.job_resnet_preds_dict[job_id]
    def get_files(self, job_id): 
        return self.job_files_dict[job_id]
    def delete_jobs(self, job_id):
        del self.job_files_dict[job_id]
        del self.job_resnet_preds_dict[job_id]
        del self.job_collage_preds_dict[job_id]
        return True
    def get_missing_dict(self):
    # There is collage prediction and some missing resnet predictions
        missing_files_preds_dict = {}
        job_ids = list(self.job_files_dict.keys())
        for job_id in job_ids:
            missing = []
            for idx, p in enumerate(self.job_resnet_preds_dict[job_id]):# Find missing resnet predictions
                if p == -1:
                    missing.append(idx)
            if len(missing) > 0:
                if job_id in self.job_collage_preds_dict:# if collage predictions found
                    for idx in missing:
                        #logging.debug(task)
                        missing_pred = self.job_collage_preds_dict[job_id][idx]
                        if missing_pred != -1:
                            missing_file = self.job_files_dict[job_id][idx]
                            missing_files_preds_dict[missing_file] = missing_pred
            self.delete_jobs(job_id)
        return missing_files_preds_dict
### Krishna

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
    collagejobs = collageJobs()
    app.run(threaded = True, host = '0.0.0.0',port = FLASK_DOCKER) #address
    # app.run(host = '0.0.0.0',port = FLASK_DOCKER) #address
