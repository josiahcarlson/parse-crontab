
'''
crontab.py

Written July 15, 2011 by Josiah Carlson
Released under the GNU LGPL v2.1
available: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html

Other licenses may be available upon request.

'''

from collections import namedtuple
import datetime

_ranges = [
    (0, 59),
    (0, 23),
    (1, 31),
    (1, 12),
    (0, 6),
    (1970, 2099),
]
_attribute = [
    'minute',
    'hour',
    'day',
    'month',
    'isoweekday',
    'year'
]
_alternate = {
    3: {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov':11, 'dec':12},
    4: {'sun': 0, 'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6},
}
_aliases = {
    '@yearly':  '0 0 1 1 *',
    '@annually':  '0 0 1 1 *',
    '@monthly': '0 0 1 * *',
    '@weekly':  '0 0 * * 0',
    '@daily':   '0 0 * * *',
    '@hourly':  '0 * * * *',
}

MINUTE = datetime.timedelta(minutes=1)
HOUR = datetime.timedelta(hours=1)
DAY = datetime.timedelta(days=1)
WEEK = datetime.timedelta(days=7)
MONTH = datetime.timedelta(days=28)
YEAR = datetime.timedelta(days=365)

# find the next scheduled time
def _end_of_month(dt):
    ndt = dt + DAY
    while dt.month == ndt.month:
        dt += DAY
    return ndt.replace(day=1) - DAY

def _month_incr(dt, m):
    odt = dt
    dt += MONTH
    while dt.month == odt.month:
        dt += DAY
    # get to the first of next month, let the backtracking handle it
    dt = dt.replace(day=1)
    return dt - odt

def _year_incr(dt, m):
    # simple leapyear stuff works for 1970-2099 :)
    mod = dt.year % 4
    if mod == 0 and (dt.month, dt.day) < (2, 29):
        return YEAR + DAY
    if mod == 3 and (dt.month, dt.day) > (2, 29):
        return YEAR + DAY
    return YEAR

_increments = [
    lambda *a: MINUTE,
    lambda *a: HOUR,
    lambda *a: DAY,
    _month_incr,
    lambda *a: DAY,
    _year_incr,
]

# find the previously scheduled time
def _day_decr(dt, m):
    if m.day.input != 'l':
        return -DAY
    odt = dt
    ndt = dt = dt - DAY
    while dt.month == ndt.month:
        dt -= DAY
    return dt - odt

def _month_decr(dt, m):
    odt = dt
    # get to the last day of last month, let the backtracking handle it
    dt = dt.replace(day=1) - DAY
    return dt - odt

def _year_decr(dt, m):
    # simple leapyear stuff works for 1970-2099 :)
    mod = dt.year % 4
    if mod == 0 and (dt.month, dt.day) > (2, 29):
        return -(YEAR + DAY)
    if mod == 1 and (dt.month, dt.day) < (2, 29):
        return -(YEAR + DAY)
    return -YEAR

_decrements = [
    lambda *a: -MINUTE,
    lambda *a: -HOUR,
    _day_decr,
    _month_decr,
    lambda *a: -DAY,
    _year_decr,
]

Matcher = namedtuple('Matcher', 'minute, hour, day, month, weekday, year')

def _assert(condition, message, *args):
    if not condition:
        raise ValueError(message%args)

class _Matcher(object):
    __slots__ = 'allowed', 'end', 'any', 'input', 'which', 'split'
    def __init__(self, which, entry):
        _assert(0 <= which <= 5,
            "improper number of cron entries specified")
        self.input = entry.lower()
        self.split = self.input.split(',')
        self.which = which
        self.allowed = set()
        self.end = None
        self.any = '*' in self.split or '?' in self.split
        for it in self.split:
            al, en = self._parse_crontab(which, it)
            if al is not None:
                self.allowed.update(al)
            self.end = en
        _assert(self.end is not None,
            "improper item specification: %r", entry.lower()
        )
    def __call__(self, v, dt):
        if 'l' in self.split:
            if v == _end_of_month(dt).day:
                return True
        elif any(x.startswith('l') for x in self.split):
            okay = dt.month != (dt + WEEK).month
            if okay and (self.any or v in self.allowed):
                return True
        return self.any or v in self.allowed
    def __lt__(self, other):
        if self.any:
            return self.end < other
        return all(item < other for item in self.allowed)
    def __gt__(self, other):
        if self.any:
            return _ranges[self.which][0] > other
        return all(item > other for item in self.allowed)
    def _parse_crontab(self, which, entry):
        '''
        This parses a single crontab field and returns the data necessary for
        this matcher to accept the proper values.

        See the README for information about what is accepted.
        '''
        # this handles day of week/month abbreviations
        def _fix(it):
            if which in _alternate and not it.isdigit():
                if it in _alternate[which]:
                    return _alternate[which][it]
            _assert(it.isdigit(),
                "invalid range specifier: %r (%r)", it, entry)
            return int(it, 10)

        # this handles individual items/ranges
        def _parse_piece(it):
            if '-' in it:
                start, end = map(_fix, it.split('-'))
            elif it == '*':
                start = _start
                end = _end
            else:
                start = _fix(it)
                end = _end
                if increment is None:
                    return set([start])
            _assert(_start <= start <= _end,
                "range start value %r out of range [%r, %r]", start, _start, _end)
            _assert(_start <= end <= _end,
                "range end value %r out of range [%r, %r]", end, _start, _end)
            _assert(start <= end,
                "range start value %r > end value %r", start, end)
            return set(range(start, end+1, increment or 1))

        _start, _end = _ranges[which]
        # wildcards
        if entry in ('*', '?'):
            if entry == '?':
                _assert(which in (2, 4),
                    "cannot use '?' in the %r field", _attribute[which])
            return None, _end

        # last day of the month
        if entry == 'l':
            _assert(which == 2,
                "you can only specify a bare 'L' in the 'day' field")
            return None, _end

        # last day of the week
        elif entry.startswith('l'):
            _assert(which == 4,
                "you can only specify a leading 'L' in the 'weekday' field")
            entry = entry.lstrip('l')

        increment = None
        # increments
        if '/' in entry:
            entry, increment = entry.split('/')
            increment = int(increment, 10)
            _assert(increment > 0,
                "you can only use positive increment values, you provided %r",
                increment)

        # handle all of the a,b,c and x-y,a,b entries
        good = set()
        for it in entry.split(','):
            good.update(_parse_piece(it))

        return good, _end

class CronTab(object):
    __slots__ = 'matchers',
    def __init__(self, crontab):
        self.matchers = self._make_matchers(crontab)

    def _make_matchers(self, crontab):
        '''
        This constructs the full matcher struct.
        '''
        crontab = _aliases.get(crontab, crontab)
        matchers = [_Matcher(which, entry)
                        for which, entry in enumerate(crontab.split())]
        if len(matchers) == 5:
            matchers.append(_Matcher(5, '*'))
        _assert(len(matchers) == 6,
            "improper number of cron entries specified")
        matchers = Matcher(*matchers)
        if not matchers.day.any:
            _assert(matchers.weekday.any,
                "missing a wildcard specifier for weekday")
        if not matchers.weekday.any:
            _assert(matchers.day.any,
                "missing a wildcard specifier for day")
        return matchers

    def _test_match(self, index, dt):
        '''
        This tests the given field for whether it matches with the current
        datetime object passed.
        '''
        at = _attribute[index]
        attr = getattr(dt, at)
        if at == 'isoweekday':
            attr = attr() % 7
        return self.matchers[index](attr, dt)

    def next(self, now=None, increments=_increments):
        '''
        How long to wait in seconds before this crontab entry can next be
        executed.
        '''
        now = now or datetime.datetime.now()
        if isinstance(now, (int, long, float)):
            now = datetime.datetime.fromtimestamp(now)
        # get a reasonable future/past start time
        future = now.replace(second=0, microsecond=0) + increments[0]()
        if future < now:
            # we are going backwards...
            _test = lambda: future.year < self.matchers.year
        else:
            # we are going forwards
            _test = lambda: self.matchers.year < future.year
        to_test = 0
        while to_test < 6:
            incr = increments[to_test]
            while not self._test_match(to_test, future):
                future += incr(future, self.matchers)
                if _test():
                    return None
            # check for backtrack conditions
            if to_test >= 3:
                for tt in xrange(2, to_test):
                    if not self._test_match(tt, future):
                        # rely on the increment below to get us back to 2
                        to_test = 1
                        break
            to_test += 1

        # verify the match
        match = [self._test_match(i, future) for i in xrange(6)]
        _assert(all(match),
            "\nYou have discovered a bug with crontab, please notify the\n" \
            "author with the following information:\n" \
            "crontab: %r\n" \
            "now: %r", ' '.join(m.input for m in self.matchers), now)
        delay = future - now
        return delay.days * 86400 + delay.seconds + delay.microseconds / 1000000.

    def previous(self, now=None):
        return self.next(now, _decrements)
