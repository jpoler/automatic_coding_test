# README #

### Overview ###

#### What does this repo do? ####

Using Automatic's REST API to gather trip data for a hypothetical user, this project provides a REST endpoint which an application can place a GET request to with a json object in the parameters. This object will hold the last few points along the current User's trip. This current location data will be checked against the User's past trip history, which will be searched to generate useful warnings about disadvantageous driving behavior. For instance, after placing a GET request to this endpoint containing the three most recent points along the current trip, the endpoint can return a json object which displays errors such as "Warning, you are within 200 Meters of a place where you have sped before." The same applies for hard acceleration events and hard braking events.

This is currently implemented by searching for buffered paths (to account for GPS error) that contain the points of the current trip. Each path that is found may or may not have a number of events associated with it (speeding, hard acceleration, hard braking). These events are checked for close proximity to the last point that was posted to the endpoint (assumed to be the User's current location). If any events are within the distance threshold, those events are used to generate warning messages, which are returned in a json object.

### Summary of set-up ###

1. Install Postgres:

    http://www.postgresql.org/download/

    On *nix-based systems, it's probably best to use your package manager

    You may want to create a PostgreSQL user that matches your OS username:

    http://www.postgresql.org/docs/9.4/static/app-createuser.htm



2. Install PostGIS

    http://postgis.net/install/

    Once again, try to favor use of a package manager on *nix systems.

3. Create a database

    http://www.postgresql.org/docs/9.4/static/manage-ag-createdb.html

    Look near the bottom of the above page, and issue the command that specifies the correct owner.

    Now, after you have created the database, issue the following commands

        $ psql <DATABASE_NAME>
        > CREATE EXTENSION postgis;
        > CREATE EXTENSION postgis_topology;

    Don't worry about the other extensions, they are not needed for this project.


4. Install Python 2.7 (Because of Flask's flaky support for Python3)

    This may be done for you depending on your system:

    https://www.python.org/downloads/release/python-279/


5. Install virtualenv

    Try this on *nix:

        sudo pip install virtualenv

    Or resort to this:

    https://virtualenv.pypa.io/en/latest/installation.html

6. Create a virtual environment

    The path to your Python executable may be different than mine (specified by '-p /usr/bin/python2.7')

        cd /path/to/this/repo
        virtualenv -p /usr/bin/python2.7 env
        . env/bin/activate

7. Install third-party dependencies

        pip install -r requirements.txt
        
8. Create an environmental variable for automatic api username
    
    You'll need access to the username provided by Automatic for this coding test. create an environmental variable in your .bashrc (or shell of choice).

        export AUTOMATIC_TEST_USERNAME=<USERNAME>
        
9. Go to settings.py and change the OS_USERNAME to the username that will access the Postgres database

10. Run tests!

        python test_db.py
        python test_endpoint.py

### TODO ###

Please see todo in the root directory of this repo for the current roadmap,
