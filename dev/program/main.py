from collections import UserDict
from datetime import datetime, timedelta
from discord.ext import tasks
import discord, prodict, asyncio, json, requests, sys, time
from bson import json_util
from requests.sessions import HTTPAdapter
from . import data as D
from .utils import now, long_ago
from .notify import Notifier
from . import smartstuff
from requests.packages.urllib3.util.retry import Retry

import faker, random


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
	scrape_amount:			int #amount of messages to scrape for the initial scrape, divided by 50. default is one (so it scrapes the last 50 messages from each channel)
	scrape_guild_count:		int #max amount of guilds to scrape on the initial scrape. default = 100
	false_positive_level:	int #how many people need to be found in clusters of servers for that cluster of servers to be considered a related server cluster?
	block_scanning:			bool #whether to stop scanning user profiles. used when getting ratelimited
	disable_stalker_flagging:	bool #set this to true if you don't want to check for stalkers. this is automatically true while doing an initial scan
	disable_profile_api_calls:	bool #set this to true if you don't want to run fully_process_user. this also disabled stalker flagging.
	max_servers_to_scrape:	int #how many servers do you want the initial scrape to cover?
	max_channels_to_scrape:	int #how many channels to scrape per server
	def init(self):
		self.ignore_servers = []
		self.ignore_users = []
		self.check_frequency = 5 #minutes
		self.servers_alert_level = 3
		self.save_frequency = 30
		self.bots_can_stalk = False
		self.friends_can_stalk = False
		self.scrape_amount = 1
		self.block_scanning = False
		self.scrape_guild_count = 100
		self.disable_stalker_flagging = False
		self.disable_profile_api_calls = False
		self.max_channels_to_scrape = 20
		self.max_servers_to_scrape = 100


