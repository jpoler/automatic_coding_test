import random


from sqlalchemy import func

from geoalchemy2 import Geometry

from geoalchemy2.functions import GenericFunction
from engine import engine, session

from sqlalchemy.sql import select

import settings

class ST_GeometryFromWKB(GenericFunction):
    name = 'ST_GeometryFromWKB'
    type = Geometry


class ST_AsText(GenericFunction):
    name = 'ST_AsText'
    type = Geometry

