import datetime
import time
import pytz
from pytz import timezone
import re

INDIAN_TZ = 'Asia/Kolkata'
IST = pytz.timezone('Asia/Kolkata')


def get_current_datetime_tz_aware():
    tz = pytz.timezone(INDIAN_TZ)
    return datetime.datetime.now(tz)


def get_current_datetime():
    return datetime.datetime.now(IST)


def get_current_time_as_str():
    return time.strftime("%H:%M:%S", time.localtime())


def get_current_time_as_str_hhmmss():
    return time.strftime("%H%M%S", time.localtime())


def get_current_datetime_as_str():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# '%H:%M:%S' to datetime
def get_time_from_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%H:%M:%S")


# '%Y-%m-%d %H:%M:%S' to datetime with tzinfo as Asia/Kolkata
def get_ist_datetime_from_naive_dt_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").astimezone(timezone('Asia/Kolkata'))


def get_ist_datetime_obj_from_naive_dt_obj(dt_obj):
    return dt_obj.astimezone(timezone('Asia/Kolkata'))


# '%Y-%m-%d %H:%M:%S' to datetime
def get_datetime_from_str(dt_str):
    return datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def get_utc_timestamp_given_datetime(date):
    """
    :param date: local datetime
    :return: returns utc timestamp corresponding to above
    """
    tz_ist = pytz.timezone("Asia/Kolkata")
    aware_d = tz_ist.localize(date, is_dst=False)
    utc_d = aware_d.astimezone(pytz.utc)
    return utc_d.timestamp()


def get_utc_to_ist_datetime(datetime_obj):
    _ist_datetime_obj = datetime_obj.astimezone(timezone('Asia/Kolkata'))
    _ist_datetime_obj_wo_t = datetime.datetime.strftime(
        _ist_datetime_obj, "%Y-%m-%dT%H:%M:%S"
    ).replace("T", " ")

    return _ist_datetime_obj_wo_t


# x=hour of next day
def get_next_day_x_time(x=3):
    today_ist = datetime.datetime.now(IST)
    tomorrow_ist = today_ist + datetime.timedelta(days=1)
    tomorrow_ist_3am = tomorrow_ist.replace(hour=x, minute=0, second=0)
    # tomorrow_ist_3am_wo_T = datetime.datetime.strftime(
    #     tomorrow_ist_3am, "%Y-%m-%dT%H:%M:%S"
    # ).replace("T", " ")

    # print("IST in Default Format wo T: ", tomorrow_ist_3am_wo_T)
    return tomorrow_ist_3am


def get_current_time_in_milli():
    return round(time.time() * 1000)


def get_ist_time_given_epoch_time(epoch_time):
    dt = datetime.datetime.fromtimestamp(epoch_time, IST)
    return dt


def get_previous_hour_sd_ed():
    """
        return previous hour's start datetime and end datetime
        returns two vars
    """
    last_hour_date_time = get_current_datetime() - datetime.timedelta(hours=1)
    # set minute and second to 00,00
    last_hour_date_time = last_hour_date_time.replace(minute=00, second=0, microsecond=0)
    last_hour_date_time_plus_one = last_hour_date_time + datetime.timedelta(hours=1)

    assert (last_hour_date_time_plus_one - last_hour_date_time).total_seconds() == 3600
    return last_hour_date_time, last_hour_date_time_plus_one


def get_previous_timerange_sd_ed(_timedelta=300, _offset=60):
    # args in seconds
    """
        return previous timerange,
        with endtime offset by _offset
        and gap between two ranges as _timedelta
        returns two vars

        :_timedelta in seconds
        :_offset in seconds
    """
    end_date_time = get_current_datetime() - datetime.timedelta(seconds=_offset)
    # set minute and second to 00,00
    # last_hour_date_time = end_date_time.replace(minute=00, second=0, microsecond=0)
    start_date_time = end_date_time - datetime.timedelta(seconds=_timedelta)
    return start_date_time, end_date_time


def get_next_timerange_sd_ed(_timedelta=300, _offset=60):
    # args in seconds
    """
        return previous timerange,
        with endtime offset by _offset
        and gap between two ranges as _timedelta
        returns two vars
    """
    end_date_time = get_current_datetime() + datetime.timedelta(seconds=_offset)
    # set minute and second to 00,00
    # last_hour_date_time = end_date_time.replace(minute=00, second=0, microsecond=0)
    start_date_time = end_date_time - datetime.timedelta(seconds=_timedelta)
    return start_date_time, end_date_time


