from dotenv import load_dotenv
import os
from core.settings import ENV_DIR
import pandas as pd

NCRTC_ENV_PATH = os.path.join(ENV_DIR, ".env.module.ncrtc.dev")
load_dotenv(NCRTC_ENV_PATH)

NCRTC_SCHEDULE_DB_PATH = os.getenv("NCRTC_SCHEDULE_DB_PATH")
NCRTC_RESPONSE_DB_PATH = os.getenv("NCRTC_RESPONSE_DB_PATH")
NCRTC_STOPS_PATH = os.getenv("NCRTC_STOPS_PATH")
NCRTC_ROUTES_PATH = os.getenv("NCRTC_ROUTES_PATH")


NCRTC_STOPS_DF = pd.read_csv(NCRTC_STOPS_PATH)
NCRTC_ROUTES_DF = pd.read_csv(NCRTC_ROUTES_PATH)
NCRTC_ROUTES_DF['idx'] = NCRTC_ROUTES_DF.loc[:, 'route_id']
NCRTC_ROUTES_DICT = NCRTC_ROUTES_DF[['idx', 'route_short_name', 'route_long_name', 'route_type', 'route_id']].set_index(
    'idx').T.to_dict('list')
del NCRTC_ROUTES_DF

