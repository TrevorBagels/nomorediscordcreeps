import asyncio, os, sys
from .main import Me

if os.path.exists("config.json") == False:
	print("No config file found!")
	sys.exit()

if os.path.exists("data.json") == False:
	with open("data.json", "w+") as f:
		f.write("{}")

loop = asyncio.get_event_loop()
me = Me()

loop.create_task(me.begin())
loop.create_task(me.main_loop())
loop.run_forever()


#from . import smartstuff
#s = smartstuff.RelatedServerFinder(me)
#thats four servers. but smartstuff should be able to condense it into 2, because 3 of them are all related and can be put into a cluster
#serverlist = [702300440334827601, 713982578692194389, 662319080182906940, 551013173990260766] 
#s.find_patterns()
#print(serverlist)
#print(s.filter_server_list(serverlist))
#me.save()