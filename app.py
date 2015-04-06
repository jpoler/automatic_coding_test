from flask import Flask, request, json, abort, jsonify

from sqlalchemy.sql import select

from engine import engine, session
from models import User
from models import SpatialQueries as SQ

app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_access_denied(error):
    response = jsonify(error);
    response.status_code = error.status_code
    return response

@app.route('/alerts/<username>', methods=['GET'])
def alerts(username):
    '''This controller will recieve a url with a username and a json object as a parameter.
    
    Args:
      username (str): A username which will be validated in the database.
    
    Returns:
      str: A serialized json object if successful, otherwise a json object with an error message

      On success, the json object will contain a list of relevant warnings based on
        proximity to the user.
    '''
    s = select([User.user_id]).where(User.username == username)
    user_id = engine.execute(s).scalar()
    if user_id is None:
        raise InvalidUsage('Please try again with a valid username', status_code=403)

    
    json_unicode = request.args.get('json')
    if json_unicode is None:
        # test this!!!
        raise InvalidUsage('A json parameter is required', 400)
    try:
        json_object = json.loads(json_unicode)
    except:
        raise InvalidUsage('Error: malformed json object', 400)
    points = json_object.get('points')
    if points is None:
        # this too!
        raise InvalidUsage('json must contain a points list', 400)

    
    events = SQ.adjacent_events_from_point_sequence(points, user_id)
    return_events = [str(event) for event in events]
    return jsonify(**dict(warnings=return_events))
    
if __name__ == '__main__':
    app.run(debug=True)
