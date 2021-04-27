import json
from typing import List, Dict


def get_dashboard_metadata_query(from_date: str, to_date: str):
    return f"""
        select * from pepys.dashboard_metadata('{from_date}', '{to_date}');
    """


def get_dashboard_stats_query(
        serial_participants: List[Dict],
        range_types: List[str],
):
    return (
        f"""
            select * from pepys.dashboard_stats('
                {json.dumps(serial_participants)}',
                '{json.dumps(range_types)}'
            );
        """
    )
