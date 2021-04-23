#where the smart stuff goes.
from . import data as D
import json


class RelatedServerFinder:
	def __init__(self, main):
		self.main = main
		self.data:D.SaveData = self.main.data
		self.server_observations = {}
		self.server_groups = []
		self.threshold = 2 #at least 5 people in the same server to be considered a server group/cluster
	
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
		pairings = []
		for k1, v1 in self.server_observations.items():
			for k2, v2 in v1.items():
				if v2 >= self.threshold:
					pairings.append([k1, k2])
		
		#sort out the pairings and remove duplicates
		pairings = remove_duplicate_lists(pairings)
		

		for x in pairings:
			for y in x: print(self.data.servers[str(y)].server_name)
	
	def part_of_cluster(self, server_list): #given a list of server IDs, determine if these are part of a cluster or not
		#actually, this should just give an int, representing the number of mutual servers. clusters will be combined to represent a single server, thus bringing down the mutual server count.
		pass


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

basically, we don't want to get yelled at 10 times because person A, B, C, D, E, F, G (etc)
 are all in servers A and B, and maybe some are in A, B, and C
P_A: [A, B]
P_B: [A, B]
P_C: [B]
P_D: [A, B, C]
P_E: [A, B]
P_F: [B, F]
P_G: [B, C]

firstly, get rid of P_C because they're only in one mutual server.
then we go through each user, and take note of the servers they're in



"""
