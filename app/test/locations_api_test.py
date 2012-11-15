import json
import requests
from testify import *
from pymongo import Connection
from bson.objectid import ObjectId
from multiprocessing import Process
from app.server import app

port = 5001
url = 'http://localhost:%s' % port
db_name = 'location_test'

def start_server():
    app.conn_args = {}
    app.db_name = db_name
    app.debug = False
    app.run(port=port)

def send_data(method, path, data):
    return requests.request(method, url + path, data=json.dumps(data), 
        headers={'Content-Type': 'application/json'})

class LocationApiIntegerationTest(TestCase):
    
    @class_setup
    def setUpClass(cls):
        cls.server_process = Process(target=start_server)
        cls.server_process.start()
        cls.conn = Connection('localhost', 27017)
    
    @class_teardown
    def tearDownClass(cls):
        cls.server_process.terminate()
        cls.conn.drop_database(db_name)
        cls.conn.disconnect()
    
    @teardown
    def tearDown(self):
        self.conn[db_name].drop_collection('locations')
    
    def test_create_location(self):
        expected_location = {'name': 'foo', 'address': 'mumbai, India'}
        
        resp = send_data('post','/locations/', expected_location)
        
        assert_equal(200, resp.status_code)
        
        actual_location = json.loads(resp.content)
        
        assert_in('id', actual_location)
        assert_in('lat', actual_location)
        assert_in('lng', actual_location)
        
        _id = actual_location['id']
        del actual_location['id']
        
        location = self.conn[db_name].locations.find_one({'_id': ObjectId(_id)})
        
        assert_is_not(location, None)
    
    def test_get_all_locations(self):
        send_data('post','/locations/', {'name': 'foo', 'address': 'Time Square New York'})
        send_data('post','/locations/', {'name': 'bar', 'address': '700 Mission Street San Francisco CA'})
        send_data('post','/locations/', {'name': 'baz', 'address': 'Vile Parle, Mumbai'})
        
        resp = requests.get(url + '/locations/')
        
        assert_equal(200, resp.status_code)
        
        data = json.loads(resp.content)
        
        assert_equal(3, len(data))
        
        last_order = 0
        
        for location in data:
            assert_in('id', location)
            assert_in('lat', location)
            assert_in('lng', location)
            assert_is_not(location['id'], None)

    
    def test_get_location(self):
        location = {'name': 'foo', 'address': 'mumbai India'}
        create_resp = send_data('post', '/locations/', location)
        _id = json.loads(create_resp.content)['id']
        
        resp = requests.get(url + '/locations/' + _id)
        
        assert_equal(200, resp.status_code)
        print resp.content
        data = json.loads(resp.content)
        
        assert_equal(_id, data['id'])
        assert_equal(data['name'], location['name'])
    
    def test_update_location(self):
        location = {'name': 'foo', 'address': 'Cental Park New York'}
        create_resp = send_data('post','/locations/', location)
        
        _id = json.loads(create_resp.content)['id']
        
        location['name'] = 'bar'
        
        update_resp = send_data('put', '/locations/' + _id, location)
        
        assert_equal(200, update_resp.status_code)
        
        resp = requests.get(url + '/locations/' + _id)
        data = json.loads(resp.content)
        
        assert_equal(data['name'], location['name'])
    
    def test_delete_location(self):
        location = {'name': 'foo', 'address': 'Empire State New York'}
        create_resp = send_data('post','/locations/', location)
        
        _id = json.loads(create_resp.content)['id']
        
        delete_resp = requests.delete(url + '/locations/' + _id)
        
        assert_equal(200, delete_resp.status_code)
        
        resp = requests.get(url + '/locations/' + _id)
        
        assert_equal(404, resp.status_code)
    
    def test_that_non_existant_location_should_return_404(self):
        resp = requests.get(url + '/locations/4e971ed699b6bd4f08000001')
        
        assert_equal(404, resp.status_code)
    
    
    def test_invalid_method_should_return_not_allowed(self):
        resp = requests.request('put', url + '/locations/')

        assert_equal(405, resp.status_code)

if __name__ == '__main__':
    run()