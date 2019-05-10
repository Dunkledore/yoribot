## Yori Bot

A discord bot with:  
Inter-Guild Moderation  
Inter_Guild Communication  
Role Management with or without Reactions  
Advanced logs with web downloads  
Detailed statistics of user data and commands  
A local website

## Instructions - Ubuntu



1- **Set up the virtual environment**

This isolates python so multiple bots can run at once

Do `python3.6 -m virtualenv env`  
Activate the venv with `source env/bin/activate`

If future packages are needed to be installed this should be activated and then installed with `pip install`

2 - **Install dependencies**

This bot requires a modified library to enable the website part to work. Feel free to install the requirements manually but ensure hypercorn is installed from the git repo found in requirements 
TLDR: `pip install -U -r requirements`

3 - **Create the database in PostgreSQL**

Install postgres `apt-get install postgresql postgresql-contrib`  
Start postgres on boot `update-rc.d postgresql enable`  
Start the postgres service `service postgresql start`  
Login to the postgres user `su - postgres`  
Open sql tool `psql`  
Create role and database
```sql
CREATE ROLE yori WITH LOGIN PASSWORD 'password';
CREATE DATABASE yori OWNER yori;
```

4 - **Bot configuration**
Create a directory in the root or the bot called `instance`
Inside this folder create a python file called `__init__.py` with the following template

```py
token = "Bot_Token_Here"
new_server_hook = {"wh_id" : "WEBHOOK_ID_HERE", "wh_token" : "WEBHOOK_TOKEN_HERE" }
error_hook = {"wh_id" : "WEBHOOK_ID_HERE", "wh_token" : "WEBHOOK_TOKEN_HERE"}
db_uri = "postgresql://yori:password@localhost/yori"
root_website = "http://www.yoribot.com:5000"
client_secret = "ENTER_SECRET_HERE"
port = 80
```

For more information on the webhooks see below

5 - **Configuration of database**

The bot will begin to throw errors until one of the developers has run the `updatetables` command

6 - **Running the bot as a service**
In order to have the bot run indefinitely you need run it in a service manager. There are many available but this tutorial will follow using systemd.

Create service file with the information to running the bot `nano /etc/systemd/system/yoribot.service`
Paste in the following information and save
```py
[Unit]
Description=My Miscellaneous Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=PATH_TO_BOT_HERE
ExecStart=PATH_TO_ENV_HERE PATH_TO_RUN_HERE
Restart=on-failure # or always, on-abort, etc

[Install]
WantedBy=multi-user.target
```
Enable the service which will allow it to run on boot. `systemctl enable yoribot`  
Start the service `systemctl start yoribot`


## Webhooks
Yori uses webhook to error reporting. These are useful as we can still get errors even when part of the bot is not working or the discord api is having issues.  
To set these up. Make 2 webhooks and get their id/token. In discord this can be retrieved by copying the url and pasting into a browser
