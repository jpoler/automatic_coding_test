from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import settings

engine = create_engine('postgresql://{user}@localhost/automatic_test'.format(user=settings.OS_USERNAME)
                       , echo=False)
Session = sessionmaker(bind=engine)
session = Session()
