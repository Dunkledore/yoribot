import os
from functools import wraps

from discord import Object
from quart import Quart, session, redirect, request, render_template, flask_patch, flash
from requests_oauthlib import OAuth2Session
from .utils import checks, utils
from .utils import web_commands
from .utils import forms
import copy
import asyncpg
import htmlmin

#TODO Minfiy web returns

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
		self.add_url_rule("/servers", "servers", self.guilds, methods=["GET", "POST"])

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

	async def is_admin_in_guild(self, guild):
		proxy_ctx = Object(id=None)
		proxy_ctx.guild = guild
		proxy_ctx.author = guild.get_member(int(session["user"]["id"]))
		if not proxy_ctx.author:
			return False
		proxy_ctx.bot = self.bot
		if await checks.has_level(proxy_ctx, "admin"):
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
		raw_guilds = copy.deepcopy(session['guilds'])
		guilds = {}
		for guild in raw_guilds:
			guilds[int(guild["id"])] = guild
			actual_guild = self.bot.get_guild(int(guild["id"]))
			if actual_guild:
				guild_id = actual_guild.id
				guilds[guild_id]["has_bot"] = True
				guilds[guild_id]["member_count"] = len(actual_guild.members)
				guilds[guild_id]["text_channels"] = len(actual_guild.text_channels)
				guilds[guild_id]["voice_channels"] = len(actual_guild.voice_channels)
				guilds[guild_id]["channels"] = actual_guild.text_channels
				try:
					guilds[guild_id]["prefixes"] = self.bot.prefixes[str(actual_guild.id)]
				except KeyError: # No prefix set
					guilds[guild_id]["prefixes"] = ["*"]
				admins = [member for member in actual_guild.members if (member.guild_permissions.administrator and not member.bot)]
				if not admins:
					admins = None
				mod_roles = [role for role in actual_guild.roles if role.name.lower() in ["mod", "moderator"]]
				if mod_roles:
					mods = [member for member in actual_guild.members if ((any(role in member.roles for role in mod_roles)) and (member not in admins))]
					if not mods:
						mods = None
				else:
					mods = None
				guilds[guild_id]["admins"] = admins
				guilds[guild_id]["mods"] = mods
				guilds[guild_id]["is_admin"] = await self.is_admin_in_guild(actual_guild)
				most_messages_member_query = "SELECT author_id " \
				                             "FROM message_logs " \
				                             "WHERE (guild_id = $1 and time > (CURRENT_DATE - INTERVAL '30 days')) " \
				                             "GROUP BY author_id " \
				                             "ORDER BY COUNT(*) DESC " \
				                             "LIMIT 1"
				most_messages_channel_query = "SELECT channel_id " \
				                             "FROM message_logs " \
				                             "WHERE (guild_id = $1 and time > (CURRENT_DATE - INTERVAL '30 days')) " \
				                             "GROUP BY channel_id " \
				                             "ORDER BY COUNT(*) DESC " \
				                             "LIMIT 1"
				#most_messages_member_id = await self.bot.pool.fetchval(most_messages_member_query, guild_id)
				#most_messages_channel_id = await self.bot.pool.fetchval(most_messages_channel_query, guild_id)
				#most_messages_member = self.bot.get_user(most_messages_member_id)
				#most_messages_channel = self.bot.get_channel(most_messages_channel_id)
				guilds[guild_id]["most_member"] = "Me" #most_messages_member.display_name if most_messages_member else "Left"
				guilds[guild_id]["most_channel"] = "Me" #most_messages_channel.name if most_messages_channel else "Deleted"

				query = "SELECT message_log_channel_id FROM log_config WHERE guild_id = $1"
				message_log_channel_id = await self.bot.pool.fetchval(query, actual_guild.id)
				guilds[guild_id]["message_log_channel"] = self.bot.get_channel(message_log_channel_id)

				query = "SELECT member_log_channel_id FROM log_config WHERE guild_id = $1"
				member_log_channel_id = await self.bot.pool.fetchval(query, actual_guild.id)
				guilds[guild_id]["member_log_channel"] = self.bot.get_channel(member_log_channel_id)

				query = "SELECT invite_log_channel_id FROM log_config WHERE guild_id = $1"
				invite_log_channel_id = await self.bot.pool.fetchval(query, actual_guild.id)
				guilds[guild_id]["invite_log_channel"] = self.bot.get_channel(invite_log_channel_id)

				query = "SELECT channel_id, whisper FROM welcome_config WHERE guild_id = $1"
				welcome_config = await self.bot.pool.fetchrow(query, actual_guild.id)
				if not welcome_config:
					guilds[guild_id]["welcome_channel"] = None
					guilds[guild_id]["welcome_whisper"] = False
				else:
					guilds[guild_id]["welcome_channel"] = self.bot.get_channel(welcome_config["channel_id"])
					guilds[guild_id]["welcome_whisper"] = welcome_config["whisper"]


				query = "SELECT text_message FROM welcome_config WHERE guild_id = $1"
				text_message = await self.bot.pool.fetchval(query, guild_id)
				guilds[guild_id]["welcome_text"] = text_message

				query = "SELECT name, value FROM welcome_fields WHERE guild_id = $1"
				fields = await self.bot.pool.fetch(query, guild_id)
				guilds[guild_id]["welcome_fields"] = fields


		if request.method == "POST":
			form = await request.form

			guild_id = form["guild_id"]
			if guilds[int(guild_id)]["is_admin"]:
				if form.getlist("prefix") != self.bot.prefixes[guild_id]:
					self.bot.prefixes[guild_id] = form.getlist("prefix")
					self.bot.save_prefixes()
					guilds[int(guild_id)]['prefixes'] = form.getlist("prefix")
					await flash("Prefixes Updated")

				log_cog = self.bot.get_cog("Logs")

				selected_message_log_channel_id = form.get("message-log-selector")
				selected_message_log_channel = self.bot.get_channel(int(selected_message_log_channel_id))
				original_message_log_channel = guilds[int(guild_id)]["message_log_channel"]
				if selected_message_log_channel:
					if selected_message_log_channel != original_message_log_channel:
						await log_cog.start_message_logs(int(guild_id), selected_message_log_channel.id)
						guilds[int(guild_id)]["message_log_channel"] = selected_message_log_channel
						await flash("Message Log Channel Updated")

				selected_member_log_channel_id = form.get("member-log-selector")
				selected_member_log_channel = self.bot.get_channel(int(selected_member_log_channel_id))
				original_member_log_channel = guilds[int(guild_id)]["member_log_channel"]
				if selected_member_log_channel:
					if selected_member_log_channel != original_member_log_channel:
						await log_cog.start_member_logs(int(guild_id), selected_member_log_channel.id)
						guilds[int(guild_id)]["member_log_channel"] = selected_member_log_channel
						await flash("Member Log Channel Updated")

				selected_invite_log_channel_id = form.get("invite-log-selector")
				selected_invite_log_channel = self.bot.get_channel(int(selected_invite_log_channel_id))
				original_invite_log_channel = guilds[int(guild_id)]["invite_log_channel"]
				if selected_invite_log_channel:
					if selected_invite_log_channel != original_invite_log_channel:
						await log_cog.start_invite_logs(int(guild_id), selected_invite_log_channel.id)
						guilds[int(guild_id)]["invite_log_channel"] = selected_invite_log_channel
						await flash("Invite Log Channel Updated")

				welcome_cog = self.bot.get_cog("Welcome")
				selected_welcome_channel_id = form.get("welcome-channel-selector")
				selected_welcome_channel = self.bot.get_channel(int(selected_welcome_channel_id))
				original_welcome_channel = guilds[int(guild_id)]["welcome_channel"]
				if selected_welcome_channel:
					if selected_welcome_channel != original_welcome_channel:
						await welcome_cog.do_setwelcomechannel(int(guild_id), selected_welcome_channel.id)
						guilds[int(guild_id)]["welcome_channel"] = selected_welcome_channel
						await flash("Welcome channel updated")



				field_names = form.getlist("field-name")
				field_values = form.getlist("field-value")

				original_fields = [(field['name'], field['value']) for field in guilds[int(guild_id)]["welcome_fields"]]
				new_fields = list(zip(field_names, field_values))

				if new_fields != original_fields:
					delete_query = "DELETE FROM welcome_fields WHERE guild_id = $1"
					await self.bot.pool.execute(delete_query, int(guild_id))
					insert_query = "INSERT INTO welcome_fields(guild_id, name, value) VALUES ($1, $2, $3)"
					for pair in new_fields:
						await self.bot.pool.execute(insert_query, int(guild_id), pair[0], pair[1])
					query = "SELECT name, value FROM welcome_fields WHERE guild_id = $1"
					fields = await self.bot.pool.fetch(query, int(guild_id))
					guilds[int(guild_id)]["welcome_fields"] = fields
					await flash("Welcome Message updated")

				welcome_whisper = form.get("whisper")
				welcome_whisper = True if welcome_whisper == "on" else False
				if welcome_whisper != guilds[int(guild_id)]["welcome_whisper"]:
					await welcome_cog.do_welcome_whisper(int(guild_id))
					await flash("Welcome whisper updated")
					guilds[int(guild_id)]["welcome_whisper"] = welcome_whisper

			else:
				await flash("You are not an admin on this server ")

		return await render_template('guilds.html', guilds=guilds)

	async def callback(self):
		if request.args.get('error'):
			print(request.args.get('error'))
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
		print(session)
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
