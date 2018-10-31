from discord import Role, Embed
from discord.ext import commands
import asyncio
from .utils.checks import is_admin
from prettytable import PrettyTable


class SpecialRoles:
	"""Allow anyone with a certain role to give a specific role"""

	def __init__(self, bot):
		self.bot = bot

	async def on_message(self, message):
		if not message.guild:
			return

		ctx = await self.bot.get_context(message)
		if not ctx.prefix:
			return

		name = message.context.replace(ctx.prefix, "").split()[0]

		query = "SELECT * FROM special_roles WHERE (guild_id = $1) and (name = $2)"
		roles = await self.bot.pool.fetch(query, message.guild.id, name)
		if not roles:
			return

		roles_to_add = []
		for role in roles:
			give_role_id = role["give_role_id"]
			give_role = message.guild.get_role(give_role_id)
			if not give_role:
				return
			if give_role not in message.author.roles:
				return

			applied_role_id = role["applied_role_id"]
			role = message.guild.get_role(applied_role_id)
			if not role:
				return
			roles_to_add.append(role)

		await message.author.add_roles(roles_to_add)

	@commands.command(aliases=["remove_special_role", "special_role_delete", "special_role_remove"])
	@is_admin()
	@commands.guild_only()
	async def delete_special_role(self, ctx, name):
		query = "DELETE FROM special_roles WHERE (guild_id = $1) and (name = $2)"
		deleted = await self.bot.pool.fetchval(query, ctx.guild.id, name)
		if deleted == 0:
			await ctx.send(embed=self.bot.error(f"Special Role {name} not found"))
		else:
			await ctx.send(embed=self.bot.success(f"Special Role {name} deleted"))


	@commands.command(aliases=["special_roles", "special_roles_view"])
	@is_admin()
	@commands.guild_only()
	async def view_special_roles(self, ctx):
		query = "SELECT * FROM special_roles WHERE guild_id = $1"
		roles = await self.bot.fetch(query, ctx.guild.id)
		if not roles:
			await ctx.send(embed=self.bot.error("No special roles for this guild"))

		table = PrettyTable(field_names=["Name", "Role To Be Applied", "Role Able To Give"])
		for role in roles:
			name = role["name"]

			applied_role = await ctx.guild.get_role(role["applied_role_id"])
			if not applied_role:
				applied_role = "Deleted Role"
			else:
				applied_role = applied_role.name

			give_role = await ctx.guild.get_role(role["give_role_id"])
			if not give_role:
				give_role = "Deleted Role"
			else:
				give_role = give_role.name

			table.add_row([name, applied_role, give_role])
		embed = Embed(title=f"Special Roles for {ctx.guild.name}", description=str(table))

		await ctx.send(embed=embed)

	@commands.command(aliases=["add_special_role", "special_role_add", "special_role_create"])
	@is_admin()
	@commands.guild_only()
	async def create_special_role(self, ctx, name=None, role_to_be_applied: Role = None,
	                              able_to_give_role: Role = None):
		def check(message):
			return (message.channel is ctx.channel) and (message.author is ctx.author)

		try:
			if not name:
				await ctx.send(
					embed=self.bot.notice("What would you like the name of the special role ot be?\n N.B. This "
					                      "name will be used to give the role. For example if the name is `under18` the"
					                      f"role will then be given with the command `{ctx.prefix}under18`"))
				name_message = await self.bot.wait_for("message", check=check, timeout=60.0)
				name = name_message.content
			while not role_to_be_applied:
				await ctx.send(embed=self.bot.notice(
					f"Mention the role you would like to be applied when the command {ctx.prefix}{name}"
					" is executed"))
				role_message = await self.bot.wait_for("message", check=check, timeout=60.0)
				if role_message.role_mentions:
					role_to_be_applied = role_message.role_mentions[0]
				else:
					await ctx.send(embed=self.bot.error("No roles were mentioned"))
			while not able_to_give_role:
				await ctx.send(embed=self.bot.notice(
					f"Mention the role you would like to able to give {role.mention} when {ctx.prefix}{name}"
					" is executed"))
				role_message = await self.bot.wait_for("message", check=check, timeout=60.0)
				if role_message.role_mentions:
					able_to_give_role = role_message.role_mentions[0]
				else:
					await ctx.send(embed=self.bot.error("No roles were mentioned"))
		except asyncio.TimeoutError:
			return

		query = "INSERT INTO special_roles (guild_id, name, applied_role_id, give_role_id) VALUES ($1, $2, $3, $4)"
		await self.bot.pool.execute(query, ctx.guild.id, name, role_to_be_applied.id, able_to_give_role.id)
		await ctx.send(embe=self.bot.success(f"Speical role made. Example usage `{ctx.prefix}{name} {ctx.me.mention}"))


def setup(bot):
	bot.add_cog(SpecialRoles(bot))
