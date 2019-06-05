### Jupiter Web Application

* Start backend
```console
$ cd backend
$ pip3 install -r requirements.txt
$ export FLASK_APP=/project/__init__.py
$ export KUBECONFIG=$HOME/admin.conf
$ python manage.py run
```

* Start frontend in another terminal window:
requirements: make sure you have installed the latest version of NodeJS and npm on your machine.
```console
$ cd frontend
$ npm install
$ npm start
```

Now it will open your browser automatically with link to http://localhost:3000 to see this web application.

1)config app_path, select a task mapper, and type in your node information.

2)set up the docker files and deploy Jupiter

3)copy your configuration.txt to web_app/backend folder

4)before run auto deploy scripts, click on "Get Plots" button and open links in a new page to see the CIRCE visualization with real time data.

5)when you deploy Jupiter successfully, click on "Run" button to see the exectution information and network statistics from DRUPE.