def get_current_hour_sd_ed():
    """
        return current hour's start datetime and end datetime
        returns two vars
    """
    this_hour_date_time = get_current_datetime()
    # set minute and second to 00,00
    this_hour_date_time = this_hour_date_time.replace(minute=00, second=0, microsecond=0)
    this_hour_date_time_plus_one = this_hour_date_time + datetime.timedelta(hours=1)

    assert (this_hour_date_time_plus_one - this_hour_date_time).total_seconds() == 3600
    return this_hour_date_time, this_hour_date_time_plus_one


def get_today_sd_ed():
    """
        return previous day's start datetime and end datetime
        returns two vars
    """
    dt = datetime.date.today()
    today_datetime_min = IST.localize(datetime.datetime.combine(dt, datetime.datetime.min.time()))
    today_datetime_max = IST.localize(datetime.datetime.combine(dt, datetime.datetime.max.time()))
    # timezone.localize(today_datetime_min)
    return today_datetime_min, today_datetime_max


def get_yesterday_sd_ed():
    """
        return previous day's start datetime and end datetime
        returns two vars
    """
    last_day_date_time = get_current_datetime() - datetime.timedelta(days=1)
    # set minute and second to 00,00
    last_day_date_time = last_day_date_time.replace(hour=0, minute=00, second=0, microsecond=0)
    last_day_date_time_plus_one = last_day_date_time + datetime.timedelta(days=1)

    assert (last_day_date_time_plus_one - last_day_date_time).total_seconds() == 86400
    return last_day_date_time, last_day_date_time_plus_one


def subtract_times(t1, t2):
    datetime1 = datetime.datetime.strptime(t1, "%H:%M:%S")
    datetime2 = datetime.datetime.strptime(t2, "%H:%M:%S")

    time_diff = datetime1 - datetime2

    # Convert the time difference to seconds
    time_diff_seconds = time_diff.total_seconds()

    return time_diff_seconds


def add_times(t1, t1_min):
    datetime1 = datetime.datetime.strptime(t1, "%H:%M:%S")
    time_delta = datetime.timedelta(minutes=t1_min)

    time_sum = datetime1 + time_delta

    return datetime.datetime.strftime(time_sum, "%H:%M:%S")


class DurationInSeconds:
    ONE_DAY = 86400
    ONE_HOUR = 3600
    ONE_MINUTE = 60


def convert_to_24h(time_str):
    # define a regular expression to match different time formats
    # the expression has four groups: hour, minute, second, and am/pm indicator
    # the second and fourth groups are optional
    time_regex = r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?:\s*(AM|PM))?'

    # try to match the input string with the regular expression
    match = re.match(time_regex, time_str, re.IGNORECASE)

    # if there is a match, extract the groups and convert them to integers
    if match:
        hour, minute, second, am_pm = match.groups()
        hour = int(hour)
        minute = int(minute)
        second = int(second) if second else 0  # if second is None, use 0 as default
        am_pm = am_pm.upper() if am_pm else None  # if am_pm is None, use None as default

        # if the input string has an am/pm indicator, use the 12-hour format to parse it
        if am_pm:
            time_obj = datetime.datetime.strptime(f'{hour}:{minute}:{second} {am_pm}', '%I:%M:%S %p')
        # otherwise, use the 24-hour format to parse it
        else:
            time_obj = datetime.datetime.strptime(f'{hour}:{minute}:{second}', '%H:%M:%S')

        # format the datetime object using the 24-hour format
        time_24 = time_obj.strftime('%H:%M:%S')

        # return the converted time string
        return time_24

    # if there is no match, raise an exception
    else:
        raise ValueError('Invalid time format')


if __name__ == "__main__":
    # print(get_next_day_x_time(3))
    # print(get_current_time_in_milli())
    # dt = get_datetime_from_str("2021-06-13 23:59:59")
    # pt = get_ist_datetime_from_naive_dt_str("2021-06-13 11:59:59")
    # validTill = datetime.datetime(pt.year, pt.month, pt.day, 23, 59, 59, tzinfo=IST)
    #
    # validTill2 = get_utc_to_ist_datetime(validTill)
    #
    # epoch_time = int(1636987551121) / 1000.0
    # dt = get_ist_time_given_epoch_time(epoch_time)
    # print(dt.strftime('%Y-%m-%d %H:%M:%S %Z%z'))
    # print(get_today_sd_ed())
    # print(get_yesterday_sd_ed())
    # print(get_next_timerange_sd_ed(90, 0))
    print(get_previous_timerange_sd_ed(86400))
# print(dt)
