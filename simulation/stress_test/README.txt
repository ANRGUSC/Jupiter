docker login
docker build -t yuki1711/sim_stress:v1 .
sudo docker push yuki1711/sim_stress:v1

docker images
docker run -i -t yuki1711/sim_stress:v1 /bin/bash

docker run -d --name sim localhost:5000/sim_stress:v1 # detached, given name 'sim'
docker exec -it sim python3 /stress_test.py # run python script inside running container 'sim'
