# UFav - Add your favourite places (with Backbone.js, Flask, and MongoDB)

This app uses 

* Backbone.js - Client side framework.
* Flask - A simple python webapp to provide a REST interface.
* MongoDB - Persistance for the client app.

Setup:

    virtualenv env --no-site-packages
    source env/bin/activate
    pip install -r requirements.txt
    mkdir data
    mongod --dbpath=data/ --fork --logpath=data/mongod.log
    python app/server.py
    http://localhost:5000/


Testing:
    testify app/test/location_api_test.py


