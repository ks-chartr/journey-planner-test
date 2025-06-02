import datetime
import os
import sqlite3
import warnings

import pandas as pd
from tqdm import tqdm

from core.settings import BASE_DIR

warnings.filterwarnings('ignore')

DIRECTOY_ADDRESS_OF_DATA = os.path.join(BASE_DIR, 'data')

dimts_duty_master = pd.read_csv(os.path.join(DIRECTOY_ADDRESS_OF_DATA + '/meta/dimts_trips_master.csv'))
schedule_master = sqlite3.connect(f'file:{DIRECTOY_ADDRESS_OF_DATA}/meta/schedule_master.db?mode=ro', uri=True,
                                  check_same_thread=False)
current_schedule = sqlite3.connect(f'file:{DIRECTOY_ADDRESS_OF_DATA}/meta/schedule.db', uri=True,
                                   check_same_thread=False)
duties_df = pd.DataFrame()
delhi_fleet = pd.read_csv(f'{DIRECTOY_ADDRESS_OF_DATA}/meta/delhi_fleet.csv')
routes_df = pd.read_csv(f'{DIRECTOY_ADDRESS_OF_DATA}/GTFS/bus/routes.txt')

delhi_fleet_dict = delhi_fleet.set_index('vehicle_id').T.to_dict('list')
bus_schedule_df = pd.read_csv(f'{DIRECTOY_ADDRESS_OF_DATA}/meta/bus_schedule.csv')
static_schedule = sqlite3.connect(f'file:{DIRECTOY_ADDRESS_OF_DATA}/meta/schedule.db?mode=ro', uri=True,
                                  check_same_thread=False)


def get_duties():
    global duties_df
    duties_df = pd.read_csv('http://143.110.182.192:8090/depot_tool_duty_master.txt')


def get_route_stop_times(route_id):
    query = f'select * from bus_schedule where route_id = {route_id}'
    df = pd.read_sql_query(query, schedule_master)
    return df


def get_updated_stop_times(df, starting_time):
    # print(df)
    start_time = pd.to_datetime(starting_time)
    df['arrival_time'] = (start_time + pd.to_timedelta(df['time_difference_seconds'], unit='s')).apply(
        lambda x: x.strftime('%H:%M:%S'))
    df['departure_time'] = (start_time + pd.to_timedelta(df['time_difference_seconds'], unit='s')).apply(
        lambda x: x.strftime('%H:%M:%S'))
    return df


def get_gtfs_route(duties_df):
    # CL | UP | DOWN | DN |
    duties_df['Route No.'] = duties_df['Route No.'].str.upper()
    duties_df['Route No.'] = duties_df['Route No.'].str.replace("CL|_C", "", regex=True)
    duties_df["Route No."] = duties_df['Route No.'].str.replace("_G|\.| |_|(P[0-9]*)|L$", "", regex=True)
    duties_df["Route No."] = duties_df['Route No.'].str.replace("(U$)", "UP", regex=True)
    duties_df["Route No."] = duties_df['Route No.'].str.replace("(D$)|(DN$)|DDOWN|DOWM", "DOWN", regex=True)
    duties_df["Route No."] = duties_df['Route No.'].str.replace("MS\(+\)$", "MS(+)UP", regex=True)
    duties_df["Route No."] = duties_df['Route No.'].str.replace("MS\(-\)$", "MS(-)DOWN", regex=True)

    return duties_df


def updated_duties_db(duties_df):
    duties_df = pd.merge(duties_df, delhi_fleet[['vehicle_id', 'agency']], left_on='Plate No.', right_on='vehicle_id',
                         how='left')

    routes_df['agency_id'] = routes_df['agency_id'].str.lower()
    duties_df['agency'] = duties_df['agency'].str.lower()
    duties_df['modified_route'] = duties_df['Route No.'].str.replace(r'(UP|DOWN)$', r'CL\1')
    duties_df['modified_route'] = duties_df['modified_route'].str.replace(r'-', '')

    merged_df = pd.merge(duties_df, routes_df[['route_long_name', 'agency_id', 'route_id']],
                         left_on=['Route No.', 'agency'],
                         right_on=['route_long_name', 'agency_id'], how='left')
    merged_df.agency_id = merged_df.agency
    nan_df = merged_df[merged_df.route_id.isna()]
    final_merged_df = pd.merge(nan_df, routes_df[['route_long_name', 'agency_id', 'route_id']],
                               left_on=['modified_route', 'agency_id'],
                               right_on=['route_long_name', 'agency_id'], how='left')
    final_merged_df = final_merged_df.drop(['route_id_x', 'route_long_name_x'], axis=1)
    final_merged_df = final_merged_df.dropna(subset=['route_id_y'])
    final_merged_df.rename(columns={'Duty ID': 'Duty ID', 'Plate No.': 'Plate No.', 'Route No.': 'Route No.',
                                    'Trip End Time': 'Trip End Time', 'Trip Number': 'Trip Number',
                                    'Trip Start Time': 'Trip Start Time', 'Shift Id': 'Shift Id',
                                    'vehicle_id': 'vehicle_id', 'agency': 'agency', 'modified_route': 'modified_route',
                                    'route_long_name_y': 'route_long_name', 'agency_id': 'agency_id',
                                    'route_id_y': 'route_id'}, inplace=True)
    duties_df = pd.concat([merged_df, final_merged_df])
    duties_df = duties_df.dropna(subset=['route_id'])
    duties_df['route_id'].fillna(-1, inplace=True)
    duties_df['route_id'] = duties_df['route_id'].astype(int)
    duties_df.drop(columns=['agency_id', 'modified_route'], inplace=True)

    return duties_df


