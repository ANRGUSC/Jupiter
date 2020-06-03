import requests
import json

hdr = {
        'Content-Type': 'application/json',
        'Authorization': None #not using HTTP secure
                                }
print("Request 0")

print("post id master")
pred_collage_server_url = 'http://0.0.0.0:5000/post-id-master'
response = requests.post(pred_collage_server_url, headers = hdr, data = json.dumps(""))
job_id = response.json()
print(job_id)

print("post files master")
filelist = ['n03345487_10_jobid_0.JPEG','n03345487_108_jobid_0.JPEG', 'n03345487_133_jobid_0.JPEG','n03345487_135_jobid_0.JPEG','n03345487_136_jobid_0.JPEG','n04146614_16038_jobid_0.JPEG','n03345487_18_jobid_0.JPEG','n03345487_40_jobid_0.JPEG','n03345487_78_jobid_0.JPEG']
params = {"job_id": job_id, "filelist":filelist}
post_files_master_server_url = 'http://0.0.0.0:5000/post-files-master'
response = requests.post(post_files_master_server_url, headers = hdr, data = json.dumps(params))
next_job_id = response.json()
print(next_job_id)

pred_resnet_server_url = 'http://0.0.0.0:5000/post-prediction-resnet'
for i in range(7):
    prediction = 555
    resnet_task_num = i
    params = {"job_id": job_id, 'msg': prediction, "resnet_task_num": resnet_task_num}
    response = requests.post(pred_resnet_server_url, headers = hdr, data = json.dumps(params))
    ret_job_id = response.json()
    print(ret_job_id)

print("post predictions collage")
pred_collage_server_url = 'http://0.0.0.0:5000/post-predictions-collage'
final_preds = [-1,-1,-1,-1,-1,-1,-1,555,555]
params = {"job_id": job_id, 'msg': final_preds}
response = requests.post(pred_collage_server_url, headers = hdr, data = json.dumps(params))
ret_job_id = response.json()
print(ret_job_id)

print("Request 1")

print("post id master")
pred_collage_server_url = 'http://0.0.0.0:5000/post-id-master'
response = requests.post(pred_collage_server_url, headers = hdr, data = json.dumps(""))
job_id = response.json()
print(job_id)

print("post files master")
filelist = ['n04146614_1_jobid_1.JPEG','n04146614_39_jobid_1.JPEG','n04146614_152_jobid_1.JPEG','n04146614_209_jobid_1.JPEG','n04146614_263_jobid_1.JPEG','n04146614_318_jobid_1.JPEG','n03345487_206_jobid_1.JPEG','n03345487_243_jobid_1.JPEG','n03345487_284_jobid_1.JPEG']
params = {"job_id": job_id, "filelist":filelist}
post_files_master_server_url = 'http://0.0.0.0:5000/post-files-master'
response = requests.post(post_files_master_server_url, headers = hdr, data = json.dumps(params))
next_job_id = response.json()
print(next_job_id)

pred_resnet_server_url = 'http://0.0.0.0:5000/post-prediction-resnet'
for i in range(9):
    prediction = 555
    resnet_task_num = i
    params = {"job_id": job_id, 'msg': prediction, "resnet_task_num": resnet_task_num}
    response = requests.post(pred_resnet_server_url, headers = hdr, data = json.dumps(params))
    ret_job_id = response.json()
    print(ret_job_id)

print("post predictions collage")
pred_collage_server_url = 'http://0.0.0.0:5000/post-predictions-collage'
final_preds = [-1,-1,-1,-1,-1,-1,-1,555,555]
params = {"job_id": job_id, 'msg': final_preds}
response = requests.post(pred_collage_server_url, headers = hdr, data = json.dumps(params))
ret_job_id = response.json()
print(ret_job_id)

print("Get missing files master")
get_missing_files_master_server_url = 'http://0.0.0.0:5000/post-get-images-master'
response = requests.post(get_missing_files_master_server_url, headers = hdr, data = json.dumps(""))
missing_files = response.json()
print(missing_files)
