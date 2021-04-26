from typing import Optional, List


def get_dashboard_metadata_query(
        from_date: str = '2021-01-05',
        to_date: str = '2021-01-05'
):
    return f"""
        select * from pepys.dashboard_metadata('{from_date}', '{to_date}');
    """


def get_dashboard_stats_query(
        serial_id: str = "faa18ef7-6823-33dc-0f16-de6e4b2c02f3",
        platform_id: str = "50d64387-9f91-4c6f-8933-f4e7b1a7d8ab",
        start_timestamp: str = "2020-11-15 00:00:00",
        end_timestamp: str = "2020-11-15 23:59:59",
        gap_seconds: int = 30,
        range_types: Optional[List[str]] = None
):
    if not range_types:
        range_types = ["G", "C"]

    return (
        f"""
            select * from pepys.dashboard_stats('[{'{'}
               "serial_id": "{serial_id}",
               "platform_id": "{platform_id}",
               "start": "{start_timestamp}",
               "end": "{end_timestamp}",
               "gap_seconds": {gap_seconds}
            {'}'}]', '[{",".join([f'"{t}"' for t in range_types])}]');
        """
    )
