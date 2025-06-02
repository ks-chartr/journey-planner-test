import datetime
import time
import os
import pandas as pd
import requests
from core.settings import BASE_DIR
import warnings

warnings.filterwarnings('ignore')

'''
1. import pis data
2. iterate bus by bus
    2.1 match subseq with GTFS
    2.2 if matched, follow below loop 
'''

DIRECTOY_ADDRESS_OF_DATA = os.path.join(BASE_DIR, 'data')
print(DIRECTOY_ADDRESS_OF_DATA)


def update():
    """Function:
        def update():
            Updates the bus data in the given csv file.
            Parameters:
                - None
            Returns:
                - None
            Processing Logic:
                - Fetches the bus data from the given url.
                - Converts the data into a dataframe.
                - Filters out any negative estimated time of arrival.
                - Saves the dataframe as a csv file."""
    file_path = '/meta/bus/rt_data.csv'
    filename = DIRECTOY_ADDRESS_OF_DATA + file_path

    start = datetime.datetime.now()
    print('STARTING FETCH at', start)
    try:
        d = requests.get('https://pis.chartr.in/all_rt_buses_data').json()
        df = pd.DataFrame(d)
        df = df[df.eta >= 0]
        df.to_csv(filename)
    except Exception as e:
        print(e)
        return

    print('CREATED after ', (datetime.datetime.now() - start).total_seconds())


if __name__ == '__main__':
    update()
    # while True:
    #     update()
    #     time.sleep(1 * 60)
    #
