import os
import json
import pymongo
from bson import json_util
from bson.objectid import ObjectId
from flask import Flask, render_template, request
from util import make_json_response, bad_id_response
from pygeocoder import Geocoder
import simplejson as json

app = Flask(__name__)

app.debug = True

def get_locations_for_templates():
    locations = get_collection()
    cur = locations.find()
    data = []
    
    for location in cur:
        location['id'] = str(location['_id'])
        del location['_id']
        data.append(location)

    return json.dumps(data)

@app.route('/')
def index():
    return render_template('index.html', locations=get_locations_for_templates())

@app.route('/locations/', methods=['GET'])
def get_locations():
    locations = get_collection()
    cur = locations.find().sort('order', pymongo.ASCENDING)
    data = []
    
    for location in cur:
        location['id'] = str(location['_id'])
        del location['_id']
        data.append(location)
    
    return make_json_response(data)

def address_to_lat_lng(address):
    result = Geocoder.geocode(address);
    place = str(result[0])
    lat, lng = result[0].coordinates
    #print "%s: %.5f, %.5f" % (place, lat, lng)  
    return place, lat, lng

@app.route('/locations/<location_id>',  methods=['GET'])
def get_location(location_id):
    oid = None
    
    try:
        oid = ObjectId(location_id)
    except:
        return bad_id_response()
    
    locations = get_collection()
    location = locations.find_one({'_id': oid})
    
    if location is None:
        return make_json_response({'message': 'no location with id: ' + location_id}, 404)
    
    location['id'] = str(location['_id'])
    del location['_id']
    
    return make_json_response(location)

def update_data(data):
    print data['address']
    address, lat, lng = address_to_lat_lng(data['address'])
    
    data['address'] = address
    data['lat'] = lat
    data['lng'] = lng
    return data;

@app.route('/locations/', methods=['POST'])
def create_location():
    data = request.json
    update_data(data);
    locations = get_collection()
    oid = locations.insert(data)
    location = locations.find_one({'_id': ObjectId(oid)})
    location['id'] = str(location['_id'])
    del location['_id']
    return make_json_response(location)

@app.route('/locations/<location_id>',  methods=['PUT'])
def update_location(location_id):
    data = request.json
    update_data(data);
    locations = get_collection()
    locations.update({'_id': ObjectId(location_id)}, {'$set': data})
    return make_json_response({'message': 'OK'})

@app.route('/locations/<location_id>',  methods=['DELETE'])
def delete_location(location_id):
    locations = get_collection()
    locations.remove(ObjectId(location_id))
    return make_json_response({'message': 'OK'})

def get_collection():
    uri = ''
    if 'MONGOLAB_URI' in os.environ:
        uri = os.environ['MONGOLAB_URI']
        db_name = uri[uri.rfind('/') + 1:]
    else:
        uri = 'localhost:27017'
        db_name = app.db_name
    print uri
    conn = pymongo.Connection(uri, **app.conn_args)
    return conn[db_name].locations

if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser()
    parser.add_option('-r', '--replicaset', dest='replicaset', help='Define replicaset name to connect to.')
    
    options, args = parser.parse_args()
    
    if options.replicaset is not None:
        app.conn_args = {'replicaset': options.replicaset, 'slave_okay': True}
    else:
        app.conn_args = {}
    
    app.db_name = 'locations_prod'
    app.jinja_env.globals.update(get_locations=get_locations)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
