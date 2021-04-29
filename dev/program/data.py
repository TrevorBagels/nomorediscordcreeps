#contains the data structure for things

from collections import UserDict
from discord import channel, message
from prodict import Prodict
from datetime import datetime, timedelta
from .utils import now
from . import utils
class MutualGuild_API(Prodict):
	id:		int
	nick:	str
class User_API(Prodict):
	avatar: 			str
	discriminator: 		int
	flags:				int
	id:					int
	public_flags:		int
	username:			str

class Profile_API(Prodict):
	user:				dict
	connected_accounts:	list
	mutual_guilds:		list[MutualGuild_API]

class Guild_API(Prodict):
	id:				int
	name:			str
	icon:			str
	description:	str
	splash:			str
	discovery_splash:			str
	approximate_member_count:	int
	approximate_presence_count:	int
	features:					list[str]
	emojis:						list
	banner:						str
	owner_id:					int
	region:						str

class User(Prodict):
	user_id:			int
	username:			str
	discriminator:		int
	bot:				bool
	servers:			list[int]
	last_profile_check:	datetime
	connections:		dict
	def init(self):
		self.connections = {}
		self.servers = []
		self.bot = False



class Member(Prodict):
	user_id:		int
	nickname:		str
	user_joined:	datetime #datetime
	messages:		int
	def init(self):
		self.user_joined = datetime.now()
		self.messages = 0

class LongHistory(Prodict):
	current_count: 	int
	measure_start: 	datetime #should be measured every 30 seconds
	history_seconds:	list[tuple[datetime, int]] #intervals of 30 seconds
	history_hour:		list[tuple[datetime, int]] #intervals of five minutes
	history_day:		list[tuple[datetime, int]] #intervals of one hour
	history_days:		list[tuple[datetime, int]] #intervals of one day
	interval_speed:		int	#how many seconds between each update. default is 30
	five_minute_cache:	list[tuple[datetime, int]] #a list of data from history_hour. This list isn't cleared, though, instead, it starts clearing itself after it reaches a length of 240
	hourly_cache:		list[tuple[datetime, int]] #same as five minute cache, but for each hour. length = 14 days (336 items)
	auto_reset:			bool

	def init(self):
		self.current_count = 0
		self.measure_start = now()
		self.history_seconds 	= []
		self.history_hour 		= []
		self.history_day 		= []
		self.history_days		= []
		self.interval_speed		= 30
		self.five_minute_cache = self.history_hour.copy()
		self.hourly_cache = self.history_day.copy() 
		self.auto_reset = True
	
	def time_range(self, values:list[tuple[datetime, int]]):
		if len(values) < 1:
			return timedelta(seconds=0)
		return utils.round_seconds_delta(values[len(values) - 1][0] - values[0][0])
	
	def add_to_fixed_list(self, value, l:list, length=240):
		l.append(value)
		if len(l) > length:
			l.pop(0)

	def get_totals(self, values:list[tuple[datetime, int]]) -> tuple:
		total_values = 0
		if self.auto_reset == True:
			for x in values:
				total_values += x[1]
		elif len(values) > 0:
			total_values = values[len(values)-1][1]
		return (values[0][0], total_values)

	def take_measurement(self, timestamp=None):
		if timestamp == None: timestamp = now()
		measurement = (self.measure_start, self.current_count)
		self.history_seconds.append(measurement)
		if self.auto_reset:
			self.current_count = 0
		self.measure_start = timestamp
		#do we need to clear the seconds, and push it to five minute intervals?
		#add timedelta(seconds=30) because each interval is 30 seconds, but we only record the start of the interval. this makes up for the ending part of the interval / the interval length
		need_update = self.time_range(self.history_seconds) + timedelta(seconds=self.interval_speed) >= timedelta(minutes=5)
		if need_update: self.update_minutes() 

	def update_minutes(self): #resets history_seconds, adds the total to history_hour
		totals = self.get_totals(self.history_seconds)
		self.history_hour.append(totals)
		self.add_to_fixed_list(totals, self.five_minute_cache)
		self.history_seconds = []
		#update when we reach a new hour
		need_update = self.history_hour[0][0].hour != self.history_hour[len(self.history_hour)-1][0].hour
		#need_update = self.time_range(self.history_hour) + timedelta(minutes=5) >= timedelta(hours=1)
		if need_update: self.update_day()

	def update_day(self): #resets history_hour, adds the total to history_day
		totals = self.get_totals(self.history_hour)
		self.history_day.append(totals)
		self.add_to_fixed_list(totals, self.hourly_cache, length=336)
		self.history_hour = []
		need_update = self.history_day[0][0].day != self.history_day[len(self.history_day)-1][0].day
		#need_update = self.time_range(self.history_day) + timedelta(hours=1) >= timedelta(days=1)
		if need_update: self.update_days()
	
	def update_days(self): #resets history_day, adds the total to history_days
		self.history_days.append(self.get_totals(self.history_day))
		self.history_day = []
	

		



class Channel(Prodict):
	channel_id:		int
	channel_name:	str
	

class Server(Prodict):
	server_id:		int
	server_name:	str
	members:		dict[str, Member]
	rate_history:	LongHistory
	member_history:	LongHistory
	channels:		dict[str, Channel] #channel ID, channel name
	recent_messages:	list[tuple[datetime, int, int, str]] #time of message, user ID, channel ID, message content. fixed size of 50.
	
	def init(self):
		self.rate_history = LongHistory()
		self.member_history = LongHistory(auto_reset=False)
		self.recent_messages = []
		self.channels = {}
	
	def process_channel(self, channel_id, channel_name):
		if str(channel_id) not in self.channels:
			self.channels[str(channel_id)] = Channel(channel_id = channel_id, channel_name = channel_name)


	def on_message(self, timestamp:datetime, user_id:int, channel_id:int, content:str):
		self.recent_messages.append((timestamp, user_id, channel_id, content))
		if len(self.recent_messages) > 50:
			self.recent_messages.pop(0)
		

class Stalker(Prodict):
	user_id:		int
	server_hash:	str
	time_found:		datetime
	def init(self):
		self.time_found = now()

class Message(Prodict):
	time_sent:		datetime #(UTC)
	author_id:		int
	server_id:		int
	channel_id:		int
	message_id:		int
	content:		str
	reply_to:		int #None if it isn't a reply
	mentions:		list[int] #people that this message mentions (as IDs)




class Stalkee(Prodict): #someone that you just so happen to be counter-stalking. or maybe you're stalking them even though they aren't stalking you.
	user_id:		int
	activities:		dict[str, LongHistory] #to keep track of what they do. with fine details, yaknow? key=activity name, value=history (where the y value is time spent doing activity)
	aliases:		list[tuple[datetime, str]] #history of their aliases
	messages:		list[Message]
	

class SaveData(Prodict):
	servers:				dict[str, Server]
	users:					dict[str, User]
	user_processing_queue:	list[int]
	stalkers:				dict[str, Stalker]
	first_time:				bool
	user_discovery:			list[tuple[int, datetime]] #list of newly discovered users
	montitored_users:		dict[str, Stalkee]
	def init(self):
		self.servers = {}
		self.first_time = True
		self.users = {}
		self.user_processing_queue = []
		self.stalkers = {}
		self.user_discovery = []