
#nomorediscordcreeps
Say goodbye to stalkers you don't know about! 

This program will regularly check users for mutual servers, and report any odd behavior back to you. It's ideal for finding people that are stalking you on Discord. Also, in a way, while helping find the creeps, it also turns you into a creep, depending on how you use it.

Disclaimer: This turns your account into a passive selfbot. It won't send any messages, however it does listen to all messages that are sent, and it scans every single user that sends them. Selfbots are against TOS, and I take no responsibility for what may happen to your Discord account if you use this. 


## Setup and installation

First, do some configuration. You'll need your discord token (`token`), Pushover application key (`pushover_token`), and Pushover user key (`pushover_user`). Set this all up in `/dev/config.json`. `config.json` probably doesn't exist, so just rename `config_example.json` to `config.json` and use that. 

Next, install the requirements.
`pip3 install -r requirements.txt`

Now, you're ready to run the program.
```
cd dev
python3 -m program
```



Todo:
* implement ignoring friends
* pattern recognition; if a few servers are somehow connected, and lots of people have those few servers as mutual servers for you, the program should automatically ignore those combos of mutual servers.\
* detect when people are talking about specific topics using NLP
