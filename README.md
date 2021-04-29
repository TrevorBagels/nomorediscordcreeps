
# Anti-Stalker System (for Discord)
*(originally called nomorediscordcreeps)*
Say ~~goodbye~~ hello to the stalkers you didn't know about! 

This program will regularly check users for mutual servers, and report any odd behavior back to you. It's ideal for finding people that are stalking you on Discord. Also, in a way, while helping find the creeps, it also turns you into a creep, because it collects data on anyone that sends messages, gets mentioned, or joins a server. 

It even includes a web interface *(some information is pixelated for the sake of my own and others privacy)*

![screenshot](https://github.com/TrevorBagels/TrevorBagels.github.io/blob/master/assets/images/blog/ass1.png?raw=true)
![screenshot (continued)](https://github.com/TrevorBagels/TrevorBagels.github.io/blob/master/assets/images/blog/ass2.png?raw=true)







Disclaimer: This turns your account into a passive selfbot. It won't send any messages, however it does listen to all messages that are sent, and it scans every single user that sends them. Selfbots are against TOS, and I take no responsibility for what may happen to your Discord account if you use this. 






## Setup and installation

**Note: Requires python 3.9 and above. Versions below that will give you type errors.**

This program uses [pushover](https://pushover.net/). You can edit `/dev/notify.py` to easily implement a different method of notifying yourself.

First, do some configuration. You'll need your discord token (`token`), Pushover application key (`pushover_token`), and Pushover user key (`pushover_user`). Set this all up in `/dev/config.json`. `config.json` probably doesn't exist, so just rename `config_example.json` to `config.json` and use that. 

Next, install the requirements.
`pip3 install -r requirements.txt`

Now, you're ready to run the program.
```
cd dev
python3 -m program
```
## First run
Upon the first time you run the program, it'll try to scrape content from each server you're in. It goes to each server, going to each channel, and it scrapes the past 50 messages for every channel. The maximum number of servers to scrape can be set using the config option `max_servers_to_scrape`. The default is 100. The maximum number of channels (per server) to scrape can be set using the config option `max_channels_to_scrape`. The default is 20. The number of messages to scrape per channel can be set with `scrape_amount`. Whatever you set that to should be the number of messages you want to scrape divided by 50 (and it should be an integer.) The default is `1`, allowing it to scrape the past 50 messages. Setting it to `2` would scrape 100 messages, `3` would be 150, and so on.

I haven't tested the first run many times, so if there are any bugs, they'll likely be in the initial scrape.

Once the initial scrape is done, it will begin processing users. Depending on how many users it found doing the scrape, this could take an extensive amount of time. For me, when I ran this, I was in 75 servers, and I didn't have limits on how many channels to scrape. It scraped the last 50 messages from every channel I was in, and collected around 2500 unique users in total. This probably took somewhere around 3-5 hours to process, and I had to stop it several times to implement ratelimiting that would evade cloudflare bans. (I managed to get the ratelimiting working to evade the bans, and as a result the entire operation can be very slow at times.)

After the first wave of users is processed, the program should run smoothly from there.

You can access an overview/dashboard by going to http://0.0.0.0:81. The host (`0.0.0.0`) and port (`81`) can be modified in `dev/flask_config.json`


Todo:
* ~~implement ignoring friends~~
* ~~pattern recognition; if a few servers are somehow connected, and lots of people have those few servers as mutual servers for you, the program should automatically ignore those combos of mutual servers.~~
* add some good and interactive UI
* add support for mongoDB
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
