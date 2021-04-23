from collections import UserDict
from datetime import datetime
from discord.ext import tasks
import discord, prodict, asyncio, json, requests
from bson import json_util
from . import data as D
from .utils import now, long_ago
from .notify import Notifier

class Config(prodict.Prodict):
	token:				str
	check_frequency:	int #how frequently, in minutes, to do a profile check on someone.
	servers_alert_level:	int #how many mutual servers does someone need to be in to be considered a potential threat?
	ignore_servers:			list[int] #servers to ignore
	ignore_users:			list[int] #users to ignore
	save_frequency:			int #seconds, how frequently to save
	pushover_token:			str
	pushover_user:			str
	bots_can_stalk:			bool #ignore bots
	friends_can_stalk:		bool #ignore friends
	scrape_amount:			int #amount of messages to scrape for the initial scrape, divided by 50.
	false_positive_level:	int #how many people need to be found in clusters of servers for that cluster of servers to be considered a related server cluster?

	def init(self):
		self.ignore_servers = []
		self.ignore_users = []
		self.check_frequency = 5 #minutes
		self.servers_alert_level = 3
		self.save_frequency = 5
		self.bots_can_stalk = False
		self.friends_can_stalk = False
		self.scrape_amount = 1


class Me(discord.Client):
	def __init__(self):
		with open("config.json", "r") as f:
			self.config = Config.from_dict(json.loads(f.read()))
		self.last_save = now()
		self.token = self.config.token
		self.load()
		self.notifier = Notifier(self)
		self.auth = {"authorization": self.token}
		discord.Client.__init__(self, self_bot=True)
	
	def save(self):
		with open("data.json", "w") as f:
			f.write(json.dumps(self.data.to_dict(is_recursive=True), default=json_util.default, indent=4))
	
	def load(self):
		with open("data.json", "r") as f:
			self.data:D.SaveData = D.SaveData.from_dict(json.loads(f.read(), object_hook=json_util.object_hook))

	def get_friends(self): #!makes a single api call
		relationships_req = requests.get(f"https://discord.com/api/v9/users/@me/relationships", headers=self.auth)
		friends = []
		if relationships_req.ok:
			for x in relationships_req.json():
				friends.append(int(x['id']))
		else:
			print("Couldn't find friends")
		return friends


	async def on_ready(self):
		print(self.user.display_name + " connected to Discord!")
		if self.user.id not in self.config.ignore_users:
			self.config.ignore_users.append(self.user.id)
		if self.config.friends_can_stalk == False:
			for x in self.get_friends():
				if x not in self.config.ignore_users:
					self.config.ignore_users.append(x)
		
		if self.data.first_time:
			self.data.first_time = False
			await self.initial_scrape()
	
	async def begin(self):
		await self.start(self.token, bot=False)

	#async def on_member_join(self, member:discord.Member): doesn't work

	async def on_message(self, message: discord.Message): #this always works, so we can just do a check on the mentions and the author
		if message.guild != None and int(message.guild.id) in self.config.ignore_servers:
			return
		if message.guild != None: self.process_server(message.guild.id, name=message.guild.name)
		server = None
		if message.guild != None:
			server = message.guild.id
		joined_at = None
		if hasattr(message.author, "joined_at"): joined_at = message.author.joined_at
		self.process_user(message.author.id, server=server, joined=joined_at, name=message.author.name, bot=message.author.bot)
		for x in message.mentions:
			joined_at = None
			if hasattr(x, "joined_at"): joined_at = x.joined_at
			self.process_user(x.id, server=server, joined=joined_at, name=x.name, bot=x.bot)
	
	async def main_loop(self):
		while True:
			#check on new members in the queue
			if len(self.data.user_processing_queue) > 0:
				#process user
				await self.fully_process_user(self.data.user_processing_queue[0]) #!makes api calls
				#remove processed user from the queue
				self.data.user_processing_queue.remove(self.data.user_processing_queue[0])
			if (now() - self.last_save).total_seconds() > self.config.save_frequency:
				self.save()
				self.last_save = now()
			await asyncio.sleep(.5)


	async def initial_scrape(self): #! MAKES LOTS OF API CALLS. I MEAN   L O T S   O F   T H E M
		"""This method scrapes and processes messages from all servers.
		 It takes awhile, but can generate a decent amount of data.
		"""
		
		me_req = requests.get(f"https://discord.com/api/v9/users/{self.user.id}/profile", headers=self.auth)
		profile:D.Profile_API = D.Profile_API.from_dict(me_req.json())
		for guild in profile.mutual_guilds:
			channels = requests.get(f"https://discord.com/api/v9/guilds/{guild.id}/channels", headers=self.auth)
			for c in channels.json():
				if c['type'] != 0 or 'last_message_id' not in c: continue
				#get the channel permissions (removed this because it doesn't work or something and i'm tired)
				"""
				channel = self.get_channel(c['id'])
				me = self.get_guild(guild.id).get_member(self.user.id)
				print(me)
				perms = channel.permissions_for(me)
				if (perms.view_channel and perms.read_messages) == False: continue
				"""
				last_message = c['last_message_id']
				
				for i in range(self.config.scrape_amount):
					msgs = requests.get(f"https://discord.com/api/v9/channels/{c['id']}/messages?before={last_message}&limit=50", headers=self.auth).json()
					for x in msgs:
						if type(x) == str: 
							msgs = "NO" * 100 #thats more than 50, so it should break the loop and skip this channel
							break
						if 'bot' not in x['author']:
							x['author']['bot'] = False
						self.process_user(int(x['author']['id']), server=int(guild.id), name=x['author']['username'], bot=x['author']['bot'])
						last_message = x['id']
					if len(msgs) < 50:
						break
					await asyncio.sleep(.08)
			
			print(f"scraped {guild.id}")

		print('initial scrape done!')
					
					
					

			


	def process_server(self, server_id, name=None):
		if str(server_id) not in self.data.servers:
			self.data.servers[str(server_id)] = D.Server(server_id=server_id, members={})
		if name != None:
			self.data.servers[str(server_id)].server_name = name
		
	def fully_process_server(self, server_id):
		server_req = requests.get(f"https://discord.com/api/v9/guilds/{server_id}", headers=self.auth)
		if server_req.ok:
			guild:D.Guild_API = D.Guild_API.from_dict(server_req.json())
			server = self.data.servers[str(server_id)]
			server.server_name = guild.name


	def process_user(self, user_id, server=None, joined=None, name=None, bot=False):
		if int(user_id) in self.config.ignore_users: return
		if str(user_id) not in self.data.users:
			self.data.users[str(user_id)] = D.User(user_id=user_id, servers=[], last_profile_check=long_ago(), bot=bot)
			if name is not None: self.data.users[str(user_id)].username = name
		
		if (now() - self.data.users[str(user_id)].last_profile_check).total_seconds() / 60 >= self.config.check_frequency and user_id not in self.data.user_processing_queue:
			self.data.user_processing_queue.append(user_id)
		if server is not None and int(server) not in self.data.users[str(user_id)].servers: #add server if provided
			self.process_server(server)
			self.data.users[str(user_id)].servers.append(int(server))
			self.data.servers[str(server)].members[str(user_id)] = D.Member(user_id=user_id)
			if joined != None:
				self.data.servers[str(server)].members[str(user_id)].user_joined = joined
	

	async def fully_process_user(self, user_id):
		profile_req = requests.get(f"https://discord.com/api/v9/users/{user_id}/profile", headers=self.auth)
		if profile_req.ok: #usually fails if the user is a bot
			profile:D.Profile_API = D.Profile_API.from_dict(profile_req.json())
			#process user servers
			user = self.data.users[str(user_id)]

			for server in profile.mutual_guilds:
				if int(server.id) in self.config.ignore_servers: continue
				if int(server.id) not in user.servers:
					user.servers.append(server.id)
					self.process_server(server.id)
					self.data.servers[str(server.id)].members[str(user_id)] = D.Member(user_id=user_id, nickname=server.nick)

			for connection in profile.connected_accounts:
				hashed = str(hash(str(connection)))
				if hashed not in user.connections:
					user.connections[hashed] = connection

			user.last_profile_check = now() #profile check finished.
			#are they stalking us?
			await self.check_stalking(user)

	async def check_stalking(self, user:D.User):
		if len(user.servers) >= self.config.servers_alert_level and (user.bot == False or self.config.bots_can_stalk):
			if str(user.user_id) not in self.data.stalkers:
				user.servers.sort()
				self.data.stalkers[str(user.user_id)] = D.Stalker(user_id=user.user_id, server_hash=str(user.servers))
				servers = []
				for x in user.servers:
					s = self.data.servers[str(x)]
					if s.server_name == None:
						self.fully_process_server(s.server_id) #!makes api calls
						await asyncio.sleep(.2)
					if s.server_name == None:
						servers.append(str(s.server_id))
					else:
						servers.append(s.server_name)
				message = f"This user is in {len(user.servers)} mutual servers.\nServers: {', '.join(servers)}"
				self.notifier.alert(f"{user.username} MIGHT BE STALKING YOU!\n{message}")
			elif self.data.stalkers[str(user.user_id)].server_hash != str(user.servers):
				self.data.stalkers[str(user.user_id)].server_hash = str(user.servers)
				self.notifier.alert(f"{user.username} MAY STILL BE STALKING YOU!\nThere was a change in mutual servers that they're in. They are now in {len(user.servers)} mutual servers")
				
	
	





