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
        This class is to unit test the business logic implemented in the dashboard_stats query.
        TO DO: Include the detailed documentation explaining the query logic
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

    def testQueryLogic2(self):
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
