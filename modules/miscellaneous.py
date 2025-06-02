import json
import datetime

import numpy as np
import pandas as pd
import math

from modules.logger import logger

def access_with_handle(env, load_using, exception, place_holder, args=False, must=False, *positional_args, **kwargs):
    try:
        if args:

            return load_using(env, *positional_args, **kwargs)
        else:
            return load_using(env)

    except exception as e:
        if must:
            logger.error(f"The environment: {env} is must. Error: {e}")
            raise Exception(f"Make sure env: {env} is not present. Error: {e}")
        else:
            logger.warning(f"The environment: {env} is not present. Error: {e}")
            return place_holder

def get_column_from_df_as_list(dataframe, column):
    try:
        return dataframe[column].to_list()
    except KeyError as e:
        logger.error(f"column: {column} not present in dataframe: {e}")
        return list()

folder = 'data/meta/metro/dmrc-station-details/'
frequencies = access_with_handle(
    'data/meta/metro/metro_frequencies.csv', pd.read_csv, FileNotFoundError,
    pd.DataFrame(), args=False, must=False
)

stop_name_stop_code_mapping = {'tughlakabad station': 'TKDS', 'rohini sector - 18, 19': 'RISE', 'hauz khas': 'HKS',
                               'jafrabad': 'JFRB', 'pitampura': 'PTP', 'sultanpur': 'SLTP', 'peeragarhi': 'PAGI',
                               'nangli': 'NNGI', 'shastri park': 'SHPK', 'model town': 'MDTW',
                               'neelam chowk ajronda': 'NCAJ', 'palam': 'PALM', 'maujpur-babarpur': 'MUPR',
                               'sadar bazar cantonment': 'SABR', 'lok kalyan marg': 'LKM',
                               'maharaja surajmal stadium': 'SMSM', 'azadpur': 'AZU', 'kohat enclave': 'KE',
                               'sector - 62 noida': 'SSTN', 'kalindi kunj': 'KIKJ', 'qutab minar': 'QM',
                               'mandi house': 'MDHS', 'shankar vihar': 'SKVR', 'bata chowk': 'BACH',
                               'samaypur badli': 'SPBI', 'johri enclave': 'JIEE', 'tagore garden': 'TG',
                               'supreme court': 'PTMD', 'rithala': 'RI', 'sector - 59 noida': 'SFNN',
                               'patel nagar': 'PN', 'terminal 1-igi airport': 'IGDA', 'noida sector-15': 'NSFT',
                               'jln stadium': 'JLNS', 'golf course': 'GEC', 'shaheed sthal ( new bus adda)': 'NBAA',
                               'bhikaji cama place': 'BKCP', 'panchsheel park': 'PSPK', 'chhatarpur': 'CHTP',
                               'tilak nagar': 'TN', 'saket': 'SAKT', 'i.p. extension': 'IPE', 'laxmi nagar': 'LN',
                               'green park': 'GNPK', 'janak puri east': 'JPE', 'vinobapuri': 'VNPR',
                               'ghevra metro station': 'GHEM', 'kaushambi': 'KSHI', 'raj bagh': 'RJBH',
                               'jahangirpuri': 'JGPI', 'raja nahar singh': 'BVHM', 'shahdara': 'SHD',
                               'noida sector-18': 'NSET', 'jasola-apollo': 'JLA', 'trilokpuri-sanjay lake': 'TKPR',
                               'guru teg bahadur nagar': 'GTBR', 'dashrathpuri': 'DSHP', 'udyog bhawan': 'UDB',
                               'netaji subhash place': 'NSHP', 'dwarka sector - 13': 'DSTN',
                               'dwarka sector - 10': 'DST', 'sarai kale khan - nizamuddin': 'NIZM',
                               'sector - 34 noida': 'STFN', 'shiv vihar': 'SVVR', 'viswavidyalaya': 'VW',
                               'dhansa bus stand': 'DNBT', 'tikri border': 'TKBR', 'okhla nsic': 'OKNS',
                               'sector - 52 noida': 'SFTN', 'nhpc chowk': 'NHPC', 'kalkaji mandir': 'KJMD',
                               'huda city centre': 'HCC', 'dabri mor - janakpuri south': 'DBMR', 'nawada': 'NWD',
                               'mandawali - west vinod nagar': 'VNNR', 'iit': 'IIT', 'rajendra place': 'RP',
                               'mayur vihar extension': 'MVE', 'pandit shree ram sharma': 'MIEE',
                               'sector - 61 noida': 'SSON', 'sarai': 'SRAI', 'pulbangash': 'PBGH', 'arthala': 'ATHA',
                               'nirman vihar': 'NV', 'shastri nagar': 'SHT', 'vidhan sabha': 'VS', 'munirka': 'MIRK',
                               'shakurpur': 'SAKP', 'central secretariat': 'CTST', 'vaishali': 'VASI',
                               'guru dronacharya': 'GE', 'jhilmil': 'JLML', 'vasant vihar': 'VTVR',
                               'kailash colony': 'KHCY', 'nangloi': 'NNOI', 'tis hazari': 'TZI', 'jhandewalan': 'JW',
                               'brig. hoshiar singh': 'CIPK', 'welcome': 'WC', 'ito': 'ITO',
                               'jamia milia islamiya': 'JANR', 'chirag delhi': 'CDLI',
                               'durgabai deshmukh south campus': 'DDSC', 'paschim vihar west': 'PVW',
                               'karkarduma': 'KKDA', 'delhi gate': 'DLIG', 'sir m. vishweshwaraiah moti bagh': 'SVMB',
                               'dwarka sector - 9': 'DSN', 'jama masjid': 'JAMD', 'shalimar bagh': 'SMBG',
                               'kashmere gate': 'KG', 'aiims': 'AIIMS', 'preet vihar': 'PTVR', 'jangpura': 'JGPA',
                               'dilshad garden': 'DSG', 'inderlok': 'ILOK', 'mundka industrial area (mia)': 'MIAA',
                               'shadipur': 'SP', 'madipur': 'MAPR', 'karkarduma court': 'KKDC', 'janpath': 'JNPH',
                               'arjan garh': 'AJG', 'rajiv chowk': 'RCK', 'kanhaiya nagar ': 'KN', 'khan market': 'KM',
                               'ashram': 'AHRM', 'dwarka sector - 11': 'DSE', 'rajouri garden': 'RG',
                               'okhla bird sanctuary': 'OKBS', 'rohini west': 'RHW',
                               'new delhi (yellow & airport line)': 'NDI', 'mohan nagar': 'MNGM',
                               'delhi cantt.': 'DLIC', 'sarojini nagar': 'SOJI', 'civil lines': 'CL',
                               'pratap nagar': 'PRA', 'r.k.puram': 'RKPM', 'sukhdev vihar': 'IWNR',
                               'mewala maharajpur': 'MMJR', 'anand vihar isbt': 'AVIT', 'sant surdas (sihi)': 'NCBC',
                               'shaheed nagar': 'SHDN', 'm.g. road': 'MGRO', 'rajdhani park': 'RDPK',
                               'punjabi bagh': 'PBGA', 'botanical garden': 'BCGN', 'keshav puram': 'KP',
                               'new ashok nagar': 'NAGR', 'badkal mor': 'BKMR', 'dwarka mor': 'DM',
                               'uttam nagar west': 'UNW', 'subhash nagar': 'SN', 'lal quila': 'LLQA',
                               'ghitorni': 'GTNI', 'adarsh nagar': 'AHNR', 'chandni chowk': 'CHK',
                               'dilli haat - ina': 'INA', 'ramesh nagar': 'RN', 'patel chowk': 'PTCK',
                               'greater kailash': 'GKEI', 'dwarka': 'DW', 'punjabi bagh west': 'PBGW',
                               'shivaji park': 'SHVP', 'udyog nagar': 'UNRG', 'mayapuri': 'MYPI',
                               'dwarka sector - 12': 'DSW', 'akshardham': 'ASDM', 'iffco chowk': 'IFOC',
                               'sarita vihar': 'STVR', 'nangloi railway station': 'NRSN', 'okhla vihar': 'OVA',
                               'jasola vihar shaheen bagh': 'JLA8', 'nehru place': 'NP', 'seelampur': 'SLAP',
                               'malviya nagar': 'MVNR', 'shyam park': 'SMPK', 'satguru ram singh marg': 'SRSM',
                               'ashok park main': 'APMN', 'major mohit sharma rajendra nagar': 'RJNM',
                               'sikanderpur': 'SKRP', 'govind puri': 'GDPI', 'badarpur border': 'BAPB',
                               'tikri kalan': 'TKLM', 'noida city centre': 'NCC', 'chawri bazar': 'CWBR',
                               'escorts mujesar': 'ECMJ', 'krishna nagar': 'KHNA', 'mayur vihar pocket-1': 'MVPO',
                               'janak puri west': 'JPW', 'esi-basaidarapur': 'ESIH', 'naraina vihar': 'NAVR',
                               'dwarka sector - 14': 'DSFN', 'indraprastha': 'IDPT', 'jor bagh': 'JB',
                               'ramakrishna ashram marg': 'RKAM', 'karol bagh': 'KB', 'noida sector-16': 'NSST',
                               'moolchand': 'MLCD', 'bahadurgarh city': 'BUSS', 'gokulpuri': 'GKPR', 'moti nagar': 'MN',
                               'old faridabad': 'OFDB', 'paschim vihar east': 'PVE', 'lajpat nagar': 'LJPN',
                               'yamuna bank': 'YB', 'noida electronic city': 'NECC', 'majlis park': 'MKPR',
                               'east azad nagar': 'EANR', 'sector-28': 'STTA', 'haiderpur badli mor': 'BIMR',
                               'barakhamba road': 'BRKR', 'east vinod nagar-mayur vihar -ii': 'VENT',
                               'uttam nagar east': 'UNE', 'dwarka sector - 8': 'DSET', 'najafgarh': 'NFGH',
                               'mansarovar park': 'MPK', 'mayur vihar -i': 'MVP1', 'harkesh nagar okhla': 'HNOK',
                               'mundka': 'MUDK', 'dwarka sector - 21': 'DSTO', 'rohini east': 'RHE',
                               'mohan estate': 'METE', 'hindon river': 'HDNR', 'nehru enclave': 'NUEE',
                               'south extension': 'SOEN'}


