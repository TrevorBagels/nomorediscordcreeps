from datetime import datetime, timezone, timedelta


def now() -> datetime:
	return datetime.now().astimezone(timezone.utc)
def long_ago() -> datetime:
	return datetime(1990, 1, 1).astimezone(timezone.utc)

def hms(seconds):
	"""Returns h:m:s from seconds
	"""
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return "%d:%02d:%02d" % (hour, minutes, seconds)

def dhms(seconds):
	"""Returns d days, h:m:s from seconds
	"""
	days = seconds // 86400
	seconds = seconds % (24 * 3600)
	hour = seconds // 3600
	seconds %= 3600
	minutes = seconds // 60
	seconds %= 60
	return  f"{days} day(s), " + "%d:%02d:%02d" % (hour, minutes, int(seconds))

def time_elapsed(seconds):
	if seconds < 60:
		return f"{'%02d' % seconds}s"
	minutes = seconds // 60
	if minutes < 60:
		return f"{'%02d' % minutes}m {'%02d' % (seconds - minutes*60)}s"
	return hms(seconds)

def time_elapsed_1(seconds):
	if seconds < 60:
		return f"{'%02d' % seconds} seconds"
	minutes = seconds // 60
	if minutes < 60:
		return f"{'%02d' % round(minutes + seconds/60, 1)} minutes"
	return hms(seconds)

def round_seconds_datetime(dt: datetime) -> datetime:
    if dt.microsecond >= 500_000:
        dt += timedelta(seconds=1)
    return dt.replace(microsecond=0)

def round_seconds_delta(dt: timedelta) -> timedelta:
    if dt.microseconds >= 500_000:
        dt += timedelta(seconds=1, microseconds=-dt.microseconds)
    return dt