import html, time

from discord import channel
from discord.enums import ChannelType
from . import data as D
from .main import Me
from . import utils
import datetime
from flask import url_for
CSS = ""

def appdisplay(me:Me):
	with open("./program/static/styles/flaskapp.css", "r") as f: CSS = f.read()
	body = "<h1>Discord Anti-Stalker System (ASS)</h1>\n"
	style = f"<style>{CSS}</style>"
	#style = f"""<link rel="stylesheet" type="text/css" href="{url_for('static', filename='styles/flaskapp.css')}">"""
	main = "<div id='dashboard'>\n"
	main += f"Uptime: {utils.time_elapsed_1((D.now() - me.start_time).total_seconds())}<br>"
	main += f"Saved: {utc2local(me.last_save).strftime('%H:%M:%S')}<br>"
	main += f"Processing queue ({len(me.data.user_processing_queue)}): <span id='pq'>"
	pq = "  "
	for x in me.data.user_processing_queue:
		pq += str(x) + ", "
	main += pq[:-2]
	main += "</span>"
	main += f"""<br>Total servers: {len(me.data.servers)}
	<br>Total users: {len(me.data.users)}"""

	main += "<div><h3>Recently discovered</h3>" + recently_discovered(me) + "</div>"
	main += "\n</div>"
	
	body += "<div id='top'>"
	body += main
	body += f"<div id='stalkers'><h2>Stalkers (<span id='stalkercount'>{len(me.data.stalkers)}</span>)</h2><div class='scrollbox'>" + display_stalkers(me) + "</div></div>"
	body += "</div>"
	
	body += f"<div id='servers'><h2>Servers ({len(me.data.servers)})</h2><div>" + display_servers(me) + "</div></div>"
	jqueryscript = """<script src="https://code.jquery.com/jquery-3.6.0.min.js" integrity="sha256-/xUj+3OJU5yExlq6GSYGSHk7tPXikynS7ogEvDej/m4=" crossorigin="anonymous"></script>"""
	return jqueryscript + "<title>ass</title><script src='https://cdn.jsdelivr.net/npm/chart.js'></script><script>Chart.defaults.elements.point.radius = 1; Chart.defaults.elements.point.hitRadius = 3</script>" + style + "<body>" + body + "</body>"


def pt(txt): #process text, removing any < / >
	return html.escape(txt)

def getname(user):
	name = pt(user.username)
	if user.discriminator != None:
		name += f"<b>#{user.discriminator}</b>"
	return name

def get_created(user_id, me):
	d = me.get_account_creation_date(user_id)
	d = utc2local(d)
	return d.strftime("%m/%d, %Y | %H:%M")


def get_server_messages(me:Me, server:D.Server) -> str:
	channels_messages = {}
	for x in server.recent_messages:
		if x[2] not in channels_messages:
			channels_messages[x[2]] = []
		channels_messages[x[2]].append(D.Prodict.from_dict({
			"timestamp": utc2local(x[0].astimezone(datetime.timezone.utc)),
			"time": utc2local(x[0].astimezone(datetime.timezone.utc)).strftime("%H:%M"),
			"author": getname(me.data.users[str(x[1])]),
			"message": pt(x[3])
		}))
	top3 = [] #top 3 channels, these are the ones containing the most recent messages
	for x in channels_messages:
		top3.append(x)
	def sortthing(value):
		return channels_messages[value][len(channels_messages[value])-1].timestamp
	
	top3.sort(key=sortthing, reverse=True)
	top3 = top3[:3]
	txt = ""
	for c in top3:
		messages = channels_messages[c][-20:]
		channel_text = f"<div class='channel'><span class='channelname'><a target='_blank' href='https://discord.com/channels/{server.server_id}/{c}'>#{server.channels[str(c)].channel_name}</a></span>"
		prev_author = None
		for i, m in enumerate(messages):
			if prev_author != m.author:
				if prev_author != None:
					channel_text += "</table></div>" #end the previous author messages div, and the previous author div.
				#new author, start an author div
				channel_text += f"<div class='newauthor'>"
				channel_text += f"<span class='authorname'>{m.author}</span>"
				channel_text += "<table class='newauthormessages'>"
			
			channel_text += f"""<tr><td class='messagetime'>{m.time}</td><td class='messagecontent'>{m.message}</td></tr>"""
			
			#add <br> if there will be more messages after this
			if len(messages)-1 > i:
				channel_text += "<br>"
			
			prev_author = m.author
		
		channel_text += "</table></div></div>"		
		txt += channel_text + "\n"
	
	return txt
		
	


