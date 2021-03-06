"""
    The following describes:

        A. LOGIC USED IN "dashboard_stats.sql" QUERY TO DETERMINE COVERAGE AND GAPS

        B. HOW THIS TEST CASE VALIDATES THE ABOVE LOGIC 

    A. LOGIC USED IN "dashboard_stats.sql" QUERY TO DETERMINE COVERAGE AND GAPS

        Requirement is to calculate *coverage* and *gaps* in a given period for a platform.

        *gap* is any duration, which exceeds a predefined value called gap_seconds, between 
        two adjacent (when sorted using time) records in pepys."States" table for that 
        platform within the requested period 

        *coverage* are sections that are not *gaps* within the requested period for that platform

        Based on the above definitions, we consider the following values to calculate *gap*/*coverage*

        a) SERIAL_START_TIME and SERIAL_END_TIME: The duration for which *coverage* measurements are to 
            be calculated for a given platform
        b) GAP_SECONDS: The predifned value (gap_seconds) considered to determine if duration is a *gap*
            or *coverage*

        The  query uses a layered approach to calculate *gaps* individually under all possible scenario
        and then invert them to find *coverage*

        The query is formed by the following CTEs (Common Table Expression)/Subqueries grouped under these 5 heads,
        the names of which are descriptive.

        <<INPUT PARSING CTEs>>
        serial_participants_input_json
        range_types
        serial_participants_json
        participating_platforms

        <<DATA FETCHING CTEs>>
        sensors_involved
        states_involved

        <<GAP DETERMINATION CTEs>>
        state_time_rankings
        participation_sans_activity
        inner_gaps
        edge_cases
        gaps_at_serial_start
        gaps_at_serial_end
        consolidated_gaps

        <<COVERAGE DETERMINATION CTEs>>
        consolidated_gap_ranks
        participation_sans_gap
        act_with_same_part_and_gap_start
        act_with_same_part_and_gap_end
        inner_coverage
        coverage_at_serial_start
        coverage_at_serial_end
        consolidated_coverage

        <<STAT CONSOLIDATION CTE>>
        consolidated_stats

        To determine adjacency, the pepys."States" records are sorted based on time and numbered
        over serial_id, platform_id, and ser_idx in state_time_rankings CTE.

        The following exhaustive cases are considered for *gap* determination

        participation_sans_activity:
           This indicates a period of exercise where there are no corresponding pepys."States" records.
           In this case, the entire period is marked as *gap*

        inner_gaps:
            This fetches all normally occuring *gaps* between two adjacent pepys."States".time records
            within the SERIAL_START_TIME and SERIAL_END_TIME

        gaps_at_serial_start:
            This identifies *gaps* between SERIAL_START_TIME and the first pepys."States" record
            for that platform and serial_id

        gaps_at_serial_end:
            This identifies *gaps* between SERIAL_END_TIME and the last pepys."States" record
            for that platform and serial_id

        consolidated_gaps:
            This consolidates all the *gaps* identified in the above gap CTEs

        The following exhaustive scenarios are considered for *coverage* determination

        participation_sans_gap:
            This identifies all serial participations without any *gaps* and marks the entire
            duration as *coverage*

        act_with_same_part_and_gap_start:
            These are edge cases where the SERIAL_START_TIME and the first pepys."States" record
            are the same, and the next pepys."States".time record is at a *gap* from the first.
            This CTEs consolidates all such periods and marks their SERIAL_START_TIME as a
            *coverage* record of duration 0.

        act_with_same_part_and_gap_end:
            These are edge cases where the SERIAL_END_TIME and the last pepys."States" record
            are the same, and the subsequent pepys."States".time record is at a *gap* from the last.
            This CTEs consolidates all such periods and marks their SERIAL_END_TIME as a
            *coverage* record of duration 0.

        inner_coverage:
            This fetches all normally occuring *coverage* between two adjacent *gap* period
            within the SERIAL_START_TIME and SERIAL_END_TIME. The end time of the first *gap*
            and the start time of the next *gap* is marked as *coverage*. *coverage* records can 
            also be of duration 0, i.e. the two *gaps* are separated by a singe pepys."State"
            record.

        coverage_at_serial_start:
            This identifies *coverage* between SERIAL_START_TIME and the first pepys."States" record
            for that platform and serial_id

        coverage_at_serial_end:
            This identifies *coverage* between SERIAL_END_TIME and the last pepys."States" record
            for that platform and serial_id

        consolidated_coverage:
            This consolidates all the *gaps* identified in the above gap CTEs
"""
import itertools
import json
import psycopg2
import testing.postgresql
import unittest

MetafileLocation="dashboard_stats.sql"
someUUId='54f6d015-8adf-47f4-bf02-33e06fbe0725'
timelist=["09:00:00"]
dateval="2020-12-12 "

class TestDashboardStatsQuery(unittest.TestCase):
    """
        This class is to unit test the business logic implemented in dashboard_stats query.
    """
    def setUp(self):
        self.postgresql=testing.postgresql.Postgresql()
        with psycopg2.connect(**self.postgresql.dsn()) as conn:
            cursor=conn.cursor()
            conn.commit()

    def tearDown(self):
        self.postgresql.stop()

    def testQueryLogic(self):
        with psycopg2.connect(**self.postgresql.dsn()) as conn:
            cursor = conn.cursor()
            populateData(cursor, timelist)
            rows=fetchrows(cursor,'12:12:12','15:12:12')
            self.assertTrue(validate(rows,['G'],['12:12:12']))
            rows=fetchrows(cursor,'08:00:00','15:12:12')
            self.assertTrue(validate(rows,['G','C','G'],['08:00:00','09:00:00','09:00:00']))

class FilterInputJSON:
    pass

class FilterEncoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__

def getData(listPlatformRanges):
    return (FilterEncoder().encode(listPlatformRanges))

def getQuery():
    return "select * from pepys.dashboard_stats(%s, %s)"

def populateData(cursor, timelist):
    cursor.execute('create schema pepys')
    cursor.execute('create table pepys."Sensors"(host uuid, sensor_id uuid)')
    cursor.execute('create table pepys."States"(sensor_id uuid, time timestamp)')
    cursor.execute('create table pepys."Serials"(serial_id uuid, serial_number text)')
    cursor.execute("""insert into pepys."Sensors" values('{}', '{}')""".format(someUUId, someUUId))
    cursor.execute("""insert into pepys."Serials" values('{}', '{}')""".format(someUUId, "J052010"))
    for time in timelist:
        cursor.execute("""insert into pepys."States" values('{}', '{}{}')""".format(someUUId,dateval,time))
    with open(MetafileLocation,"r") as statssqlfile:
        cursor.execute(statssqlfile.read())

def fetchrows(cursor, start, end):
    cursor.execute(getQuery(), testcaseData(start, end))
    return cursor.fetchall()

def testcaseData(start, end):
    fij=FilterInputJSON()
    fij.serial_id=fij.platform_id=someUUId
    fij.start=dateval+start
    fij.end=dateval+end
    fij.gap_seconds=150
    return (getData([fij]), '["C","G"]',)

def validate(rows, rangeTypes, startTimes):
    for (row,ranget,startt) in zip(rows,rangeTypes,startTimes):
        (rangetype,starttime,endtime,platid,serialid)=row
        if rangetype!=ranget or startt!=starttime.strftime('%H:%M:%S'):
            print(row,ranget,startt)
            return False
    return True

if __name__ == '__main__':
    unittest.main()
