"""
A micro-service passing back enhanced information from Astronomy
Picture of the Day (APOD).
    
Adapted from code in https://github.com/nasa/planetary-api
Dec 1, 2015 (written by Dan Hammer)

@author=danhammer
@author=bathomas @email=brian.a.thomas@nasa.gov
@author=jnbetancourt @email=jennifer.n.betancourt@nasa.gov
"""
import sys
sys.path.insert(0, "../lib")

import os
import json
from multiprocessing.dummy import Pool

from datetime import datetime, date
from flask import request, jsonify, render_template, Flask
from flask_cors import CORS
from flask_gzip import Gzip
from utility import parse_apod
import logging

app = Flask(__name__)
CORS(app)
gzip = Gzip(app)

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# this should reflect both this service and the backing 
# assorted libraries
SERVICE_VERSION = 'v1'
APOD_METHOD_NAME = 'apod'
ALLOWED_APOD_FIELDS = ['date', 'start_date', 'end_date']

CACHE_FOLDER = "cache"
MISSING_DATES = []


def _abort(code, msg, usage=True):
    if usage:
        msg += " " + _usage() + "'"

    response = jsonify(service_version=SERVICE_VERSION, msg=msg, code=code)
    response.status_code = code
    LOG.debug(str(response))

    return response


def _usage(joinstr="', '", prestr="'"):
    return 'Allowed request fields for ' + APOD_METHOD_NAME + ' method are ' + prestr + joinstr.join(
        ALLOWED_APOD_FIELDS)


def _validate(data):
    LOG.debug('_validate(data) called')
    for key in data:
        if key not in ALLOWED_APOD_FIELDS:
            return False
    return True


def _validate_date(dt):
    LOG.debug('_validate_date(dt) called')
    today = datetime.today().date()
    begin = datetime(1995, 6, 16).date()  # first APOD image date

    # validate input
    if (dt > today) or (dt < begin):
        today_str = today.strftime('%b %d, %Y')
        begin_str = begin.strftime('%b %d, %Y')

        raise ValueError('Date must be between %s and %s.' % (begin_str, today_str))


def _apod_handler(dt, use_default_today_date=False):
    """
    Accepts a parameter dictionary. Returns the response object to be
    served through the API.
    """
    try:
        page_props = parse_apod(dt, use_default_today_date)
        LOG.debug('managed to get apod page characteristics')
        return page_props

    except Exception as e:

        LOG.error('Internal Service Error :' + str(type(e)) + ' msg:' + str(e))
        # return code 500 here
        return _abort(500, 'Internal Service Error', usage=False)


def _get_json_for_date(input_date):
    """
    This returns the JSON data for a specific date, which must be a string of the form YYYY-MM-DD. If date is None,
    then it defaults to the current date.
    :param input_date:
    :return:
    """

    # get the date param
    use_default_today_date = False
    if not input_date:
        # fall back to using today's date IF they didn't specify a date
        input_date = datetime.strftime(datetime.today(), '%Y-%m-%d')
        use_default_today_date = True

    # validate input date
    dt = datetime.strptime(input_date, '%Y-%m-%d').date()
    _validate_date(dt)

    # get data
    try:
        data = cached_data_for(dt)
    except:
        data = _apod_handler(dt, use_default_today_date)

    data['service_version'] = SERVICE_VERSION

    # return info as JSON
    return jsonify(data)


def _get_json_for_date_range(start_date, end_date):
    """
    This returns the JSON data for a range of dates, specified by start_date and end_date, which must be strings of the
    form YYYY-MM-DD. If end_date is None then it defaults to the current date.
    :param start_date:
    :param end_date:
    :return:
    """
    # validate input date
    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
    _validate_date(start_dt)

    # get the date param
    if not end_date:
        # fall back to using today's date IF they didn't specify a date
        end_date = datetime.strftime(datetime.today(), '%Y-%m-%d')

    # validate input date
    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
    _validate_date(end_dt)

    start_ordinal = start_dt.toordinal()
    end_ordinal = end_dt.toordinal()
    today_ordinal = datetime.today().date().toordinal()

    if start_ordinal > end_ordinal:
        raise ValueError('start_date cannot be after end_date')

    all_data = []

    while start_ordinal <= end_ordinal:
        # get data
        dt = date.fromordinal(start_ordinal)
        touple = (dt, start_ordinal == today_ordinal)
        all_data.append(touple)
        start_ordinal += 1


    pool = Pool(min(100, len(all_data)))  # max 100 threads
    pool.map(threaded_download, all_data)
    pool.close()
    pool.join()

    # return info as JSON
    return {
        "processed": {"from": start_date, "to": end_date},
        "missing_dates": MISSING_DATES
    }


def threaded_download(touple):
    # touple = (dt, start_ordinal == today_ordinal)
    # _apod_handler(dt, use_default_today_date=False)
    requested_date = touple[0]
    
    if os.path.exists(f"{CACHE_FOLDER}/{requested_date}.json"):
        return
    
    try:
        data = _apod_handler(requested_date, touple[1])
        dump(data, requested_date)
    except:
        date_str = datetime.strftime(requested_date, '%Y-%m-%d')
        MISSING_DATES.append(date_str)
        pass


def dump(data, date):
    if not os.path.exists(CACHE_FOLDER):
        os.makedirs(CACHE_FOLDER)
    with open(f"{CACHE_FOLDER}/{date}.json", "w") as file:
        json.dump(data, file, indent=2)


def cached_data_for(date):
    with open(f"{CACHE_FOLDER}/{date}.json") as file:
        data = json.load(file)
    return data

#
# Endpoints
#

@app.route('/')
def home():
    return render_template('home.html', version=SERVICE_VERSION,
                           service_url=request.host,
                           methodname=APOD_METHOD_NAME,
                           usage=_usage(joinstr='", "', prestr='"') + '"')


@app.route('/' + SERVICE_VERSION + '/' + APOD_METHOD_NAME + '/', methods=['GET'])
def apod():
    LOG.info('apod path called')
    try:

        # application/json GET method
        args = request.args

        if not _validate(args):
            return _abort(400, 'Bad Request: incorrect field passed.')

        #
        input_date = args.get('date')
        start_date = args.get('start_date')
        end_date = args.get('end_date')

        if not start_date and not end_date:
            return _get_json_for_date(input_date)

        elif not input_date and start_date:
            return _get_json_for_date_range(start_date, end_date)

        else:
            return _abort(400, 'Bad Request: invalid field combination passed.')

    except ValueError as ve:
        return _abort(400, str(ve), False)

    except Exception as ex:

        etype = type(ex)
        if etype == ValueError or 'BadRequest' in str(etype):
            return _abort(400, str(ex) + ".")
        else:
            LOG.error('Service Exception. Msg: ' + str(type(ex)))
            return _abort(500, 'Internal Service Error', usage=False)


@app.errorhandler(404)
def page_not_found(e):
    """
    Return a custom 404 error.
    """
    LOG.info('Invalid page request: ' + e)
    return _abort(404, 'Sorry, Nothing at this URL.', usage=True)


@app.errorhandler(500)
def application_error(e):
    """
    Return a custom 500 error.
    """
    return _abort(500, 'Sorry, unexpected error: {}'.format(e), usage=False)


@app.route("/favicon.ico")
def favicon():
    return _abort(404, "favicon doesn't exist")


if __name__ == '__main__':
    app.run(host="0.0.0.0")
