
# Anti-Stalker System (for Discord)
*(originally called nomorediscordcreeps)*
Say ~~goodbye~~ hello to the stalkers you didn't know about! 

This program will regularly check users for mutual servers, and report any odd behavior back to you. It's ideal for finding people that are stalking you on Discord. Also, in a way, while helping find the creeps, it also turns you into a creep, because it collects data on anyone that sends messages, gets mentioned, or joins a server. 

It even includes a web interface *(some information is pixelated for the sake of my own and others privacy)*

![screenshot](https://github.com/TrevorBagels/TrevorBagels.github.io/blob/master/assets/images/blog/ass1.png?raw=true)
![screenshot (continued)](https://github.com/TrevorBagels/TrevorBagels.github.io/blob/master/assets/images/blog/ass2.png?raw=true)







Disclaimer: This turns your account into a passive selfbot. It won't send any messages, however it does listen to all messages that are sent, and it scans every single user that sends them. Selfbots are against TOS, and I take no responsibility for what may happen to your Discord account if you use this. 






## Setup and installation

This program uses [pushover](https://pushover.net/). You can edit `/dev/notify.py` to easily implement a different method of notifying yourself.

First, do some configuration. You'll need your discord token (`token`), Pushover application key (`pushover_token`), and Pushover user key (`pushover_user`). Set this all up in `/dev/config.json`. `config.json` probably doesn't exist, so just rename `config_example.json` to `config.json` and use that. 

Next, install the requirements.
`pip3 install -r requirements.txt`

Now, you're ready to run the program.
```
cd dev
python3 -m program
```



Todo:
* ~~implement ignoring friends~~
* ~~pattern recognition; if a few servers are somehow connected, and lots of people have those few servers as mutual servers for you, the program should automatically ignore those combos of mutual servers.~~
* detect when people are talking about specific topics using NLP



Known issues:
Only works on python 3.9

If there is an issue involving `json_util` and `bson`, try this:

```
pip3 uninstall bson
pip3 uninstall pymongo
pip3 install pymongo
```

That tends to fix it for some reason.