def display_servers(me:Me) -> str:
	servers = ""
	sorted_servers = []
	def sort_server(item):
		if len(item.rate_history.five_minute_cache) < 1:
			return 0
		return item.rate_history.five_minute_cache[len(item.rate_history.five_minute_cache) - 1][1]
	for _, server in me.data.servers.items(): sorted_servers.append(server)
	
	sorted_servers.sort(key=sort_server, reverse=True)

	for server in sorted_servers:
		s = "<div class='server'>"
		s += f"""
		<div class='serverinfo'><h3 style='float: left;'>{pt(str(server.server_name))}</h3>
		<p style='float: right;'>Members documented: {len(server.members)}<br>
		ID: <code>{server.server_id}</code><br>
		</p></div>
		<div class='servermessages'>{get_server_messages(me, server)}</div>
		{chart(server.rate_history.five_minute_cache[-70:], server.server_id, extra_data=server.member_history.five_minute_cache[-70:])}
		"""
		s += "</div>"
		servers += s
	return servers

def utc2local(utc) -> datetime.datetime:
	epoch = time.mktime(utc.timetuple())
	offset = datetime.datetime.fromtimestamp(epoch) - datetime.datetime.utcfromtimestamp(epoch)
	return utc + offset


def make_dataset(label, data, bg=(40, 40, 80), hidden=False):

	return f"""{{label: "{label}", backgroundColor: "rgb({bg[0]}, {bg[1]}, {bg[2]})", borderColor: "rgb({bg[0]*1.5}, {bg[1]*1.5}, {bg[2]*2.5})", data: {data}, hidden: {str(hidden).lower()} }}"""

def chart(data:list[tuple[datetime.datetime, int]], id, extra_data:list[tuple[datetime.datetime, int]]=[]) -> str:
	txt = f"<canvas id='{id}'></canvas>"
	labels = []
	data2 = []
	data3 = []
	for a in data:
		labels.append(utc2local(a[0]).strftime("%H:%M"))
		if type(a[1]) != int: print(a)
		data2.append(a[1])
		data3.append(0)
	
	for a in extra_data:
		datestring = utc2local(a[0]).strftime("%H:%M")
		if datestring in labels:
			index = labels.index(datestring)
			data3[index] = a[1]
	
	
	datastring = f"""{{labels: {labels}, datasets: [{make_dataset("Messages", data2)}, {make_dataset("Member Discovery", data3, bg=(80, 40, 40), hidden=True)} ]}}"""

	configstring = f"""
	{{
		type: 'line',
		data: {datastring},
		options:{{}} }}
	"""
	script = f"""
	new Chart(document.getElementById('{id}'), {configstring});
	"""
	txt += "<script>"+script+"</script>"
	return txt

def get_chart_labels(data):
	pass

def servers(me:Me, server_ids):
	serverslist = []
	for x in server_ids:
		serverslist.append(pt(str(me.data.servers[str(x)].server_name)))
	return serverslist

def recently_discovered(me:Me):
	txt = "<table>"
	userhistory = me.data.user_discovery[-25:].copy()
	userhistory.sort(reverse=True)
	for x in userhistory:
		user = me.data.users[str(x[1])]
		servs = ""
		for s in servers(me, user.servers):
			servs += f"<li>{s}</li>"
		txt += f"<tr><td>{utc2local(x[0]).strftime('%H:%M')}</td><td>{getname(user)}</td><td>{servs}</td></tr>"
	txt += "</table>"
	return txt

def display_stalkers(me) -> str:
	stalkers = ""
	for _, x in me.data.stalkers.items():
		u = me.data.users[str(x.user_id)]
		txt2 = f"<b>{getname(u)}</b><br><code>{u.user_id}</code><br><code>{get_created(u.user_id, me)}</code><br>"
		
		button = f"""<button onclick="$.post('/ignore_user', {{user_id: '{u.user_id}' }}); document.getElementById('stalker{u.user_id}').remove(); document.getElementById('stalkercount').innerHTML -= 1;">Ignore</button>"""
		txt2 += button
		servers = "<table><tr><th>Server</th><th>Server ID</th></tr>"
		for x in u.servers:
			s = me.data.servers[str(x)]
			servers += f"<tr><td>{pt(s.server_name)}</td><td>[{s.server_id}]</td></tr>"
		servers += "</table>"
		txt2 += "<h3>Servers</h3>" + servers
		stalkers += "\n" + f"<div id='stalker{u.user_id}'class='stalker'>{txt2}</div>"
	stalkers += "<div style='min-height: 350px;'><br></div>"
	return stalkers




def olddisp(me):
	txt = "Processing queue: " + str(len(me.data.user_processing_queue))
	pq = "\n\n"
	for x in me.data.user_processing_queue:
		pq += str(x) + ", "
	txt += pq[:-2]
	txt += f"\nTotal servers: {len(me.data.servers)}\n"
	txt += f"Total users: {len(me.data.users)}\n\n\n"
	stalkers = "Stalkers: \n"
	for _, x in me.data.stalkers.items():
		u = me.data.users[str(x.user_id)]
		txt2 = f"<b>{u.username}</b>\n\t<code>{u.user_id}</code>\n"
		servers = ""
		for x in u.servers:
			s = me.data.servers[str(x)]
			servers += f"\t\t{s.server_name} [{s.server_id}]\n"
		txt2 += "\tServers: \n" + servers
		stalkers += "\n" + txt2
	txt += stalkers
	txt = txt.replace("\n", "<br>").replace("\t", "&nbsp;&nbsp;")