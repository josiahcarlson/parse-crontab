import datetime
import unittest

from crontab import CronTab

class TestCrontab(unittest.TestCase):
    def _run_test(self, crontab, max_delay, now=None, min_delay=None):
        ct = CronTab(crontab)
        now = now or datetime.datetime.now()
        delay = ct.next(now)
        assert delay is not None
        dd = (crontab, delay, max_delay, now, now+datetime.timedelta(seconds=delay))
        assert delay <= max_delay, dd
        if min_delay is not None:
            assert delay >= min_delay, dd
        if not crontab.endswith(' 2099'):
            delay2 = ct.previous(now + datetime.timedelta(seconds=delay))
            dd = (crontab, delay, max_delay, now, now+datetime.timedelta(seconds=delay))
            assert abs(delay2) >= delay, (delay, delay2)
            pt = now + datetime.timedelta(seconds=delay) + datetime.timedelta(seconds=delay2)
            assert pt <= now, dd

    def _run_impossible(self, crontab, now):
        ct = CronTab(crontab)
        delay = ct.next(now)
        assert delay is None, (crontab, delay, now, now+datetime.timedelta(seconds=delay))

    def test_normal(self):
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
        self.assertRaises(ValueError, lambda: CronTab('* * * * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('-1 * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* mon-tue * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * feb-jan *'))
        self.assertRaises(ValueError, lambda: CronTab('* * * * L'))
        self.assertRaises(ValueError, lambda: CronTab('* * * L *'))
        self.assertRaises(ValueError, lambda: CronTab('* L * * *'))
        self.assertRaises(ValueError, lambda: CronTab('L * * * *'))
        self.assertRaises(ValueError, lambda: CronTab('* 1, * * *'))

def test():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrontab)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == '__main__':
    test()
