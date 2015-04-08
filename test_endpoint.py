import json
import unittest
from urllib import urlencode

from app import app
from insert import DatabaseManager as DBM
from models import SpatialQueries as SQ
from parse_inputs import get_json
import settings

class TestRESTEndpoint(unittest.TestCase):
    username = settings.USERNAME
    
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()
        
    def test_invalid_username_returns_403(self):
        rv = self.app.get('/alerts/sadflkjsfdal')
        ## assert that 403 is returned on invalid username
        self.assertEqual(rv.status_code, 403)

    def test_no_json_param_returns_400(self):
        url = '/alerts/{username}?useless_param={useless_param}'.format(
            **{'username': self.username,
               'useless_param': 'foo',})
        rv = self.app.get(url)
        
        self.assertEqual(rv.status_code, 400)
        
        # just to make sure that json is parseable and has a message attribute
        json_response = json.loads(rv.data)
        self.assertTrue('message' in json_response)
        self.assertIsInstance(json_response['message'], unicode)

    def test_malformed_json_object_returns_400(self):
        url = '/alerts/{username}?json={json}'.format(
            **{'username': self.username,
               'json': '{badness>]}',})
        rv = self.app.get(url)
        
        self.assertEqual(rv.status_code, 400)
        
        # just to make sure that json is parseable and has a message attribute
        json_response = json.loads(rv.data)
        self.assertTrue('message' in json_response)
        self.assertIsInstance(json_response['message'], unicode)
        

    def test_no_points_returns_400(self):
        url = '/alerts/{username}?json={json}'.format(
            **{'username': self.username,
               'json': '{}',})
        rv = self.app.get(url)
        
        self.assertEqual(rv.status_code, 400)
        
        # just to make sure that json is parseable and has a message attribute
        json_response = json.loads(rv.data)
        self.assertTrue('message' in json_response)
        self.assertIsInstance(json_response['message'], unicode)
        self.assertTrue('points' in json_response['message'])
        
        

    def test_endpoint_yields_correct_messages(self):
        points = SQ.segmentized_line_with_geographic_points(1)
        for i in range(0, len(points), 3):
            start = i
            end = min(i+3, len(points))
            point_group = points[start:end]
            serializable_point_group = [list(pair) for pair in point_group]
            json_point_group = dict(points=serializable_point_group)
            serialized_json = json.dumps(json_point_group)
            qs = urlencode(dict(json=serialized_json))
            url = '/alerts/{username}?{qs}'.format(**{'username': self.username,
                                                       'qs': qs})
            rv = self.app.get(url)
            self.assertEqual(rv.status_code, 200)
            json_response = json.loads(rv.get_data())
            warnings = json_response.get('warnings')
            self.assertIsInstance(warnings, list)
            for warning in warnings:
                self.assertIsInstance(warning, unicode)
            print("warnings at {location}:\n{warnings}".format(location=point_group[-1],
                                                              warnings=warnings))

    

if __name__ == '__main__':
    DBM.clear_database_and_create_tables()
    DBM.create_new_user(username=settings.USERNAME)
    DBM.insert_json_into_db( settings.USERNAME, get_json(settings.DATAPATH))
    unittest.main()
