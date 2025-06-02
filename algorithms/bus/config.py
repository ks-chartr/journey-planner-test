import os
import json
from core.settings import ENV_DIR
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from modules.miscellaneous import access_with_handle, get_column_from_df_as_list

BUS_MODE_ENV = os.getenv("BUS_MODE")
BUS_MUST = False
if BUS_MODE_ENV:
    BUS_MUST = True

BUS_ENV_PATH = os.path.join(ENV_DIR, ".env.module.bus.dev")
load_dotenv(BUS_ENV_PATH)

# Used variables
# Get the environment variables
ZERO_HOP_DB_PATH = os.getenv("ZERO_HOP_DB_PATH")
BUS_TIME_TABLE_DETAILS_DB_PATH = os.getenv("BUS_TIME_TABLE_DETAILS_DB_PATH")
BUS_SCHEDULE_DB_PATH = os.getenv("BUS_SCHEDULE_DB_PATH")
BUS_GRAPH_PATH = os.getenv("BUS_GRAPH_PATH")

ROUTE_STOP_DICT_PATH = os.getenv("ROUTE_STOP_DICT_PATH")
WALK_DISTANCE_DETAILS_PATH = os.getenv("WALK_DISTANCE_DETAILS_PATH")
STOPS_IN_ROUTE_LIST_PATH = os.getenv("STOPS_IN_ROUTE_LIST_PATH")
BUS_ROUTES_DATA_PATH = os.getenv("BUS_ROUTES_DATA_PATH")
CLUSTER_DETAILS_PATH = os.getenv("CLUSTER_DETAILS_PATH")
BUS_STOPS_PATH = os.getenv("BUS_STOPS_PATH")
UPDATED_FREQ_OCT_PATH = os.getenv("UPDATED_FREQ_OCT_PATH")
UPDATED_BUS_ROUTES_DATA_PATH = os.getenv("UPDATED_BUS_ROUTES_DATA_PATH")
BUS_ROUTES_DETAILS_DATA_PATH = os.getenv("BUS_ROUTES_DETAILS_DATA_PATH")
MAPPED_BUS_STOPS = os.getenv("MAPPED_BUS_STOPS")

BUS_STOPS_DATA_PATH = os.getenv("BUS_STOPS_DATA_PATH")


# Load the value of the variable
ROUTE_STOP_DICT = access_with_handle(ROUTE_STOP_DICT_PATH, np.load, FileNotFoundError, place_holder=None, args=True, must=BUS_MUST, allow_pickle=True).item()
WALK_DISTANCE_DETAILS = access_with_handle(WALK_DISTANCE_DETAILS_PATH, np.load, FileNotFoundError, place_holder=None, args=True, must=BUS_MUST, allow_pickle=True).item()
BUS_GRAPH = access_with_handle(BUS_GRAPH_PATH, np.load, FileNotFoundError, place_holder=None, args=True, must=BUS_MUST, allow_pickle=True)
STOPS_IN_ROUTE_LIST = access_with_handle(STOPS_IN_ROUTE_LIST_PATH, np.load, FileNotFoundError, place_holder=None, args=True, must=BUS_MUST, allow_pickle=True).item()
BUS_ROUTES_DF = access_with_handle(BUS_ROUTES_DATA_PATH, pd.read_csv, FileNotFoundError, place_holder=None, args=False, must=BUS_MUST)
CLUSTER_DETAILS = access_with_handle(CLUSTER_DETAILS_PATH, np.load, FileNotFoundError, place_holder=None, args=True, must=BUS_MUST, allow_pickle=True).item()
BUS_STOPS_DF = access_with_handle(BUS_STOPS_PATH, pd.read_csv, FileNotFoundError, place_holder=None, args=False, must=BUS_MUST)
UPDATED_BUS_ROUTES_DF = access_with_handle(UPDATED_BUS_ROUTES_DATA_PATH, pd.read_csv, FileNotFoundError, place_holder=None, args=False, must=BUS_MUST)

BUS_STOPS_DATA = pd.read_csv(BUS_STOPS_DATA_PATH)

# Used in common/core.py
# Get the environment variables
METRO_TO_BUS_DICT_FILE_PATH = os.getenv("METRO_TO_BUS_DICT_FILE_PATH")
BUS_TO_METRO_DICT_FILE_PATH = os.getenv("BUS_TO_METRO_DICT_FILE_PATH")
CLUSTERED_STOPS_CSV_FILE_PATH = os.getenv("CLUSTERED_STOPS_CSV_FILE_PATH")

# Load the value of the variable
METRO_TO_BUS_DICT = access_with_handle(METRO_TO_BUS_DICT_FILE_PATH, np.load, FileNotFoundError, place_holder=dict(), args=True, must=BUS_MUST, allow_pickle=True).item()
BUS_TO_METRO_DICT = access_with_handle(BUS_TO_METRO_DICT_FILE_PATH, np.load, FileNotFoundError, place_holder=dict(), args=True, must=BUS_MUST, allow_pickle=True).item()

# Environment variables for Metro PTX API
BUS_PTX_GRAPH_PATH = os.getenv("BUS_PTX_GRAPH_PATH")
PTX_ROUTES_FILE_PATH = os.getenv("BUS_PTX_ROUTES_FILE_PATH")
