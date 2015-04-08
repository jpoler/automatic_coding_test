import json
import os
import unittest
from urllib import urlencode
from urllib2 import urlopen


from parse_inputs import get_json
import settings

class TestRemoteEndpoint(unittest.TestCase):
    username = settings.USERNAME
    port = settings.PORT
    ip = os.environ['JPOLER_SERVER_IP']
    json = get_json('data1')
    
    def test_endpoint_yields_correct_messages(self):
        points = self.json[0]['path']
        for i in range(0, len(points), 3):
            start = i
            end = min(i+3, len(points))
            point_group = points[start:end]
            serializable_point_group = [list(pair) for pair in point_group]
            json_point_group = dict(points=serializable_point_group)
            serialized_json = json.dumps(json_point_group)
            qs = urlencode(dict(json=serialized_json))
            url = 'http://{host}:{port}/alerts/{username}?{qs}'.format(**{'host': self.ip,
                                                                          'port': self.port,
                                                                          'username': self.username,
                                                                          'qs': qs})

            url_descriptor = urlopen(url)
            self.assertEqual(url_descriptor.getcode(), 200)
            rv = url_descriptor.read()
            print(rv)
            json_response = json.loads(rv)
            warnings = json_response.get('warnings')
            self.assertIsInstance(warnings, list)
            for warning in warnings:
                self.assertIsInstance(warning, unicode)
            print("warnings at {location}:\n{warnings}".format(location=point_group[-1],
                                                              warnings=warnings))

if __name__ == '__main__':
    unittest.main()
