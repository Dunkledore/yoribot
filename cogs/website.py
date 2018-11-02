import os
from functools import wraps

from discord import Object
from quart import Quart, session, redirect, request, render_template
from requests_oauthlib import OAuth2Session
from .utils import checks, utils
from .utils import web_commands

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL+'/oauth2/authorize'
TOKEN_URL = API_BASE_URL+'/oauth2/token'



def require_login(function_):
	@wraps(function_)
	async def wrapper(*args, **kwargs):
		if "user" not in session or not session["user"]:
			session["path"] = request.path
			return redirect('/login')
		return await function_(*args, **kwargs)
	return wrapper

def get_command_signature(cmd):  #taken from rdanny
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


class Website(Quart):

	def __init__(self, client_secret, client_id, redirect_uri, port, bot):
		super().__init__(__name__, static_folder="website/static", template_folder="website/templates")
		self.config['SERCRET_KEY'] = client_secret
		self.secret_key = client_secret
		self.client_secret = client_secret
		self.client_id = client_id
		self.redirect_uri = redirect_uri
		self.port = port
		self.bot = bot
		self.add_url_rule("/", "index", self.index)
		self.add_url_rule("/index", "index", self.index)
		self.add_url_rule("/me", "me", self.profile)
		self.add_url_rule("/callback", "callback", self.callback)
		self.add_url_rule("/login", "login", self.login)
		self.add_url_rule('/logs/<int:guild_id>/<int:user_id>', "user_logs", self.logs_for_user)
		self.add_url_rule('/messages/<int:guild_id>/<int:user_id>', "message_logs", self.messages_for_user)
		self.add_url_rule('/logout',"logout", self.logout)
		self.add_url_rule('/about', "about", self.about)
		self.add_url_rule("/commands", "commands", self.commands)
		self.add_url_rule("/commands_list", "commands_list", self.commands_list)
		self.add_url_rule("/servers", "servers", self.guilds)

	async def errorhandler(self, error):
		webhook = self.bot.error_hook
		await webhook.send(str(error))



	def make_session(self, token=None, state=None, scope=None):
		return OAuth2Session(
			client_id=self.client_id,
			token=token,
			state=state,
			scope=scope,
			redirect_uri=self.redirect_uri,
			auto_refresh_kwargs={
				'client_id': self.client_id,
				'client_secret': self.client_secret,
			},
			auto_refresh_url=TOKEN_URL,
			token_updater=self.token_updater)

	def token_updater(self, token):
		session['oauth2_token'] = token

	async def is_mod_in_guild(self, guild):
		proxy_ctx = Object(id=None)
		proxy_ctx.guild = guild
		proxy_ctx.author = guild.get_member(int(session["user"]["id"]))
		if not proxy_ctx.author:
			return False
		proxy_ctx.bot = self.bot
		if await checks.has_level(proxy_ctx, "mod"):
			return True


	async def index(self):
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
		channels = text+voice
		return await render_template('index.html', guilds=guilds, members=members, commands=commands, channels=channels)

	@require_login
	async def profile(self):
		return await render_template("profile.html")

	async def about(self):
		return await render_template("about.html")

	async def commands(self):
		categories = web_commands.get_categories(self.bot)
		return await render_template('commands.html', categories=categories)

	async def commands_list(self):
		commands = web_commands.get_commands(self.bot)
		return await render_template('commands_list.html', commands=commands)

	@require_login
	async def guilds(self):
		guilds = session['guilds']
		for counter, guild in enumerate(list(guilds)):
			actual_guild = self.bot.get_guild(int(guild["id"]))
			if actual_guild:
				guilds[counter]["has_bot"] = True
				guilds[counter]["member_count"] = len(actual_guild.members)
				guilds[counter]["text_channels"] = len(actual_guild.text_channels)
				guilds[counter]["voice_channels"] = len(actual_guild.voice_channels)
		return await render_template('guilds.html', guilds=guilds)

	async def callback(self):
		if request.args.get('error'):
			return request.args['error']
		discord = self.make_session(state=session.get('oauth2_state'))
		token = discord.fetch_token(
			TOKEN_URL,
			client_secret=self.client_secret,
			code=request.args.get('code'))
		session['oauth2_token'] = token
		session['guilds'] = discord.get(API_BASE_URL+'/users/@me/guilds').json()
		session['user'] = discord.get(API_BASE_URL+'/users/@me').json()
		session['user_connections'] = discord.get(API_BASE_URL+'/users/@me/connections').json()
		return redirect(session.get('path', '/me'))

	async def login(self):
		scope = request.args.get(
			'scope',
			'identify connections guilds')
		discord = self.make_session(scope=scope.split(' '))
		authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
		session['oauth2_state'] = state
		return redirect(authorization_url)

	async def logout(self):
		session.clear()
		return redirect("/")

	@require_login
	async def logs_for_user(self, guild_id, user_id):
		guild = self.bot.get_guild(guild_id)
		if not guild:
			return "Guild not found"
		if not (await self.is_mod_in_guild(guild)):
			return "Not authorized"

		query = "SELECT * FROM event_logs WHERE (guild_id = $1) and (target_id = $2)"
		logs = await self.bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])

	@require_login
	async def messages_for_user(self, guild_id, user_id):
		guild = self.bot.get_guild(guild_id)
		if not guild:
			return "Guild not found"
		if not (await self.is_mod_in_guild(guild)):
			return "Not authorized"
		requesting_member = guild.get_member(int(session["user"]["id"]))
		if not requesting_member:
			return "You are not in this guild"
		target_member = guild.get_member(user_id)
		if target_member:
			if not utils.check_hierarchy(target_member, requesting_member):
				return "This person is higher than you in the hierarchy"



		query = "SELECT * FROM message_logs WHERE (guild_id = $1) and (author_id = $2)"
		logs = await self.bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])

	def run(self):
		super().run(host='0.0.0.0', port=self.port)
