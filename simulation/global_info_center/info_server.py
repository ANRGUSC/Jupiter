from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import json
import configparser

import collections

app = Flask('Global_Server')

### Krishna
@app.route('/post-prediction-resnet', methods=['POST'])
def request_resnet_prediction():
    print('Receive the prediction from resnet for job id')
    recv = request.get_json()
    job_id = recv['job_id']
    prediction = recv['msg']
    resnet_task_num = recv['resnet_task_num']
    ret_val = collagejobs.put_resnet_pred(job_id, prediction, resnet_task_num)
    response = ret_val
    print(collagejobs.job_resnet_preds_dict)
    return json.dumps(response)

@app.route('/post-predictions-collage', methods=['POST'])
def request_collage_prediction():
    print('Receive the prediction from collage for job id')
    recv = request.get_json()
    job_id = recv['job_id']
    final_preds = recv['msg']
    collagejobs.put_collage_preds(job_id, final_preds)
    response = job_id
    #print("posted predictions from collage: ", job_id, final_preds)
    #print("collage preds dict: ", collagejobs.job_collage_preds_dict)
    return json.dumps(response)

@app.route('/post-id-master', methods=['POST'])
def request_id_master():
    recv = request.get_json()
    response = collagejobs.get_id()
    print("New job id is: ", response)
    return json.dumps(response)

@app.route('/post-files-master', methods=['POST'])
def request_post_files():
    recv = request.get_json()
    job_id = recv['job_id']
    filelist = recv['filelist']
    #print("File list for job id %s is %s " % (job_id, filelist))
    response = collagejobs.put_files(job_id, filelist)
    print(collagejobs.job_files_dict)
    return json.dumps(response)

@app.route('/post-get-images-master', methods=['POST'])
def request_post_get_images():
    recv = request.get_json()
    #print("post-get-images: before processing")
    #print(collagejobs.job_files_dict)
    #print(collagejobs.job_resnet_preds_dict)
    #print(collagejobs.job_collage_preds_dict)
    response = collagejobs.get_missing_dict()
    print("missing files dict: ", response)
    #print("post-get-images: after processing")
    #print(collagejobs.job_files_dict)
    #print(collagejobs.job_resnet_preds_dict)
    #print(collagejobs.job_collage_preds_dict)
    return json.dumps(response)
    
class collageJobs(object):
    def __init__(self):
        self.current_job_id = 0
        self.num_tasks = 9
        self.job_files_dict = collections.defaultdict(list)
        self.job_resnet_preds_dict = collections.defaultdict(list)
        self.job_collage_preds_dict = collections.defaultdict(list)
        self.processed_jobids = []
    def get_id(self):
        self.job_resnet_preds_dict[self.current_job_id] = [-1] * self.num_tasks
        return self.current_job_id
    def put_files(self, job_id, filelist): 
        self.job_files_dict[job_id] = filelist
        self.current_job_id += 1
        return self.current_job_id
    def put_resnet_pred(self, job_id, pred, task_num):
        #print("job_id, resnet task_num, resnet preds for this job id", job_id, task_num, self.job_resnet_preds_dict[job_id])
        print("already processed job_ids", self.processed_jobids)
        if job_id in self.processed_jobids:
            return -1
        else:
            self.job_resnet_preds_dict[job_id][task_num] = pred
            return job_id
    def put_collage_preds(self, job_id, preds):
        self.job_collage_preds_dict[job_id] = preds
    #def get_collage_preds(self, job_id):
    #    return self.job_collage_preds_dict[job_id]
    #def get_resnet_preds(self, job_id):
    #    return self.job_resnet_preds_dict[job_id]
    #def get_files(self, job_id): 
    #    return self.job_files_dict[job_id]
    #def delete_jobs(self, job_id):
    #    if job_id in self.job_files_dict:
    #        del self.job_files_dict[job_id]
    #    if job_id in self.job_resnet_preds_dict:
    #        del self.job_resnet_preds_dict[job_id]
    #    if job_id in self.job_collage_preds_dict:
    #        del self.job_collage_preds_dict[job_id]
    #    return True
    def get_missing_dict(self):
    # There is collage prediction and some missing resnet predictions
        missing_files_preds_dict = {}
        job_ids = list(self.job_files_dict.keys())
        print("already processed job_ids")
        print(self.processed_jobids)
        #print("all job ids")
        #print(job_ids)
        for job_id in job_ids:
            if job_id in self.processed_jobids: # already processed
                continue
            missing = []
            if self.job_resnet_preds_dict[job_id].count(-1) >= RESNETS_THRESHOLD: # not enough resnet task predictions. too early for this jobid.
                continue
                #for i in range(self.num_tasks):
                #    missing.append(i)
            else:
                for idx, p in enumerate(self.job_resnet_preds_dict[job_id]):# Find missing resnet predictions
                    if p == -1:
                        missing.append(idx)
            print("missing tasks nums for jobid %s are %s" %(job_id, missing))
            if len(missing) > 0:
                if job_id in self.job_collage_preds_dict:# if collage predictions found
                    for idx in missing:
                        #logging.debug(task)
                        missing_pred = self.job_collage_preds_dict[job_id][idx]
                        if missing_pred != -1:
                            missing_file = self.job_files_dict[job_id][idx]
                            missing_files_preds_dict[missing_file] = missing_pred
                    self.processed_jobids.append(job_id)
            else: # len(missing) == 0. all resnet predictions are available.
                self.processed_jobids.append(job_id)
                
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
    global FLASK_DOCKER, RESNETS_THRESHOLD

    INI_PATH = 'jupiter_config.ini'
    config = configparser.ConfigParser()
    config.read(INI_PATH)
    FLASK_DOCKER  = int(config['PORT']['FLASK_DOCKER'])
    RESNETS_THRESHOLD = int(config['OTHER']['RESNETS_THRESHOLD'])

    num_class = 2
    log = []
    for i in range(num_class):
        event = EventLog()
        log.append(event)
    collagejobs = collageJobs()
    app.run(threaded = True, host = '0.0.0.0',port = FLASK_DOCKER) #address
    # app.run(threaded = True, host = '0.0.0.0')
    # app.run(host = '0.0.0.0',port = FLASK_DOCKER) #address
