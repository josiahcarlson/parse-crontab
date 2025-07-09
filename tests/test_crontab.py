
from collections import namedtuple
import datetime
import unittest

import pytz
import dateutil.tz

from crontab import CronTab

Results = namedtuple('Results', 'crontab delay max_delay now future')

class TestCrontab(unittest.TestCase):
    def _run_test(self, crontab, max_delay, now=None, min_delay=None):
        ct = CronTab(crontab)
        now = now or datetime.datetime.utcnow()
        delay = ct.next(now, default_utc=True)
        assert delay is not None
        dd = Results(crontab, delay, max_delay, now, now+datetime.timedelta(seconds=delay))
        assert delay <= max_delay, dd
        if min_delay is not None:
            assert delay >= min_delay, dd
        if not crontab.endswith(' 2099'):
            delay2 = ct.previous(now + datetime.timedelta(seconds=delay), default_utc=True)
            dd = Results(crontab, delay, max_delay, now, now+datetime.timedelta(seconds=delay))
            assert abs(delay2) >= delay, (delay, delay2)
            pt = now + datetime.timedelta(seconds=delay) + datetime.timedelta(seconds=delay2)
            assert pt <= now, dd

    def _run_impossible(self, crontab, now):
        ct = CronTab(crontab)
        delay = ct.next(now, default_utc=True)
        assert delay is None, (crontab, delay, now, now+datetime.timedelta(seconds=delay))

    def test_closest(self):
        ce = CronTab("*/15 10-15 * * 1-5")
        t945 = datetime.datetime(2013, 1, 1, 9, 45) # tuesday
        t1245 = datetime.datetime(2013, 1, 1, 12, 45) # tuesday
        s1245 = datetime.datetime(2013, 1, 5, 12, 45) # saturday

        assert not ce.test(t945)
        assert not ce.test(s1245)
        assert ce.test(t1245)

        n = datetime.datetime.utcfromtimestamp(ce.next(t945, delta=False, default_utc=True))
        assert n == datetime.datetime(2013, 1, 1, 10, 0), n
        p = datetime.datetime.utcfromtimestamp(ce.previous(t945, delta=False, default_utc=True))
        assert p == datetime.datetime(2012, 12, 31, 15, 45), p

        n = datetime.datetime.utcfromtimestamp(ce.next(s1245, delta=False, default_utc=True))
        assert n == datetime.datetime(2013, 1, 7, 10, 0), n
        p = datetime.datetime.utcfromtimestamp(ce.previous(s1245, delta=False, default_utc=True))
        assert p == datetime.datetime(2013, 1, 4, 15, 45), p

    def test_normal(self):
        self._run_test('*/5 * * * * * *', 5)
        self._run_test('* * * * *', 60)
        self._run_test('0 * * * *', 3600)
        self._run_test('0 0 * * *', 86400)
        self._run_test('0 0 1 * *', 31*86400)
        self._run_test('5/15 * * * *', 15*60)
        self._run_test('5-51/15 * * * *', 15*60)
        self._run_test('1,8,40 * * * *', 3600)
        self._run_test('0 0 1 1 *', 86400 * 366)
        self._run_test('0 0 1 1 * 2099', 99 * 86400 * 366)
        self._run_test('0 0 ? * 0-6', 86400)
        self._run_test('0 0 31 * *', 62*86400, datetime.datetime(2011, 1, 31))
        self._run_test('0,1/2 * * * *', 60, datetime.datetime(2011, 1, 1, 1, 0))
        self._run_test('0,1/2 * * * *', 120, datetime.datetime(2011, 1, 1, 1, 1))
        self._run_test('0,1/2 * * * *', 60, datetime.datetime(2011, 1, 1, 1, 2))
        self._run_test('0-6,50-59/2 * * * *', 60, datetime.datetime(2011, 1, 1, 1, 1))
        self._run_test('0-6,50-59/2 * * * *', 120, datetime.datetime(2011, 1, 1, 1, 2))
        self._run_test('0-6,50-59/2 * * * *', 900, datetime.datetime(2011, 1, 1, 1, 45))
        self._run_test('0-6,50-59/2 * * * *', 60, datetime.datetime(2011, 1, 1, 1, 55))
        self._run_test('0-6,50/2 * * * *', 60, datetime.datetime(2011, 1, 1, 1, 55))

        self._run_test('10,20 15 * * *', 9*60, datetime.datetime(2011, 1, 1, 15, 1), min_delay=9*60)
        self._run_test('10,20 15 * * *', 5*60, datetime.datetime(2011, 1, 1, 15, 15), min_delay=5*60)
        self._run_test('10,20 15 * * *', 86400 - 600, datetime.datetime(2011, 1, 1, 15, 20), min_delay=86400 - 600)
        self._run_test('* 2-5 * * *', 12525, datetime.datetime(2013, 6, 19, 22, 31, 15), min_delay=12525)

    def test_alternate(self):
        self._run_test('0 0 1 jan-dec *', 32 * 86400)
        self._run_test('0 0 ? * sun-sat', 86400)

    def test_aliases(self):
        self._run_test('@hourly', 3600)
        self._run_test('@daily', 86400)
        self._run_test('@monthly', 31*86400)
        self._run_test('@yearly', 86400 * 366)

    def test_day_of_week(self):
        self._run_test('0 0 ? 7 mon', 4*86400, datetime.datetime(2011, 7, 15))
        self._run_test('0 0 ? 7 mon', 366*86400, datetime.datetime(2011, 7, 25, 1))
        self._run_test('0 0 ? 8 mon-fri', 5*86400 + 1, datetime.datetime(2011, 7, 27, 1))
        self._run_test('0 12 * * sat-sun', 129600, datetime.datetime(2015, 11, 6), 129600)
        self._run_test('0 12 * * sat-sun', 86400, datetime.datetime(2015, 11, 7, 12), 86400)
        self._run_test('0 12 * * sat-sun', 518400, datetime.datetime(2015, 11, 8, 12), 518400)
        self._run_test('0 5 * * fri *', 7*86400, datetime.datetime(2016, 3, 25, 5), 7*86400)
        self._run_test('* * * * Fri *', 6*86400+1, datetime.datetime(2016, 3, 25, 23, 59, 59), 6*86400+1)
        self._run_test('* * * * Fri *', 60, datetime.datetime(2016, 3, 25, 23, 56), 60)
        self._run_test('* * 13 * Fri *', 181*86400+1, datetime.datetime(2015, 11, 13, 23, 59, 59), 181*86400+1)

    def test_last_day(self):
        self._run_test('0 0 L 2 ?', 28*86400, datetime.datetime(2011, 1, 31))
        self._run_test('0 0 1,L 2 ?', 86400, datetime.datetime(2011, 1, 31))
        self._run_test('0 0 2,L 2 ?', 2*86400, datetime.datetime(2011, 1, 31))
        self._run_test('0 0 L 2 ?', 58*86400, datetime.datetime(2011, 1, 1))
        self._run_test('0 0 ? 2 L1', 58*86400, datetime.datetime(2011, 1, 31))
        self._run_test('0 0 ? 7 L1', 1*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L2', 2*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L3', 3*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L4', 4*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L5', 5*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L6', 6*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L0', 7*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L3-5', 3*86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L3-5', 2*86400, datetime.datetime(2011, 7, 25))
        self._run_test('0 0 ? 7 L3-5', 86400, datetime.datetime(2011, 7, 26))
        self._run_test('0 0 ? 7 L3-5', 86400, datetime.datetime(2011, 7, 27))
        self._run_test('0 0 ? 7 L3-5', 86400, datetime.datetime(2011, 7, 28))
        self._run_test('0 0 ? 7 L3-5', 362*86400, datetime.datetime(2011, 7, 29))
        self._run_test('0 0 ? 7 L0-1', 24*86400, datetime.datetime(2011, 7, 1))
        self._run_test('0 0 ? 7 L0-1', 24*86400, datetime.datetime(2011, 7, 1))
        self._run_test('0 0 ? 7 L0-1', 86400, datetime.datetime(2011, 7, 24))
        self._run_test('0 0 ? 7 L0-1', 6*86400, datetime.datetime(2011, 7, 25))
        self._run_test('59 23 L 12 *', 282*86400, datetime.datetime(2012, 3, 25), 280*84400)
        self._run_test('0 0 ? 2 L1', 28*86400, datetime.datetime(2016, 2, 1), 28*86400)
        self._run_test('0 0 ? 2 L0', 27*86400, datetime.datetime(2016, 2, 1), 27*86400)
        self._run_test('0 0 ? 2 L7', 27*86400, datetime.datetime(2016, 2, 1), 27*86400)
        self._run_test('0 0 ? 2 L6', 26*86400, datetime.datetime(2016, 2, 1), 26*86400)
        self._run_test('0 0 ? 2 L5', 25*86400, datetime.datetime(2016, 2, 1), 25*86400)
        self._run_test('0 0 ? 2 L4', 24*86400, datetime.datetime(2016, 2, 1), 24*86400)
        self._run_test('0 0 ? 2 L3', 23*86400, datetime.datetime(2016, 2, 1), 23*86400)
        self._run_test('0 0 ? 2 L2', 22*86400, datetime.datetime(2016, 2, 1), 22*86400)

    def test_impossible(self):
        self._run_impossible('0 0 * 7 fri 2011', datetime.datetime(2011, 7, 31))
        self._run_impossible('0 0 29 2 * 2011', datetime.datetime(2011, 2, 1))
        self._run_impossible('0 0 L 1 * 2011', datetime.datetime(2011, 2, 1))
        self._run_impossible('0 0 L 1 * 2011', datetime.datetime(2011, 1, 31))
        self._run_impossible('0 0 ? 7 L3-5 2011', datetime.datetime(2011, 7, 29))
        self._run_impossible('0 0 29 2 * 2012-2015', datetime.datetime(2012, 2, 29))

    def test_bad_crontabs(self):
        self.assertRaises(ValueError, lambda: CronTab('*'))
        self.assertRaises(ValueError, lambda: CronTab('* *'))
        self.assertRaises(ValueError, lambda: CronTab('* * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * * * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('-1 * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* mon-tue * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * feb-jan *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * * L'))
        self.assertRaises(ValueError, lambda: CronTab('* * * L *'))
        self.assertRaises(ValueError, lambda: CronTab('* L * * *'))
        self.assertRaises(ValueError, lambda: CronTab('L * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* 1, * * *'))
        self.assertRaises(ValueError, lambda: CronTab('60 * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* 25 * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * 32 * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * 13 *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * * 9999'))
        self.assertRaises(ValueError, lambda: CronTab('20/50 * * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('0/100 * * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('*,50-59/12 * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * DEC/7 * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * * MON/7 *'))

    def test_previous(self):
        schedule = CronTab('0 * * * *')
        ts = datetime.datetime(2014, 6, 6, 9, 0, 0)
        for i in range(70):
            next = schedule.next(ts, default_utc=True)
            self.assertTrue(0 <= next <= 3600, next)
            previous = schedule.previous(ts, default_utc=True)
            self.assertTrue(-3600 <= previous <= 0, previous)
            ts += datetime.timedelta(seconds=1)

    def test_timezones_pytz(self):
        s = CronTab('0 9 13 3 * 2016')

        self.assertEqual(s.next(datetime.datetime(2016, 3, 13), default_utc=True), 32400)
        self.assertEqual(s.next(pytz.utc.localize(datetime.datetime(2016, 3, 13)), default_utc=True), 32400)

        self.assertEqual(s.next(pytz.timezone('US/Eastern').localize(datetime.datetime(2016, 3, 13))), 28800)

        t = CronTab('0 9 * * * 2018')
        self.assertEqual(t.next(datetime.datetime(2018, 11, 4), default_utc=True), 32400)

        timezone = pytz.timezone("America/Los_Angeles")
        self.assertEqual(t.next(timezone.localize(datetime.datetime(2018, 11, 4))), 36000)
        before = pytz.utc.localize(datetime.datetime(2018, 11, 4, 8, 29)).astimezone(timezone)
        self.assertEqual(CronTab('30 1 * * * 2018').next(before), 3660)
        self.assertEqual(CronTab('30 1 * * * 2018').next(timezone.localize(datetime.datetime(2018, 11, 4, 1, 15))), 900)
        self.assertEqual(CronTab('30 1 * * * 2018').next(timezone.localize(datetime.datetime(2018, 11, 4))), 9000)

    def test_timezones_dateutil(self):
        s = CronTab('0 9 13 3 * 2016')

        self.assertEqual(s.next(datetime.datetime(2016, 3, 13), default_utc=True), 32400)
        utc = dateutil.tz.tzutc()
        self.assertEqual(s.next(datetime.datetime(2016, 3, 13, tzinfo=utc), default_utc=True), 32400)

        x = datetime.datetime(2016, 3, 13, tzinfo=dateutil.tz.gettz('US/Eastern'))
        self.assertEqual(s.next(x), 28800)

        t = CronTab('0 9 * * * 2018')
        self.assertEqual(t.next(datetime.datetime(2018, 11, 4), default_utc=True), 32400)

        timezone = dateutil.tz.gettz("America/Los_Angeles")
        self.assertEqual(t.next(datetime.datetime(2018, 11, 4, tzinfo=timezone)), 36000)
        before = datetime.datetime(2018, 11, 4, 8, 29, tzinfo=utc).astimezone(timezone)
        self.assertEqual(CronTab('30 1 * * * 2018').next(before), 60)
        before = datetime.datetime(2018, 11, 4, 8, 31, tzinfo=utc).astimezone(timezone)
        self.assertEqual(CronTab('30 1 * * * 2018').next(before), 89940)
        self.assertEqual(CronTab('30 1 * * * 2018').next(datetime.datetime(2018, 11, 4, 1, 15, tzinfo=timezone)), 900)
        self.assertEqual(CronTab('30 1 * * * 2018').next(datetime.datetime(2018, 11, 4, tzinfo=timezone)), 5400)

    def test_equal(self):
        a = CronTab("3 * 5 6 *")
        b = CronTab("3 * 5 6 *")
        self.assertEqual(a, b)
        a = CronTab("3 * 5 6 *", random_seconds=True)
        b = CronTab("3 * 5 6 *")
        self.assertNotEqual(a, b)

    def test_last_days(self):
        utc = dateutil.tz.tzutc()
        a = CronTab("* * l * *")
        b = CronTab("* * z0 * *")
        c = CronTab("* * z1 * *")
        d = CronTab("* * z7 * *")
        e = CronTab("* * z0-7 * *")

        a_day = datetime.datetime(2025, 7, 8, 0, 0, tzinfo=utc)
        last = a.next(a_day)
        self.assertEqual(last, b.next(a_day))
        last = a_day + datetime.timedelta(seconds=last)
        self.assertEqual(last.day - 1, (a_day + datetime.timedelta(seconds=c.next(a_day))).day)
        self.assertEqual(last.day - 7, (a_day + datetime.timedelta(seconds=d.next(a_day))).day)
        self.assertEqual(last.day - 7, (a_day + datetime.timedelta(seconds=e.next(a_day))).day)


if __name__ == '__main__':
    unittest.main()
