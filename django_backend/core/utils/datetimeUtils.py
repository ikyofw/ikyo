from datetime import datetime, timedelta

def getDurationStr(startTime: datetime, endTime: datetime = None, millisecond: bool = True, microsecond: bool = True, convertDayToHour: bool = False) -> str:
    """Get timestamp duration string.

    Args:
        startTime (datetime): Start time.
        endTime (datetime): End time. None means current time.
        millisecond (bool): True to show millisecond. Default to True.
        microsecond (bool): When both millisecond and microsecond are True to show microsecond. Default to True.
        convertDayToHour (bool): Convert days to hour. Default to False. E.g. convert 1 day to 24 hours.

    Returns:
        Time duration string. [-][9 days, ]hour:minute:second.999999.
        E.g. "19:23:33.123456", "1 day, 19:23:33.123456", "500 days, 19:23:33.123456".

        Example:
        millisecond = True and microsecond = True: Returns hour:minute:second.999999. E.g. "19:23:33.123456".
        millisecond = True and microsecond = False: Returns hour:minute:second.999. E.g. "19:23:33.123".
        millisecond = False and microsecond = False: Returns hour:minute:second. E.g. "19:23:33".
        millisecond = False and microsecond = True: Returns hour:minute:second. E.g. "19:23:33".
    """
    if endTime is None:
        endTime = datetime.now()
    duration = str(endTime - startTime) # hour:minute:second.999999
    r = None
    if millisecond is True and microsecond is True:
        r = duration
    elif millisecond is True and microsecond is False:
        r = duration[:-3]
    else:
        r = duration[0:duration.index('.')]
    if convertDayToHour and 'day' in r:
        # "1 day, 19:23:33.123456", "500 days, 19:23:33.123456"
        # conver day(s) to hour
        days = int(r[0:r.index(' ')])
        r1 = r[r.index(',') + 2:] # 19:23:33.123456
        ss = r1.split(':')
        hours = days * 24 + int(ss[0])
        if len(ss) == 3:
            r = '%s:%s:%s' % (hours, ss[1], ss[2])
        else:
            r = '%s:%s:00' % (hours, ss[1])
    if millisecond and "." not in r:
        # '19:23:33'
        if microsecond:
            r += '.000000'
        else:
            r += '.000'
    if len(r.split(':')) == 2:
        r = '00:%s' % r 
    return r