def get_dashboard_metadata_query(from_date='2021-01-05', to_date='2021-01-05'):
    return f"""
        select * from pepys.dashboard_metadata('{from_date}', '{to_date}');
    """


def get_dashboard_stats_query():
    return (
        """
            select * from pepys.dashboard_stats('[{
               "serial_id": "faa18ef7-6823-33dc-0f16-de6e4b2c02f3",
               "platform_id": "50d64387-9f91-4c6f-8933-f4e7b1a7d8ab",
               "start": "2020-11-15 00:00:00",
               "end": "2020-11-15 23:59:59",
               "gap_seconds": 30
            }]', '["G","C"]');
        """
    )
