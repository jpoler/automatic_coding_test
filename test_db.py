import math
import random
import unittest

from sqlalchemy import func
from sqlalchemy.sql import select, text

from engine import engine, session
from insert import DatabaseManager as DBM
from models import User, Trip
from models import SpatialQueries as SQ
from parse_inputs import get_json

import settings

class TestDatabaseInsertionTestCase(unittest.TestCase):
    json = get_json(settings.DATAPATH)

    def test_creation_of_user(self):
        result = session.query(User).filter_by(
            username=settings.USERNAME).first()

        self.assertEqual(result.username, settings.USERNAME)

    def test_creation_of_trip(self):
        self.assertNotEqual(len(self.json), 0)
        for item in self.json:
            tripid = item['id']
            if len(item['path']) > 1:
                result = session.query(Trip).filter_by(trip_id_string=tripid).first()
                self.assertEqual(result.trip_id_string, tripid)
            
    # the next three tests could be more thorough,
    # for instance, they could check that each attribute 
    # is the right value instead of merely checking for list length equality

    def test_creation_of_speeding_event(self):
        for trip in self.json:
            if len(trip['path']) > 1:
                speeding_events = [event for event in trip['drive_events']
                                   if event['type'] == 'speeding']
                db_trip = session.query(Trip).filter_by(trip_id_string=trip['id']).first()
                self.assertEqual(len(speeding_events), len(db_trip.speeding_events))
                
    def test_creation_of_hard_accel_event(self):
        for trip in self.json:
            if len(trip['path']) > 1:
                hard_accel_events = [event for event in trip['drive_events']
                                   if event['type'] == 'hard_accel']
                db_trip = session.query(Trip).filter_by(trip_id_string=trip['id']).first()
                self.assertEqual(len(hard_accel_events), len(db_trip.hard_acceleration_events))

    def test_creation_of_hard_brake_events(self):
        for trip in self.json:
            if len(trip['path']) > 1:
                hard_brake_events = [event for event in trip['drive_events']
                                   if event['type'] == 'hard_brake']
                db_trip = session.query(Trip).filter_by(trip_id_string=trip['id']).first()
                self.assertEqual(len(hard_brake_events), len(db_trip.hard_brake_events))



class TestSpatialDatabaseQueries(unittest.TestCase):
    json = get_json(settings.DATAPATH)
    user_id = 1
    
    def test_find_trips_matching_line(self):
        for trip in self.json:
            if len(trip['path']) > 1:
                line = SQ.points_to_projected_line(trip['path'])
                trips = list(SQ.find_trips_matching_line(trip['path'], self.user_id))
                for trip in trips:
                    self.assertTrue(engine.execute(func.ST_Contains(trip.geom, line)).first()[0])
        
    def test_get_associated_events(self):
        for trip in self.json:
            if len(trip['path']) > 1:
                db_trip = session.query(Trip).filter_by(trip_id_string=trip['id']).first()
                total_trips = len(db_trip.hard_brake_events) + \
                              len(db_trip.hard_acceleration_events) + \
                              len(db_trip.speeding_events)
                result = SQ.get_associated_events(db_trip)
                self.assertEqual(len(result), total_trips)

    def test_find_adjacent_points(self):
        trips = session.query(Trip).all()

        for trip in trips:
            events = SQ.get_associated_events(trip)
            for event in events:
                point = SQ.find_test_point_within_distance(event.point, trip.geom_path)
                result = SQ.find_adjacent_events(point, [event])
                self.assertEqual(len(result), 1)
                point = SQ.find_test_point_outside_distance(event.point, trip.geom_path)
                if point is None:
                    continue
                result = SQ.find_adjacent_events(point, [event])
                self.assertEqual(len(result), 0)
                
                
                
        # for every trip:
        #     find an event:
        
        # use ST_LineLocatePoint from event point to lock a point on the line
        # then use that fraction*ST_Length for total length from start
        # subtract a distance less than the threshold, and divide by ST_Length
        # ST_LineInterpolatePoint for the point we want
        # also subtract more than total to get out of bounds
        # obviously if subtraction results in a negative number, forget it
        
        # now check if these points are within a threshold to any others
        # make sure that the number you get back from find_adjacent_points
        # matches the total number of events within threshold
        #     check if it insersects any others
        #     thats your list to match
            
        #     also choose a coord outside of range of any and make sure list is empty

    def test_trip(self):
        
        # this one isnt bad
        # for simplicity, just do ST_LineInterpolatePoint and add distance along an
        # can add a set distance or ratio of total line at each step
        # existing trip to get trip points
        # can even add an x and y using the random function from earlier
        trips = session.query(Trip).filter_by(user_id=self.user_id)
        
        for trip in trips[:1]:
            points = SQ.segmentized_line_with_geographic_points(trip.trip_id)
            for start in range(0, len(points), 3):
                stop = min(start+3, len(points))
                point_group = points[start:stop]
                if len(point_group) < 2:
                    continue
                trips_matching_line = SQ.find_trips_matching_line(point_group, self.user_id)
                total_adj_events = []
                for matching_trip in trips_matching_line:
                    events = SQ.get_associated_events(matching_trip)
                    proj_point = SQ.\
                                 convert_geographic_coordinates_to_projected_point(*point_group[-1])
                    adj_events = SQ.find_adjacent_events(proj_point, events)
                    total_adj_events.extend(adj_events)
                res = SQ.adjacent_events_from_point_sequence(point_group, self.user_id)
                self.assertEqual(len(res), len(total_adj_events))    

if __name__ == '__main__':
    DBM.clear_database_and_create_tables()
    DBM.create_new_user(username=settings.USERNAME)
    DBM.insert_json_into_db( settings.USERNAME, get_json(settings.DATAPATH))
    unittest.main()
