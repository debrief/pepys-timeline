import os.path
import json

from flask import Blueprint, current_app, request, render_template

from pepys_timeline.config import STATIC_DIR
from pepys_timeline.db import get_dashboard_metadata, get_dashboard_stats


api = Blueprint('api', __name__, url_prefix='')

MISSING_PARAMS_MSG = "missing parameter(s)"


@api.route('/')
def index():
    return render_template('index.html')


@api.route('/config')
def config():
    return {
       "frequency_secs": current_app.config['UPDATE_FREQUENCY']
    }


@api.route('/timelines')
def timelines():
    with open(os.path.join(STATIC_DIR, 'serials.json'), 'r') as f:
        serials = json.load(f)

    return {
        "serials": serials
    }


@api.route('/dashboard_metadata')
def dashboard_metadata():
    data = request.args
    if any((p not in data for p in ('from_date', 'to_date'))):
        return MISSING_PARAMS_MSG, 400
    from_date = data.get('from_date')
    to_date = data.get('to_date')
    return {
        "dashboard_metadata": get_dashboard_metadata(from_date, to_date)
    }


@api.route('/dashboard_stats', methods=['POST'])
def dashboard_stats():
    data = request.json
    if any((p not in data for p in ('serial_participants', 'range_types'))):
        return MISSING_PARAMS_MSG, 400
    serial_participants = data.get('serial_participants')
    range_types = data.get('range_types')
    stats = get_dashboard_stats(serial_participants, range_types)
    return {
        "dashboard_stats": stats
    }