class Me(discord.Client):
	def __init__(self):
		from .managedata import ManageData
		with open("config.json", "r") as f:
			self.config = Config.from_dict(json.loads(f.read()))
		self.last_save = now()
		self.token = self.config.token
		self.load()
		self.start_time = now()
		self.measure_message_rates()
		self.cluster_finder = smartstuff.RelatedServerFinder(self)
		self.notifier = Notifier(self)
		#self.cloudscraper = cloudscraper.create_scraper()
		self.faker = faker.Faker()
		self.auth = {"authorization": self.token, "user-agent": self.faker.user_agent()}
		self.has_connected = False
		self.req_log_last_cleared = time.time()
		self.req_log = []
		self.ignore_users = self.config.ignore_users.copy()
		self.last_rate_measurement = time.time()
		self.message_rate_watcher.start()
		self.reqs = requests.Session()
		retries = Retry(connect=3, backoff_factor=2.5)
		self.reqs.mount("http://", HTTPAdapter(max_retries=retries))
		#for repairing (04/28/21)
		"""
		for _, s in self.data.servers.items():
			del s["member_history"]
			to_repair = [s.rate_history.history_hour, s.rate_history.history_day, s.rate_history.five_minute_cache, s.rate_history.hourly_cache]
			for r in to_repair:
				for i, x in enumerate(r):
					if type(x[1]) != int:
						r[i] = (x[0], x[1][1])
		print("done")
		time.sleep(5)
		self.save()
		"""
		discord.Client.__init__(self, self_bot=True)
	
	def ignore_user(self, user_id):
		self.config.ignore_users.append(user_id)
		self.ignore_users.append(user_id)

	def get(self, url, headers={}):
		req = None
		try:
			
			req = self.reqs.get(url, headers=headers)
			#req = self.cloudscraper.get(url, headers=headers)
			self.req_log.append([url, req.content.decode(), str(req.headers), str(req.cookies)])
		except Exception as e:
			print("Request failed!", "\n", e)
		return req

	def measure_message_rates(self):
		print("Measure rates")
		for _, server in self.data.servers.items():
			server.rate_history.take_measurement()
			server.member_history.current_count = len(server.members)
			server.member_history.take_measurement()
		self.last_rate_measurement = time.time()


	def get_account_creation_date(self, user_id) -> datetime:
		epoch = (datetime(year=2015, day=1, minute=1, month=1, second=0))
		binary = format(int(user_id), "b")
		ms_since_epoch = int(binary[:(len(binary) - 22)], 2)
		totaltime = epoch + timedelta(milliseconds=ms_since_epoch)
		return totaltime

	def save(self):
		print("Saving... Do not stop the program while this operation takes place.")
		with open("data.json", "w") as f:
			f.write(json.dumps(self.data.to_dict(is_recursive=True), default=json_util.default, indent=4))
		with open("config.json", "w+") as f:
			f.write(json.dumps(self.config.to_dict(is_recursive=True), default=json_util.default, indent=4))
		with open("requestslog.json", "w+") as f:
			f.write(json.dumps(self.req_log, default=json_util.default, indent=4))
		print("Saved!")
	
	def load(self):
		with open("data.json", "r") as f:
			self.data:D.SaveData = D.SaveData.from_dict(json.loads(f.read(), object_hook=json_util.object_hook))

	def get_friends(self): #!makes a single api call
		relationships_req = self.get(f"https://discord.com/api/v9/users/@me/relationships", headers=self.auth)
		friends = []
		if relationships_req.ok:
			for x in relationships_req.json():
				friends.append(int(x['id']))
		else:
			print("Couldn't find friends")
		return friends


	async def on_ready(self):
		print(self.user.display_name + " connected to Discord!")
		if self.user.id not in self.ignore_users:
			self.ignore_users.append(self.user.id)
		if self.config.friends_can_stalk == False:
			for x in self.get_friends():
				if x not in self.ignore_users:
					self.ignore_users.append(x)
		
		if self.data.first_time:
			self.data.first_time = False
			await self.initial_scrape()
		
		self.cluster_finder.find_patterns() #identify related servers to avoid false positives		
		self.config.disable_stalker_flagging = self.disable_stalker_flagging_original #set stalker detection to the original value
		self.has_connected = True
	

	async def begin(self):
		self.disable_stalker_flagging_original = self.config.disable_stalker_flagging #temporarily disable stalker detection
		self.config.disable_stalker_flagging = True
		await self.start(self.token, bot=False)

	#async def on_member_join(self, member:discord.Member): doesn't work

	async def on_message(self, message: discord.Message): #this always works, so we can just do a check on the mentions and the author
		if message.guild != None and int(message.guild.id) in self.config.ignore_servers:
			return
		server = None
		if message.guild != None: 
			self.process_server(message.guild.id, name=message.guild.name)
			server = message.guild.id
			svr = self.data.servers[str(server)]
			svr.process_channel(message.channel.id, message.channel.name)
			svr.on_message(message.created_at, message.author.id, message.channel.id, message.content)
		if server != None:
			self.data.servers[str(server)].rate_history.current_count += 1
		joined_at = None
		if hasattr(message.author, "joined_at"): joined_at = message.author.joined_at
		self.process_user(message.author.id, server=server, joined=joined_at, name=message.author.name, disc=message.author.discriminator, bot=message.author.bot)
		for x in message.mentions:
			joined_at = None
			if hasattr(x, "joined_at"): joined_at = x.joined_at
			self.process_user(x.id, server=server, joined=joined_at, name=x.name, disc=x.discriminator, bot=x.bot)
	
	@tasks.loop(seconds=10)
	async def message_rate_watcher(self):
		if time.time() - self.last_rate_measurement >= 29.99:
			self.measure_message_rates()
	
	async def main_loop(self):
		while True:
			getting_ready_printed_already = False
			while self.has_connected == False:
				if getting_ready_printed_already == False:
					print("getting ready...")
					getting_ready_printed_already = True
				await asyncio.sleep(.3)
			#check on new members in the queue
			if self.config.block_scanning == False:
				for i in range(2):
					if len(self.data.user_processing_queue) > 0:
						#process user
						req = await self.fully_process_user(self.data.user_processing_queue[0]) #!makes api calls
						#because i'm scared of ratelimiting. note: this doesn't really happen anymore, i've "perfected" the program to not exceed ratelimits. but it's still here because, you know, paranoia.
						if "ratelimit" in req.content.decode().lower() or "ratelimit" in str(req.headers).lower():
							print("VVV RATELIMITING? VVV")
							print(req.content.decode())
							print(req.headers)
							print("^^^ RATELIMITING? ^^^")
							sys.exit()
						
						#remove processed user from the queue
						self.data.user_processing_queue.remove(self.data.user_processing_queue[0])
						if req.ok == False and req.json()['code'] != 50001:
							await asyncio.sleep(3 + random.random() * 5) #sleep, we probably made a bad request. too many of these is bad. hopefully we aren't being ratelimited
						await asyncio.sleep(1.5 + random.random() * 2.5)
			
			if (now() - self.last_save).total_seconds() > self.config.save_frequency:
				self.save()
				self.last_save = now()
			
			await asyncio.sleep(1.5 + random.random() * 3)

			if len(self.req_log) > 30 * (time.time() - self.req_log_last_cleared)/60 + random.randrange(-10, 10) or time.time() - self.req_log_last_cleared > 180: #take a break if we get near 30 requests in under a minute
				print("taking a break!")
				self.save()
				await asyncio.sleep(random.randrange(25, 70))
				self.req_log = [] #clear request log
				self.req_log_last_cleared = time.time()
				await asyncio.sleep(3)



	async def initial_scrape(self): #! MAKES LOTS OF API CALLS. I MEAN   L O T S   O F   T H E M
		"""This method scrapes and processes messages from all servers.
		 It takes awhile, but can generate a decent amount of data.
		"""
		#region scraping stuff
		me_req = self.get(f"https://discord.com/api/v9/users/{self.user.id}/profile", headers=self.auth)
		profile:D.Profile_API = D.Profile_API.from_dict(me_req.json())
		servers_scraped = 0
		for guild in profile.mutual_guilds:
			if servers_scraped >= self.config.max_servers_to_scrape: break
			await self.scrape_server(guild.id)
			servers_scraped += 1
		#endregion
		print('initial scrape done!', "scraped", servers_scraped, "server(s)")
		
	async def scrape_server(self, guild_id):
		channels = self.get(f"https://discord.com/api/v9/guilds/{guild_id}/channels", headers=self.auth)
		if channels == None:
			print("Failed to scrape server! Something went wrong with the request.")
			return
		channels_scraped = 0
		for c in channels.json():
			if channels_scraped >= self.config.max_channels_to_scrape:
				break
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
				msgs = self.get(f"https://discord.com/api/v9/channels/{c['id']}/messages?before={last_message}&limit=50", headers=self.auth).json()
				for x in msgs:
					if type(x) == str: #this happens when we don't have access to the channel.
						msgs = "NO" * 100 #thats more than 50, so it should break the loop and skip this channel
						channels_scraped -= 1
						break
					if 'bot' not in x['author']:
						x['author']['bot'] = False
					self.process_user(int(x['author']['id']), server=int(guild_id), name=x['author']['username'], disc=x['author']['discriminator'], bot=x['author']['bot'])
					last_message = x['id']
				if len(msgs) < 50:
					break
				channels_scraped += 1
				await asyncio.sleep(.08)
		
		print(f"scraped {guild_id}")
					
					
					

			


	def process_server(self, server_id, name=None):
		if str(server_id) not in self.data.servers:
			self.data.servers[str(server_id)] = D.Server(server_id=server_id, members={})
		if name != None:
			self.data.servers[str(server_id)].server_name = name
		
	def fully_process_server(self, server_id):
		server_req = self.get(f"https://discord.com/api/v9/guilds/{server_id}", headers=self.auth)
		if server_req == None:
			print("Something went wrong when processing server", server_id)
		if server_req.ok:
			guild:D.Guild_API = D.Guild_API.from_dict(server_req.json())
			server = self.data.servers[str(server_id)]
			server.server_name = guild.name


	def process_user(self, user_id, server=None, joined=None, name=None, disc=None, bot=False):
		#if int(user_id) in self.ignore_users: return
		if str(user_id) not in self.data.users:
			self.data.user_discovery.append((now(), int(user_id)))
			self.data.users[str(user_id)] = D.User(user_id=user_id, servers=[], last_profile_check=long_ago(), bot=bot)
			if name is not None: 
				self.data.users[str(user_id)].username = name
				self.data.users[str(user_id)].discriminator = disc
		if self.data.users[str(user_id)].discriminator == None and disc != None:
			self.data.users[str(user_id)].discriminator = disc
		if int(user_id) not in self.ignore_users and (now() - self.data.users[str(user_id)].last_profile_check).total_seconds() / 60 >= self.config.check_frequency and user_id not in self.data.user_processing_queue:
			self.data.user_processing_queue.append(user_id)
		if server is not None and int(server) not in self.data.users[str(user_id)].servers: #add server if provided
			self.process_server(server)
			self.data.users[str(user_id)].servers.append(int(server))
			self.data.servers[str(server)].members[str(user_id)] = D.Member(user_id=user_id)
			if joined != None:
				self.data.servers[str(server)].members[str(user_id)].user_joined = joined
	

	async def fully_process_user(self, user_id):
		if self.config.disable_profile_api_calls: return
		profile_req = self.get(f"https://discord.com/api/v9/users/{user_id}/profile", headers=self.auth)
		if profile_req == None:
			print("Failed to process user ", user_id)
			print("Something went wrong with the request.")
			await asyncio.sleep(30) #sleep for a bit, give it a chance to work again
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
			if self.config.disable_stalker_flagging == False:
				await self.check_stalking(user)
			else: print(f"Did not check {user_id} to see if they're stalking you")
			print("user processed")
		else:
			#usually, a code 50001/missing access, will mean that the user is no longer in any mutual servers
			print(user_id, profile_req.content)
			if "Access denied" in profile_req.content.decode(): #ratelimiting by cloudflare
				await asyncio.sleep(120)
		return profile_req

	async def check_stalking(self, user:D.User):
		filtered_servers = self.cluster_finder.filter_server_list(user.servers)
		if len(filtered_servers) >= self.config.servers_alert_level and (user.bot == False or self.config.bots_can_stalk):
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