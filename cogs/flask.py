import discord 
from discord.ext import commands
from quart import Quart, g, session, render_template, redirect, request, jsonify, abort, Response
from requests_oauthlib import OAuth2Session
import os
import asyncio
from multiprocessing.pool import ThreadPool
from .static import config
import functools
from .utils import checks
from threading import Thread
import itertools, inspect
from collections import Counter

OAUTH2_CLIENT_ID =  config.client_id
OAUTH2_CLIENT_SECRET = config.secret
OAUTH2_REDIRECT_URI = config.redirect

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

def token_updater(token):
	session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
	return OAuth2Session(
		client_id=OAUTH2_CLIENT_ID,
		token=token,
		state=state,
		scope=scope,
		redirect_uri=OAUTH2_REDIRECT_URI,
		auto_refresh_kwargs={
			'client_id': OAUTH2_CLIENT_ID,
			'client_secret': OAUTH2_CLIENT_SECRET,
		},
		auto_refresh_url=TOKEN_URL,
		token_updater=token_updater)

def _command_signature(cmd):
	# this is modified from discord.py source
	# which I wrote myself lmao

	result = [cmd.qualified_name]
	if cmd.usage:
		result.append(cmd.usage)
		return ' '.join(result)

	params = cmd.clean_params
	if not params:
		return ' '.join(result)

	for name, param in params.items():
		if param.default is not param.empty:
			# We don't want None or '' to trigger the [name=value] case and instead it should
			# do [name] since [name=None] or [name=] are not exactly useful for the user.
			should_print = param.default if isinstance(param.default, str) else param.default is not None
			if should_print:
				result.append(f'[{name}={param.default!r}]')
			else:
				result.append(f'[{name}]')
		elif param.kind == param.VAR_POSITIONAL:
			result.append(f'[{name}...]')
		else:
			result.append(f'<{name}>')

	return ' '.join(result)

#CREATE TABLE bans (user_id BIGINT, guild_id BIGINT, reason Text)