def get_platform_info_details(station_name, terminal_stop):
    try:
        stop_code = stop_name_stop_code_mapping[station_name.lower()]
    except:
        return None

    with open(folder + f'station_details_{stop_code}.json', 'r') as f:
        resp = json.load(f)
        for p in resp['platforms']:
            if terminal_stop.lower() in p['train_towards']['station_name'].lower():
                return p['platform_name']
    return None


def get_peak_off_peak_category(cur_time):
    if cur_time < 8:
        category = "non_peak_1"
    elif cur_time < 12:
        category = "peak_1"
    elif cur_time < 17:
        category = "non_peak_2"
    elif cur_time < 21:
        category = "peak_2"
    else:
        category = "non_peak_3"
    return category


def get_frequency(route_id, query_time=None):
    if query_time is None:
        query_time = datetime.datetime.now().hour
    else:
        query_time = int(query_time.split(':')[0])
    category = get_peak_off_peak_category(query_time)
    # print(category)
    try:
        return int(frequencies.loc[(frequencies.route_id == route_id) & (frequencies.time_category == category), 'frequency'].squeeze())
    except Exception as e:
        if frequencies.empty:
            logger.error(f"Can not find frequency for route_id: {route_id} and category: {category}, frequency dataframe is empty. {e}")
        else:
            logger.error(f"Can not find frequency for route_id: {route_id} and category: {category}, route_id might not available. {e}")
        return -1


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6367  # Earth's radius in KM

    # print(type(lat1), type(lat2), type(lon1), type(lon2))
    d_lat = np.radians(lat2) - math.radians(lat1)
    d_lon = np.radians(lon2) - math.radians(lon1)

    a = (
            np.sin(d_lat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            np.cos(np.radians(lat2)) *
            np.sin(d_lon / 2) ** 2
    )

    c = 2 * np.arcsin(np.sqrt(a))
    return R * c




if __name__ == '__main__':
    print(get_platform_info_details("Adarsh Nagar", "HUDA CITY CENTRE"))
    print(get_frequency(1, '11:00:04'))
