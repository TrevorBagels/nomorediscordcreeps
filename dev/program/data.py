from prodict import Prodict
from datetime import datetime
from .utils import now
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
	def init(self):
		self.user_joined = datetime.now()


class Server(Prodict):
	server_id:		int
	server_name:	str
	members:		dict[str, Member]

class Stalker(Prodict):
	user_id:		int
	server_hash:	str
	time_found:		datetime
	def init(self):
		self.time_found = now()

class SaveData(Prodict):
	servers:				dict[str, Server]
	users:					dict[str, User]
	user_processing_queue:	list[int]
	stalkers:				dict[str, Stalker]
	first_time:				bool
	def init(self):
		self.servers = {}
		self.first_time = True
		self.users = {}
		self.user_processing_queue = []
		self.stalkers = {}