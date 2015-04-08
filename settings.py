import os

DATAPATH = 'data1'
TARGET_PROJECTION = 26910 # UTM Zone 10 (Western portion of California)
TARGET_DATUM = 4326
MAX_GPS_ERROR_TOLERANCE = 20 # in meters, arbitrary choice
ALERT_DISTANCE = 200 # in meters, also arbitrary
USERNAME = os.environ['AUTOMATIC_TEST_USERNAME']
OS_USERNAME = 'jdp'
SERVER_IP = os.environ['JPOLER_SERVER_IP']
PORT = 5000

