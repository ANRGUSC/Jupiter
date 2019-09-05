sudo docker login
sudo docker build -t yuki1711/sim_stress:v1 .
sudo docker push yuki1711/sim_stress:v1

sudo docker images
sudo docker run -i -t yuki1711/sim_stress:v1 /bin/bash
