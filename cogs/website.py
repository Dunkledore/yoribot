import os
from functools import wraps

from discord import Object
from quart import Quart, session, redirect, request
from requests_oauthlib import OAuth2Session
from .utils import checks

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
			return
		proxy_ctx.bot = self.bot
		if await checks.has_level(proxy_ctx, "mod"):
			return



	async def index(self):
		return "Index"

	async def profile(self):
		return "profile"

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
		return "done"

	@require_login
	async def logs_for_user(self, guild_id, user_id):
		guild = self.bot.get_guild(guild_id)
		if not guild:
			return "Guild not found"
		if not self.is_mod_in_guild(guild):
			return "Not authorized"

		query = "SELECT * FROM event_logs WHERE (guild_id = $1) and (target_id = $2)"
		logs = await self.bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])

	@require_login
	async def messages_for_user(self, guild_id, user_id):
		query = "SELECT * FROM message_logs WHERE (guild_id = $1) and (author_id = $2)"
		logs = await self.bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])

	def run(self):
		super().run(host='0.0.0.0', port=self.port)
