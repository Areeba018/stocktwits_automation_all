import os
import uuid
import json
import time
import tornado
import tornado.escape
# import datetime
from random import choice
from string import ascii_lowercase
from datetime import datetime, timedelta, timezone

from tornado.httpclient import HTTPRequest, AsyncHTTPClient

from common.exceptions import GeneralException

BASE36_ALPHABETS = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def MakeTimedUniqueId():
    """
    Generate a unique id.
    """

    time.sleep(0.0001)  # to make number unique

    prefix = os.environ.get('HOST_PK_PREFIX', '')
    if len(prefix) > 4:
        prefix = prefix[:4]

    base36 = ''

    # H00116407760464156960
    # H00216407760464156960
    number = int(time.time() * 1000000)
    while number != 0:
        number, i = divmod(number, len(BASE36_ALPHABETS))
        base36 = BASE36_ALPHABETS[i] + base36

    return f'{prefix}{base36}'


def TimeUniqueIdInt(number: str):
    return int(number, 36)


def make_uuid4():
    return str(uuid.uuid4()).replace('-', '')


def make_string(n=10):
    string_val = "".join(choice(ascii_lowercase) for i in range(n))
    return string_val


def date_timestamp(date_string):
    dt = datetime.strptime(date_string, '%d %b %Y %I:%M%p')
    return datetime.timestamp(dt)


def year_range(dt, datetime_o = datetime):

    month = dt.strftime('%b')
    year = int(dt.strftime('%Y'))

    return (
        datetime.timestamp(datetime_o.min.replace(year = year)),
        datetime.timestamp(datetime_o.max.replace(year = year)) - 1,
        f'{year}'
    )


def format_date(dt, tz_offset=18000, frmt='%d %b %Y'):
    dt = datetime.fromtimestamp(dt, tz=timezone(timedelta(seconds=tz_offset)))
    fd = dt.strftime(frmt)
    return fd


async def get_time_year_month(self, current_time=None, tz_offset=18000):
    if current_time is None:
        current_time = int(time.time())

    dt = datetime.fromtimestamp(current_time, tz=timezone(timedelta(seconds=tz_offset)))
    month = dt.strftime('%b')
    year = dt.strftime('%Y')
    return year, month, current_time


async def call_api(url, data, method='POST'):
    headers = {'content-type': 'application/json'}

    req = HTTPRequest(url=url, method=method, headers=headers, connect_timeout=5)
    if data is not None:
        req = HTTPRequest(url=url, method=method, headers=headers, body=json.dumps(data), connect_timeout=5)

    http_client = AsyncHTTPClient()

    resp = None

    try:
        resp = await http_client.fetch(request=req, raise_error=True)
        if resp is not None and resp.body is not None:
            resp = tornado.escape.json_decode(resp.body)
    except Exception as ex:
        print('internal api error ->', ex.args)
        # raise GeneralException(422, 'internal api error')

    http_client.close()

    return resp


def start_of_day(ref_time_stamp, tz_offset=0):
    tz = timezone(timedelta(seconds=tz_offset))
    current_date = datetime.fromtimestamp(ref_time_stamp, tz=tz)
    sod = datetime(year=current_date.year,
                            month=current_date.month,
                            day=current_date.day,
                            hour=0,
                            minute=0,
                            second=0,
                            tzinfo=tz)
    _timestamp = int(sod.timestamp())
    return _timestamp


def get_start_time_for_daily_night_service():
    tz = timezone(timedelta(seconds=-18000))
    current_date = datetime.now(tz=tz)
    current_date_11_59 = datetime(year=current_date.year,
                                  month=current_date.month,
                                  day=current_date.day,
                                  hour=23,
                                  minute=59,
                                  second=59)

    current_time = int(current_date.timestamp())
    next_time = int(current_date_11_59.timestamp()) + 1
    time_diff_12am_from_now = next_time - current_time

    return time_diff_12am_from_now


def get_start_time_hours_multiple():
    tz = timezone(timedelta(seconds=-18000))
    current_date = datetime.now(tz=tz)
    current_date_updated = datetime(year=current_date.year,
                                  month=current_date.month,
                                  day=current_date.day,
                                  hour=current_date.hour + 1,
                                  minute=0,
                                  second=0, tzinfo=tz)

    current_time = int(current_date.timestamp())
    next_time = int(current_date_updated.timestamp())
    time_diff_from_now = next_time - current_time

    return time_diff_from_now
