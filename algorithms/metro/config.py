from dotenv import load_dotenv
import os
from core.settings import ENV_DIR
import pandas as pd
import numpy as np
from modules.miscellaneous import access_with_handle

METRO_MODE_ENV = os.getenv("METRO_MODE")
METRO_MUST = False
if METRO_MODE_ENV:
    METRO_MUST = True

METRO_ENV_PATH = os.path.join(ENV_DIR, ".env.module.metro.dev")
load_dotenv(METRO_ENV_PATH)

METRO_SCHEDULE_DB_PATH = os.getenv("METRO_SCHEDULE_DB_PATH")
METRO_RESPONSE_DB_PATH = os.getenv("METRO_RESPONSE_DB_PATH")
METRO_FARE_FILE_PATH = os.getenv("METRO_FARE_FILE_PATH")
METRO_STOPS_PATH = os.getenv("METRO_STOPS_PATH")
METRO_ROUTES_PATH = os.getenv("METRO_ROUTES_PATH")
STOP_SEQUENCE_FILE_PATH = os.getenv("STOP_SEQUENCE_FILE_PATH")


METRO_STOPS_DF = access_with_handle(METRO_STOPS_PATH, pd.read_csv, FileNotFoundError, place_holder=pd.DataFrame(), args=False, must=METRO_MUST)
METRO_FARE_LIST = access_with_handle(METRO_FARE_FILE_PATH, np.load, FileNotFoundError, place_holder=np.array(dict()), args=True, must=False, allow_pickle=True).item()
METRO_ROUTES_DF = access_with_handle(METRO_ROUTES_PATH, pd.read_csv, FileNotFoundError, place_holder=None, args=False, must=METRO_MUST)

if METRO_STOPS_DF.empty:
    METRO_ROUTES_DICT = dict()
else:
    METRO_ROUTES_DF['idx'] = METRO_ROUTES_DF.loc[:, 'route_id']
    METRO_ROUTES_DICT = METRO_ROUTES_DF[['idx', 'route_short_name', 'route_long_name', 'route_type', 'route_id']].set_index(
        'idx').T.to_dict('list')
del METRO_ROUTES_DF