def driver_code():
    global duties_df
    get_duties()
    get_gtfs_route()
    updated_duties_db()
    df = pd.DataFrame()
    start = datetime.datetime.now()
    for i, duty in enumerate(duties_df.itertuples()):
        try:
            route_id = duty[11]
            if route_id != -1:
                stop_times = bus_schedule_df[bus_schedule_df.route_id == route_id]
                # stop_times = get_route_stop_times(route_id)
            else:
                print(f"{duty[3]} not found.")
                continue
            if stop_times.size != 0:
                if df.size == 0:
                    df = get_updated_stop_times(stop_times, duty[6])
                else:
                    df = pd.concat([df, get_updated_stop_times(stop_times, duty[6])], ignore_index=True)
                # break
            else:
                print(f"{duty[3]} stop times not found.")
                continue
        except:
            print(f"{duty[2], duty[3]} not found.")
        if i % 1000 == 0:
            df.to_sql('bus_schedule', current_schedule, if_exists='append', index=False)
            print('Inserted 1000 values')
            df = pd.DataFrame()
    try:
        df.to_sql('bus_schedule', current_schedule, if_exists='append', index=False)
        # current_schedule.commit()
    except sqlite3.Error as e:
        print("SQLite error:", e)


def get_count():
    cursor = current_schedule.cursor()
    count_query = "SELECT COUNT(*) FROM bus_schedule"
    try:
        cursor.execute(count_query)
        result = cursor.fetchone()
        row_count = result[0]
    except:
        row_count = 0
    cursor.close()
    return row_count


def copy_static_if_empty():
    source_cursor = static_schedule.cursor()
    target_cursor = current_schedule.cursor()
    source_cursor.execute(f'SELECT * FROM bus_schedule')
    first_row = source_cursor.fetchone()
    if first_row is not None:
        column_info = ", ".join([f"{col[0]} {col[1]}" for col in source_cursor.description])
        create_table_query = f'CREATE TABLE IF NOT EXISTS bus_schedule ({column_info})'
        target_cursor.execute(create_table_query)
        current_schedule.commit()
    while True:
        row = source_cursor.fetchone()
        if row is None:
            break
        target_cursor.execute(f'INSERT INTO bus_schedule VALUES (?, ?, ?)', row)

    # Step 6: Commit the changes to the target database
    current_schedule.commit()
    source_cursor.close()
    target_cursor.close()


def get_duties_from_duty_master():
    failed = 0
    try:
        duties_df = pd.read_csv('http://143.110.182.192:8090/depot_tool_duty_master.txt')
    except:
        failed = 1
        duties_df = pd.DataFrame()
    duties_df = pd.concat([duties_df, dimts_duty_master], ignore_index=True, sort=False)
    if failed == 0 and len(duties_df) == 0:
        failed = 1
    if failed == 0:
        duties_df = get_gtfs_route(duties_df)
        duties_df = updated_duties_db(duties_df)
        df = pd.DataFrame()
        start = datetime.datetime.now()
        cursor = current_schedule.cursor()
        try:
            cursor.execute('DELETE FROM bus_schedule')
            cursor.execute(
                'CREATE INDEX "ix_route_id_departure_time_stop_id" ON "bus_schedule" ("route_id", "departure_time", "stop_id")')
        except:
            pass
        current_schedule.commit()
        for i, duty in tqdm(enumerate(duties_df.itertuples())):
            # print(f'Currently at {i}')
            try:
                route_id = duty.route_id
                if route_id != -1:
                    stop_times = bus_schedule_df[bus_schedule_df.route_id == route_id]
                    # stop_times = get_route_stop_times(route_id)
                else:
                    print(f"{duty[3]} not found.")
                    continue
                if stop_times.size != 0:
                    if df.size == 0:
                        df = get_updated_stop_times(stop_times, duty[6])
                    else:
                        df = pd.concat([df, get_updated_stop_times(stop_times, duty[6])], ignore_index=True)
                    # break
                else:
                    print(f"{duty[3]} stop times not found.")
                    continue
            except Exception as e:
                print(f"{duty[2], duty[3]} not found.")
            if i % 1000 == 0:
                print(f'size : {len(df)}')
                df.to_sql('bus_schedule', current_schedule, if_exists='append', index=False)
                print('Inserted 1000 values')
                df = pd.DataFrame()
        try:
            df.to_sql('bus_schedule', current_schedule, if_exists='append', index=False)
            # current_schedule.commit()
        except sqlite3.Error as e:
            print("SQLite error:", e)
    else:
        prev_duty_count = get_count()
        if prev_duty_count == 0:
            print('No previous duty found. Copying static schedule...')
            copy_static_if_empty()


# if __name__ == '__main__':
#     # drop_same_route_values()
#     start = datetime.datetime.now()
#     driver_code()
#     print(f'Took {(datetime.datetime.now() - start).total_seconds()}s for {len(duties_df)} rows.')
#     pass


# if __name__ == '__main__':
#     while True:
#         get_duties_from_duty_master()
#         time.sleep(6000)

if __name__ == '__main__':
    get_duties_from_duty_master()
