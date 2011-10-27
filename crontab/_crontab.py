
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

def _day_incr(dt, m):
    if m.day.input != 'l':
        return DAY
    odt = dt
    ndt = dt = dt + DAY
    while dt.month == ndt.month:
        dt += DAY
    return dt - odt

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
    _day_incr,
    _month_incr,
    lambda *a: DAY,
    _year_incr,
]

Matcher = namedtuple('Matcher', 'minute, hour, day, month, weekday, year')

def _assert(condition, message, *args):
    if not condition:
        raise ValueError(message%args)

class _Matcher(object):
    __slots__ = 'allowed', 'end', 'any', 'input', 'which'
    def __init__(self, which, entry):
        _assert(0 <= which <= 5,
            "improper number of cron entries specified")
        self.input = entry.lower()
        self.which = which
        self.allowed, self.end = self._parse_crontab(which, entry.lower())
        self.any = self.allowed is None
    def __call__(self, v, dt):
        if self.input == 'l':
            return v != (dt + DAY).month
        elif self.input.startswith('l'):
            okay = dt.month != (dt + WEEK).month
            return okay and (self.any or v in self.allowed)
        return self.any or v in self.allowed
    def __lt__(self, other):
        if self.any:
            return self.end < other
        return all(item < other for item in self.allowed)
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

    def next(self, now=None):
        '''
        How long to wait in seconds before this crontab entry can next be
        executed.
        '''
        now = now or datetime.datetime.now()
        if isinstance(now, (int, long, float)):
            now = datetime.datetime.fromtimestamp(now)
        # get a reasonable future start time
        future = now.replace(second=0, microsecond=0) + datetime.timedelta(minutes=1)
        to_test = 0
        while to_test < 6:
            incr = _increments[to_test]
            while not self._test_match(to_test, future):
                future += incr(future, self.matchers)
                if self.matchers.year < future.year:
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
