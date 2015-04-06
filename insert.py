from engine import engine, session
from models import User, Trip, SpeedingEvent, HardBrakeEvent, HardAccelerationEvent
import settings

class DatabaseManager(object):
    engine = engine
    session = session
    
    @classmethod
    def clear_database_and_create_tables(cls):
        HardBrakeEvent.__table__.drop(engine, checkfirst=True)
        HardAccelerationEvent.__table__.drop(engine, checkfirst=True)
        SpeedingEvent.__table__.drop(engine, checkfirst=True)
        Trip.__table__.drop(engine, checkfirst=True)
        User.__table__.drop(engine, checkfirst=True)
        User.__table__.create(engine)
        Trip.__table__.create(engine)
        SpeedingEvent.__table__.create(engine)
        HardAccelerationEvent.__table__.create(engine)
        HardBrakeEvent.__table__.create(engine)

    @classmethod
    def insert_json_into_db(cls, username, json):
        user = cls.session.query(User).filter_by(username=username).first()
        user.trips.extend([Trip(trip=trip, srid=settings.TARGET_DATUM) for trip in json 
                           if len(trip['path']) > 1])
        cls.session.commit()
        
    
    @classmethod
    def create_new_user(cls, username=None):
        if not username is None:
            user = User(username=username)
            cls.session.add(user)
            cls.session.commit()
