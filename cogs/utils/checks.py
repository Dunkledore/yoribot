from discord.ext import commands
import discord


def is_developer():
	"developer"
	def check(ctx):
		return has_level(ctx, "developer")
	return commands.check(check)


def is_guild_owner():
	"guild_owner"
	def check(ctx):
		return has_level(ctx, "guild_owner")
	return commands.check(check)


def is_admin():
	"""admin"""
	def check(ctx):
		return has_level(ctx, "admin")
	return commands.check(check)


def is_mod():
	"""mod"""
	def check(ctx):
		return has_level(ctx, "mod")
	return commands.check(check)


async def has_level(ctx, level):
	# OWNER #
	author = ctx.author
	if await ctx.bot.is_owner(author):
		return True

	# DEVELOPER #
	if author.id in [123900100081745922, 399407075785965578]:
		return level in ["developer",
						 "guild_owner",
						 "admin",
						 "mod",
						 "greeter", ]

	# GUILD OWNER #
	if author is ctx.guild.owner:
		return level in ["guild_owner",
						 "admin",
						 "mod",
						 "greeter", ]

	# ADMIN #
	if ctx.author.guild_permissions.administrator:
		return level in ["admin",
						 "mod",
						 "greeter", ]

	query = "SELECT admin_role_id FROM guild_config WHERE guild_id = $1"
	admin_role_id = await ctx.bot.pool.fetchval(query, ctx.guild.id)  # Admin is permission or role
	for role in ctx.author.roles:
		if role.id == admin_role_id:
			return level in ["admin",
			                 "mod",
			                 "greeter", ]

	# MOD #
	mod_roles = ["mod", "moderator"]
	member_mod_roles = [role for role in ctx.author.roles if role.name.lower() in mod_roles]
	if member_mod_roles:
		return level in ["mod",
		                 "greeter"]
	# GREETER #
	query = "SELECT greeter_role_id FROM guild_config WHERE guild_id = $1"
	greeter_role_id = await ctx.bot.pool.fetchval(query, ctx.guild.id)
	for role in ctx.author.roles:
		if role.id == greeter_role_id:
			return level in ["greeter", ]

	return False

















