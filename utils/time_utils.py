import datetime
from dateutil import tz
import inspect

class TimeInterval:
	DAILY = "daily"
	WEEKLY = "weekly"
	BIWEEKLY = "biweekly"
	MONTHLY = "monthly"

	INTERVALS = (
		DAILY,
		WEEKLY,
		BIWEEKLY,
		MONTHLY
	)

	@classmethod
	def format_interval_datetime(klass, interval, cur_date):
		day = cur_date.day
		if interval != TimeInterval.DAILY:
			if interval == TimeInterval.WEEKLY:
				if day < 8: day = 1
				elif day < 16: day = 8
				elif day < 24: day = 16
				else: day = 24
			elif interval == TimeInterval.BIWEEKLY:
				if day < 16: day = 1
				else: day = 16
			elif interval == TimeInterval.MONTHLY:
				day = 1

		return datetime.datetime(cur_date.year, cur_date.month, day)

def benchmark_time(name=None, print_args=True):
	def decorator(fn):
		def fn_body(*args, **kwargs):
			start_time=datetime.datetime.now()

			results = fn(*args, **kwargs)

			fn_name = inspect.getmodule(fn).__name__
			end_time = datetime.datetime.now()
			time_elapsed=(end_time-start_time).total_seconds()

			time_components = []
			seconds_left = time_elapsed

			hours = int(seconds_left/3600)
			seconds_left -= hours*3600
			if hours > 0: time_components.append("{}h".format(hours))

			minutes = int(seconds_left/60)
			seconds_left -= minutes*60
			if minutes > 0: time_components.append("{}m".format(minutes))

			time_components.append("{:.2f}s".format(seconds_left))
			time_str = " ".join(time_components)

			arg_str = " (args={} | kwargs={})".format(args, kwargs) if print_args else ""
			print("benchmark_time Name:    {}{}".format((name or fn_name), arg_str))
			print("benchmark_time Took:    {}".format(time_str))
			print("benchmark_time Started: {}".format(start_time))
			print("benchmark_time Ended:   {}".format(end_time))
			print("benchmark_time ----------")
			return results
		return fn_body
	return decorator

def datetime_to_date(dt):
	utc_timezone = tz.gettz('UTC')
	new_dt = datetime.datetime(
		year=dt.year,
		month=dt.month,
		day=dt.day
	).replace(tzinfo=utc_timezone)
	return new_dt

def today():
	cur_datetime = datetime.datetime.now()
	return datetime_to_date(cur_datetime)

def arg_date_range_to_fn(date_range_str, fn):
	start_date_str, end_date_str = date_range_str.split("-")
	start_date_str = "/".join(start_date_str.split("/")[:3])
	end_date_str = "/".join(end_date_str.split("/")[:3])

	date_range_str = "{}-{}".format(start_date_str, end_date_str)

	start_date, end_date = date_range_str.split("-")

	start_date = fn(start_date)
	end_date = fn(end_date, day_offset=1)
	return (start_date, end_date, date_range_str)

def arg_date_range_to_datetime(date_range_str):
	return arg_date_range_to_fn(date_range_str, arg_date_str_to_datetime)

def arg_date_range_to_epoch_time(date_range_str):
	return arg_date_range_to_fn(date_range_str, arg_date_str_to_epoch_time)

def arg_date_str_to_datetime(date_str, day_offset=0):
	date_components = date_str.split("/")

	if len(date_components) < 2:
		raise Exception("Dates are of the format M/D/Y, Y is Optional")

	if len(date_components) < 3:
		date_components.append(datetime.date.today().year)

	month, day, year = [int(x) for x in date_components[:3]]

	if year<1000: year += 2000

	pst_timezone = tz.gettz('PST')
	local_datetime = datetime.datetime(year, month, day).replace(tzinfo=pst_timezone)
	local_datetime += datetime.timedelta(days=day_offset)
	return local_datetime

def arg_date_str_to_epoch_time(date_str, day_offset=0):
	local_datetime = arg_date_str_to_datetime(date_str, day_offset)

	utc_timezone = tz.gettz('UTC')
	epoch_datetime = datetime.datetime(1970, 1, 1).replace(tzinfo=utc_timezone)

	epoch_time = (local_datetime - epoch_datetime).total_seconds()
	return epoch_time

def utc_str_to_date(t):
	t = t.replace("T", " ")
	t = t.split("+")[0]
	if "." not in t: t = t+".0"
	utc_timezone = tz.gettz('UTC')
	return datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=utc_timezone)

def utc_to_epoch_time(t):
	utc_timezone = tz.gettz('UTC')
	utc_time = utc_str_to_date(str(t))
	epoch_datetime = datetime.datetime(1970, 1, 1).replace(tzinfo=utc_timezone)
	epoch_time = (utc_time - epoch_datetime).total_seconds()
	return epoch_time

def epoch_time_to_utc_datetime(t):
	return datetime.datetime.utcfromtimestamp(t)

def epoch_time_to_local_datetime(t):
	return datetime.datetime.fromtimestamp(t)

def utc_to_local_datetime(d):
	pst_timezone = tz.gettz('PST')
	return d.replace(tzinfo=pst_timezone)

def utc_str_to_local_datetime(t):
	utc_d = utc_str_to_date(t)
	return utc_to_local_datetime(utc_d)