import psycopg2
from flask import current_app
from psycopg2.extras import RealDictCursor

from pepys_timeline.queries import (
    get_dashboard_metadata_query,
    get_dashboard_stats_query
)


def get_db_conn_kwargs():
    config = current_app.config
    return dict(
        host=config['DB_HOST'],
        port=config['DB_PORT'],
        database=config['DB_NAME'],
        user=config['DB_USER'],
        password=config['DB_PASSWORD'],
    )


def get_dashboard_metadata():
    db_conn_kwargs = get_db_conn_kwargs()
    with psycopg2.connect(**db_conn_kwargs) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(get_dashboard_metadata_query())
            meta = curs.fetchall()
    return meta


def get_dashboard_stats():
    db_conn_kwargs = get_db_conn_kwargs()
    with psycopg2.connect(**db_conn_kwargs) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as curs:
            curs.execute(get_dashboard_stats_query())
            stats = curs.fetchall()
    return stats
