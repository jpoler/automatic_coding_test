## California UTM zone 10: 26910
## Assuming NAD83 for datum

import random

from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction

from sqlalchemy import (Column, Integer, BigInteger, String, Float, PickleType, Time,
                        ForeignKey, func)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import select, text

from engine import engine, session
import settings



Base = declarative_base()

class User(Base):
    """username, which is assumed to be unique, and one-to-many rel with Trip"""
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    trips = relationship('Trip', backref=backref('users', order_by=user_id))

    def __repr__(self):
        return "<User(username='{}')>".format(self.username)

class Trip(Base):
    """Trips contain all information available from the API as fields."""
    __tablename__ = 'trips'
    trip_id = Column(Integer, primary_key=True)
    geom = Column(Geometry(geometry_type='POLYGON', srid=settings.TARGET_PROJECTION))
    geom_path = Column(Geometry(geometry_type='LINESTRING', srid=settings.TARGET_PROJECTION))
    user_id = Column(Integer, ForeignKey('users.user_id'))
    average_mpg = Column(Float)
    distance_m = Column(Float)
    duration_over_70_s = Column(Integer)
    duration_over_75_s = Column(Integer)
    duration_over_80_s = Column(Integer)
    end_location = Column(PickleType)
    end_time = Column(BigInteger)
    end_time_zone = Column(String)
    fuel_cost_usd = Column(Float)
    fuel_volume_gal = Column(Float)
    hard_accels = Column(Integer)
    hard_brakes = Column(Integer)
    trip_id_string = Column(String, unique=True)
    path = Column(PickleType)
    score = Column(PickleType)
    start_location = Column(PickleType)
    start_time = Column(BigInteger)
    start_time_zone = Column(String)
    uri = Column(String)
    speeding_events = relationship('SpeedingEvent', backref=backref('trips', order_by=trip_id))
    hard_brake_events = relationship('HardBrakeEvent', backref=backref('trips', order_by=trip_id))
    hard_acceleration_events = relationship('HardAccelerationEvent', 
                                            backref=backref('trips', order_by=trip_id))
    def __init__(self, trip=None, srid='0'):
        """This won't try to catch KeyErrors because it is 
        better than nasty surprises later.
        """

        self.event_types = {
            'speeding': SpeedingEvent,
            'hard_accel': HardAccelerationEvent,
            'hard_brake': HardBrakeEvent
        }
        if trip is None:
            raise ValueError("A trip object must be supplied")
        trip.pop('user')
        # this path will be used to find speeding_event substrings
        path_linestring = SpatialQueries.points_to_projected_line(trip['path'])
        # paths are stored with a 20 M buffer as a polygon to account for gps
        # inaccuracies. This is just a very rough way to do this, more care
        # would be needed for a robust solution, such as greater buffer size,
        # or simply checking that a high percentage of points are within a smaller
        # buffer.
        trip['geom_path'] = path_linestring
        trip['geom'] = func.ST_Buffer(path_linestring, 20)
        trip_id_string = trip.pop('id')
        trip['trip_id_string'] = trip_id_string
        drive_events = trip.pop('drive_events')
        
        super(Trip, self).__init__(**trip)


        for event in drive_events:
            cls = self.event_types[event.pop('type')]
            lst = getattr(self, cls.__tablename__)
            lst.append(cls(trip['trip_id_string'], event, path_linestring))

class SpeedingEvent(Base):
    __tablename__ = 'speeding_events'
    speeding_event_id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.trip_id'))
    
    start_distance_m = Column(Float)
    end_distance_m = Column(Float)
    start_time = Column(BigInteger)
    end_time = Column(BigInteger)
    point = Column(Geometry(geometry_type='POINT', srid=settings.TARGET_PROJECTION))
    end_point = Column(Geometry(geometry_type='POINT', srid=settings.TARGET_PROJECTION))
    line = Column(Geometry(geometry_type='LINESTRING', srid=settings.TARGET_PROJECTION))
    velocity_mph = Column(Float)

    def __init__(self, trip, event, path):
        event = event.copy()
        event['line'] = SpatialQueries.find_line_substring(
            path, 
            event['start_distance_m'],
            event['end_distance_m']
        )
        event['point'] = SpatialQueries.line_start_point(event['line'])
        event['end_point'] = SpatialQueries.line_end_point(event['line'])
        
        super(SpeedingEvent, self).__init__(**event)

    def __repr__(self):
        return "Warning! Based on your driving patterns, " \
            "you are likely to speed within {} meters.".format(settings.ALERT_DISTANCE)

