from datetime import datetime, timezone


def now() -> datetime:
	return datetime.now().astimezone(timezone.utc)
def long_ago() -> datetime:
	return datetime(1990, 1, 1).astimezone(timezone.utc)