class Website:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = Quart(__name__)
		self.app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET
		self.bot.loop.run_until_complete(self.run_app(None))
		self.ip_list = []


		
	def start_app(self):
		asyncio.set_event_loop(self.bot.loop)
		print (config.port)
		self.app.run(host ='0.0.0.0', port=config.port)


	#@commands.command(hidden=True)
	#@checks.is_developer()
	async def run_app(self, ctx):
		@self.app.errorhandler(401)
		def custom_401(error):
			return Response("Please visit support server to authorize your ip", 401, {"code" : 0 , "message" : "Please visit support server to authorize your ip"})
		
		@self.app.errorhandler(404)
		def page_not_found(e):
			return render_template('404.html'), 404

		@self.app.errorhandler(500)
		def page_not_found(e):
			return render_template('404.html'), 500

		@self.app.route('/tutorials')
		def tutorials():
			return render_template('tutorials.html')

		@self.app.route("/guildstats/<guild_id>")
		async def guildstats(guild_id):

			guild = self.bot.get_guild(int(guild_id))
			member_by_status = Counter(str(m.status) for m in guild.members)
			online = member_by_status['online']
			idle = member_by_status["idle"]
			dnd = member_by_status["dnd"]
			offline = member_by_status["offline"]
			total = guild.member_count

			return await render_template('stats.html', name=guild.name, online=online, idle=idle, dnd=dnd, offline=offline, total=total)


		@self.app.route('/me')
		async def profile():
			if session.get('oauth2_token'):
				discord = make_session(token=session.get('oauth2_token'))
				session['guilds'] = discord.get(API_BASE_URL + '/users/@me/guilds').json()
				session['user'] = discord.get(API_BASE_URL + '/users/@me').json()
				session['user_connections'] = discord.get(API_BASE_URL + '/users/@me/connections').json()
				session['profile'] = await self.fetch_profile(session['user']['id'])
			return await render_template('profile.html')

		@self.app.route('/callback')
		async def callback():
			if request.args.get('error'):
				return request.args['error']
			discord = make_session(state=session.get('oauth2_state'))
			token = discord.fetch_token(
				TOKEN_URL,
				client_secret=OAUTH2_CLIENT_SECRET,
				code=request.args.get('code'))
			session['oauth2_token'] = token
			return redirect('/me')

		@self.app.route('/login')
		async def login():
			scope = request.args.get(
				'scope',
				'identify connections guilds')
			discord = make_session(scope=scope.split(' '))
			authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
			session['oauth2_state'] = state
			return redirect(authorization_url)

		@self.app.route('/about')
		async def about():
			return await render_template('about.html')

		@self.app.route('/bans/<int:user_id>', methods=['GET'])
		async def is_banned(user_id):
			if request.remote_addr not in self.ip_list:
				abort(401)
			query = "SELECT * FROM bans WHERE user_id = $1"
			results = await self.bot.pool.fetchrow(query, user_id)
			return jsonify(dict(results))

		@self.app.route('/bans/<int:user_id>' methods=['POST'])
		async def add_ban():
			user_id = request.args.get('user_id')
			guild_id = request.args.get('guild_id')
			reason = request.args.get('reason')

			query = "INSERT INTO bans (user_id, guild_id, reason) VALUES ($1, $2, $3)"

			await self.bot.execute(query, user_id, guild_id, reason)
			return {}





		@self.app.route('/ip', methods=['GET'])
		async def ip():
			return request.remote_addr

			
		@self.app.route('/')
		async def index():

			guilds = len(self.bot.guilds)
			members = sum(1 for _ in self.bot.get_all_members())
			commands = len(self.bot.commands)

			voice_channels = []
			text_channels = []
			for guild in self.bot.guilds:
				voice_channels.extend(guild.voice_channels)
				text_channels.extend(guild.text_channels)

			text = len(text_channels)
			voice = len(voice_channels)
			channels = text + voice
			return await render_template('index.html', guilds=guilds, members=members, commands=commands, channels=channels)

		@self.app.route('/commands')
		async def commands():
			cogs = self.get_cogs()
			return await render_template('commands.html', cogs=cogs)

		@self.app.route('/commands_list')
		async def commands_list():
			commands = self.get_commands()
			return await render_template('commands_list.html', commands=commands)



		
		t = Thread(target=self.start_app)
		t.start()

		#await ctx.send("running")

	def get_commands(self):
		def key(c):
			return c.name

		entries = sorted(self.bot.commands, key=key)

		display_commands = []
		for command in entries:
			display_commands.append({"signature" : _command_signature(command), "description" : command.short_doc})

		return display_commands


	def get_cogs(self):
		
		def key(c):
			return c.cog_name or '\u200bMisc'

		entries = sorted(self.bot.commands, key=key)
		display_commands = []

		# 0: (cog, desc, commands) (max len == 9)
		# 1: (cog, desc, commands) (max len == 9)
		# ...

		for cog, commands in itertools.groupby(entries, key=key):
			non_hidden = [cmd for cmd in commands if not cmd.hidden]
			non_hidden = sorted(non_hidden, key=lambda x: x.name)
			if len(non_hidden) == 0:
				continue

			description = self.bot.get_cog(cog)
			if description is not None:
				description = inspect.getdoc(description) or None
			detailed_commands = []

			for command in non_hidden:
				sig = (_command_signature(command))
				desc = command.short_doc or "No help given"
				detailed_commands.append({"signature" : sig, "description" : desc})


			display_commands.append({"name" : cog, "description" : description, "commands" : detailed_commands})

		return display_commands

	async def fetch_profile(self, user_id):
		query = "SELECT * FROM profile WHERE user_id = $1"
		results = await self.bot.pool.fetchrow(query, int(user_id))
		return dict(results)


	@commands.command(name="update_ip_cache")
	async def _update_ip_cache(self, ctx):
		await self.update_ip_cache()
		await ctx.send(embed=self.bot.success("Updated"))



	async def update_ip_cache(self):
		query = "SELECT ip FROM auth_ips"
		self.ip_list = await self.bot.pool.fetch(query)





def setup(bot):
	bot.add_cog(Website(bot))








