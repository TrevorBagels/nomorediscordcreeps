import asyncio, os, sys
from .main import Me
from flask import Flask
import threading



if os.path.exists("config.json") == False:
	print("No config file found!")
	sys.exit()

if os.path.exists("data.json") == False:
	with open("data.json", "w+") as f:
		f.write("{}")

loop = asyncio.get_event_loop()
me = Me()
app = Flask(__name__, static_folder="./program/static")

from .flaskapp import appdisplay as appdisp
from flask import request
@app.route("/ignore_user", methods=["POST"])
def ignore_user():
	print("IGNORE USER REQUEST RECEIVED")
	user_id = request.form["user_id"]
	me.ignore_user(user_id)
	del me.data.stalkers[str(user_id)]
	return appdisplay()
@app.route("/", methods=['GET', 'POST'])
def appdisplay():
	return appdisp(me)
	

threading.Thread(target=app.run).start()

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