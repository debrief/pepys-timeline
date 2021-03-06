from flask import Flask


def create_app(config_path: str = None):
    if config_path is None:
        config_path = 'pepys_timeline.config'

    app = Flask(__name__)
    app.config.from_object(config_path)

    register_blueprints(app)
    register_extensions(app)

    return app


def register_extensions(app):
    from pepys_timeline.extensions import cors, cache_buster
    cors.init_app(app)
    cache_buster.init_app(app)


def register_blueprints(app):
    from pepys_timeline.api import api
    app.register_blueprint(api)