# class BaseBrakeAccelEvent(Base):
#     def __init__(self, trip, event, path):
#         event = event.copy()
#         event['trip'] = session.query(Trip).filter_by(trip_id_string=trip).first()
#         event['point'] = Geometry.convert_geographic_coordinates_to_projected_point(
#             event['lat'], 
#             event['log']
#         )

        
class HardBrakeEvent(Base):
    __tablename__ = 'hard_brake_events'
    hard_brake_event_id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.trip_id'))
    
    lat = Column(Float)
    lon = Column(Float)
    ts = Column(BigInteger)
    g = Column(Float)
    point = Column(Geometry(geometry_type='POINT', srid=settings.TARGET_PROJECTION))

    def __init__(self, trip, event, path):
        event = event.copy()
        
        event['point'] = SpatialQueries.convert_geographic_coordinates_to_projected_point(
            event['lat'], 
            event['lon']
        )
        super(HardBrakeEvent, self).__init__(**event)

    def __repr__(self):
        return "Warning! Based on your driving patterns, " \
            "you are likely to brake hard within {} meters.".format(settings.ALERT_DISTANCE)
        


    
class HardAccelerationEvent(Base):
    __tablename__ = 'hard_acceleration_events'
    hard_accleration_event_id = Column(Integer, primary_key=True)
    trip_id = Column(Integer, ForeignKey('trips.trip_id'))
    
    lat = Column(Float)
    lon = Column(Float)
    ts = Column(BigInteger)
    g = Column(Float)
    point = Column(Geometry(geometry_type='POINT', srid=settings.TARGET_PROJECTION))

    def __init__(self, trip, event, path):
        event = event.copy()
        
        event['point'] = SpatialQueries.convert_geographic_coordinates_to_projected_point(
            event['lat'], 
            event['lon']

        )
        super(HardAccelerationEvent, self).__init__(**event)

    def __repr__(self):
        return "Warning! Based on your driving patterns, " \
            "you are likely to accelerate hard within {} meters.".format(settings.ALERT_DISTANCE)

