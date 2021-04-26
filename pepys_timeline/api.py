import os.path
import json

from flask import Blueprint, current_app, render_template

from pepys_timeline.config import STATIC_DIR
from pepys_timeline.db import get_dashboard_metadata, get_dashboard_stats


api = Blueprint('api', __name__, url_prefix='')


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
    return {
        "dashboard_stats": get_dashboard_metadata()
    }


@api.route('/dashboard_stats')
def dashboard_stats():
    return {
        "dashboard_stats": get_dashboard_stats()
    }
