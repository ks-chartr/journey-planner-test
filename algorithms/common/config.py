from dotenv import load_dotenv
import os
from core.settings import ENV_DIR
import pandas as pd

COMMON_ENV_PATH = os.path.join(ENV_DIR, ".env.module.common.dev")
load_dotenv(COMMON_ENV_PATH)

ALL_STOPS_PATH = os.getenv("ALL_STOPS_PATH")
ALL_STOPS_DF = pd.read_csv(ALL_STOPS_PATH)

PARK_N_RIDE_REQUEST_URL = os.getenv("PARK_N_RIDE_REQUEST_URL")

if __name__ == "__main__":
    ALL_STOPS_DF = pd.read_csv(ALL_STOPS_PATH)
    print(ALL_STOPS_DF)
