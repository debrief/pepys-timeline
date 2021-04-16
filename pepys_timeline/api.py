from flask import Blueprint, current_app, render_template

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
    return 'not implemented'
