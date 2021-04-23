#where the smart stuff goes.
from sys import dont_write_bytecode
from . import data as D
import json, time, copy, sys



class RelatedServerFinder:
	def __init__(self, main):
		self.main = main
		self.data:D.SaveData = self.main.data
		self.server_observations = {} #k = server ID, v = dictionary, where the keys are other server IDs, and the values are integers representing how many connections this server has with the other server
		self.pairings = []
		self.threshold = 4 #at least 5 people in the same server to be considered a server group/cluster
		self.clusters:dict[int, set] = {}
	
	def find_patterns(self):
		for k, v in self.data.users.items():
			for s in v.servers:
				if s not in self.server_observations:
					self.server_observations[s] = {}
				for s2 in v.servers:
					if s2 not in self.server_observations[s] and s2 != s:
						self.server_observations[s][s2] = 0
					if s2 != s:
						self.server_observations[s][s2] += 1
		#ok, now find the pairs of related servers
		#from there we can find whole clusters
		self.pairings = []
		for k1, v1 in self.server_observations.items():
			for k2, v2 in v1.items():
				if v2 >= self.threshold:
					self.pairings.append([k1, k2])
		#sort out the pairings and remove duplicates
		self.pairings = remove_duplicate_lists(self.pairings)
		#self.show_pairings(self.pairings)

		#now find clusters

		self.clusters = {} #dictionary of sets
		for x in self.data.servers:
			self.clusters[int(x)] = set()
		
		#print(len(pairings), "pairings in total")
		
		#this doesn't go very far. We need to go deeper. it only adds the initially apparent related servers. 
		for k, v in self.clusters.items(): #k = server ID, v = cluster set
			for pair in self.pairings:
				if int(k) in pair:
					add_list_to_set(pair, v, exclude=[int(k)])
		
		depth = 3 #how many times to look for related servers.

		for i in range(depth):
			old = copy.deepcopy(self.clusters)
			#connect servers that are indirectly related
			for k, v in old.items():
				#now add things to V from every other related set
				for v2 in v:
					for v3 in old[v2]:
						if v3 != k: self.clusters[k].add(v3) #adds v3 to the real version of V
		
		



	def filter_server_list(self, server_list) -> list[int]: 
		#actually, this should just give an int, representing the number of mutual servers. 
		# clusters will be combined to represent a single server, thus bringing down the mutual server count.
		filtered_server_list = []
		do_not_count = [] #servers that we shouldn't count
		for x in server_list:
			if x not in do_not_count:
				#what are the related servers?
				if x in self.clusters:
					for y in self.clusters[x]:
						do_not_count.append(y)
				else:
					print(self.clusters)
					sys.exit()
				filtered_server_list.append(x)
		
		return filtered_server_list
	


	def show_clusters(self, clusters):
		def s_n(sid):
			return self.data.servers[str(sid)].server_name
		for k, v in clusters.items():
			if len(v) > 0:
				names = []
				for o in v:
					names.append(s_n(o))
				print(s_n(k) + ":", ", ".join(names))

	def show_pairings(self, pairings):
		for x in pairings:
			print("---")
			for y in x: 
				if self.data.servers[str(y)].server_name == None:
					self.main.fully_process_server(y)
					time.sleep(.7)
				name = self.data.servers[str(y)].server_name
				print(name, " " * (100-len(name)), y)
		print("---")
		

def add_list_to_set(l, s, convert=int, exclude=[]):
	for x in l:
		if x not in exclude:
			s.add(convert(x))

def remove_duplicate_lists(l:list):
	kvp = {}
	for x in l: 
		x.sort()
		kvp[str(x)] = x
	newlist = []
	for k, v in kvp.items():
		newlist.append(v)
	return newlist






"""drafting out the idea
pairs

[A, B]
[B, C]

a and b are related, b and c are also related, so we should make a few cluster defs for a, b, and c
A: [B, C]
B: [A, C]
C: [A, B]
how do we do that with [A, B], [B, C]? Because [A, C] isn't in there, so it won't be seen as directly related

well, at first, it looks like this

A: [B]
B: [C]

go through the sets
#0 A: [B]
add things to A by looking at set B
	B: [C], so add C to A

"""
