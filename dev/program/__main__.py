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
from . import smartstuff

#s = smartstuff.RelatedServerFinder(me)

#s.find_patterns()


loop.create_task(me.begin())
loop.create_task(me.main_loop())
loop.run_forever()