class SpatialQueries:
    
    @classmethod
    def find_trips_matching_line(cls, line, user_id):
        # use azimuth of last two points to determine if the route
        # is in the right direction
        # maybe use last three points for two azimuths,
        # find some function to find nearest point on trip line
        # so then we have to go third to second in same dir
        # and second to first in same dir

        ## use ST_LineLocatePoint to find the consective points on the line
        ## use ST_OrderingEquals to make sure that they all go in the same dir
        proj_line = cls.points_to_projected_line(line)
        s = session.query(Trip).filter_by(user_id=user_id).filter(func.ST_Within(proj_line, Trip.geom))
        return s
    
    @classmethod
    def get_associated_events(cls, trip):
        events = []
        for event in trip.speeding_events:
            events.append(event)
        for event in trip.hard_acceleration_events:
            events.append(event)
        for event in trip.hard_brake_events:
            events.append(event)
        return events

    @classmethod
    def find_adjacent_events(cls, point, events):
        adjacent_events = []
        for event in events:
            within = session.execute(
                func.ST_DWithin(event.point, 
                                point,
                                settings.ALERT_DISTANCE)).first()[0]
            if within:
                adjacent_events.append(event)
        return adjacent_events

    @classmethod
    def segmentized_line_with_geographic_points(cls, trip_id):
        """ Returns (lat, lon) of geographic coordinate of points every 50m along route.
        Mainly intended for use with testing."""
        s = select([
            func.ST_DumpPoints(func.ST_Transform(func.ST_Segmentize(Trip.geom_path, 50), 
                                                 settings.TARGET_DATUM))\
            .label('dp')
        ]).where(Trip.trip_id == trip_id)
        inner_select = s.correlate(None).alias()
        s = select([
            func.ST_Y(inner_select.columns.dp.geom),
            func.ST_X(inner_select.columns.dp.geom),
        ])
        
        return list(engine.execute(s))
        

    @classmethod
    def adjacent_events_from_point_sequence(cls, point_group, user_id):
        total_adjacent_events = []
        if len(point_group) < 2:
            return total_adjacent_events
        trips_matching_line = cls.find_trips_matching_line(point_group, user_id)
        for matching_trip in trips_matching_line:
            events = cls.get_associated_events(matching_trip)
            proj_point = cls.\
                         convert_geographic_coordinates_to_projected_point(*point_group[-1])
            total_adjacent_events.extend(cls.find_adjacent_events(proj_point, events))
        return total_adjacent_events


    @staticmethod
    def point_to_string(lat, lon):
        return "POINT({} {})".format(lon, lat)
    
    @classmethod
    def convert_geographic_coordinates_to_projected_point(cls, lat, lon):
        point_string = cls.point_to_string(lat, lon)
        return func.ST_Transform(
            func.ST_GeometryFromText(point_string, settings.TARGET_DATUM),
            settings.TARGET_PROJECTION
        )

    @classmethod
    def convert_projected_point_to_geographic_coordinates(cls, point):
        s = select([
            func.ST_Transform(func.ST_WKBToSQL(point), settings.TARGET_DATUM).label('p')
        ])
        inner_select = s.correlate(None).alias()
        s = select([
            func.ST_Y(inner_select.columns.p),
            func.ST_X(inner_select.columns.p),
        ])
        return list(engine.execute(s))[0]
        
    @staticmethod
    def path_to_string(path):
        return ','.join(['{} {}'.format(lon, lat) for lat, lon in path])

    @classmethod
    def construct_linestring_string(cls, srid, path):
        return 'SRID={};LINESTRING({})'.format(srid, cls.path_to_string(path))
    
    @staticmethod
    def find_line_substring(path, start, end):
        length = func.ST_Length(path)
        start_fraction = start / length
        end_fraction = end / length
        return func.ST_LineSubstring(path, start_fraction, end_fraction)

    @staticmethod
    def line_start_point(line):
        return func.ST_StartPoint(line)

    @staticmethod
    def line_end_point(line):
        return func.ST_EndPoint(line)

    @classmethod
    def points_to_projected_line(cls, line):
        return func.ST_Transform(
            func.ST_GeometryFromText(cls.construct_linestring_string(settings.TARGET_DATUM, line)),
            settings.TARGET_PROJECTION
        )
        

    @classmethod
    def dump_points_to_projected_line(cls, line):
        return func.ST_DumpPoints(cls.points_to_projected_line(line))

    @classmethod
    def find_test_point_within_distance(cls, point, line):
        ratio_location_query = func.ST_LineLocatePoint(line, point)
        ratio = list(session.execute(ratio_location_query))[0][0]
        line_length = func.ST_Length(line)
        total_length = list(session.execute(line_length))[0][0]
        distance_on_line = ratio * total_length
        # can move point back as far as the beginning of the line
        # or within the set ALERT_DISTANCE
        allowable_subtraction = min(distance_on_line, settings.ALERT_DISTANCE)
        fraction = random.random()
        new_distance = distance_on_line - (fraction * allowable_subtraction)
        new_point = list(session.execute(
            func.ST_Line_Interpolate_Point(
            line, new_distance/total_length)))[0][0]
        return new_point

    @classmethod
    def find_test_point_outside_distance(cls, point, line):
        ratio_location_query = func.ST_LineLocatePoint(line, point)
        ratio = list(session.execute(ratio_location_query))[0][0]
        line_length = func.ST_Length(line)
        total_length = list(session.execute(line_length))[0][0]
        distance_on_line = ratio * total_length
        if distance_on_line <= settings.ALERT_DISTANCE:
            # can't get a point that is outside tolerance from here
            return None
        # find a point anywhere from beginning of line 
        # to threshold of event
        fraction = 1
        while fraction == 1:
            fraction = random.random()
            
        threshold_distance = distance_on_line - settings.ALERT_DISTANCE
        new_distance = fraction * threshold_distance
        new_point = list(session.execute(
            func.ST_Line_Interpolate_Point(
            line, new_distance/total_length)))[0][0]
        return new_point
        
    
        
