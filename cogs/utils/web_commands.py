import itertools
import inspect


def get_command_signature(cmd):
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


def get_categories(bot):
	def key(c):
		return c.cog_name or '\u200bMisc'

	entries = sorted(bot.commands, key=key)
	display_commands = []

	# 0: (cog, desc, commands) (max len == 9)
	# 1: (cog, desc, commands) (max len == 9)
	# ...

	for cog, commands in itertools.groupby(entries, key=key):
		non_hidden = [cmd for cmd in commands if not cmd.hidden]
		non_hidden = sorted(non_hidden, key=lambda x: x.name)
		if len(non_hidden) == 0:
			continue

		cog_obj = bot.get_cog(cog)
		description = inspect.getdoc(cog_obj) or None
		if hasattr(cog_obj, "category"):
			category = cog_obj.category
		else:
			category = None
		detailed_commands = []

		for command in non_hidden:
			sig = (get_command_signature(command))
			desc = command.short_doc or "No help given"
			try:
				perm = command.checks[0].__qualname__.split(".")[0]
				perm = perm.replace("guild_only", "")
			except IndexError:
				perm = None

			detailed_commands.append({"signature": sig, "description": desc, "permission": perm})

		display_commands.append(
			{"name": cog, "description": description, "commands": detailed_commands, "category": category})
	categories = {}
	for cog in display_commands:
		if cog["category"] in categories:
			categories[cog["category"]].append(cog)
		else:
			categories[cog["category"]] = [cog]

	to_return = [{"name": category, "cogs": cogs} for category, cogs in categories.items()]
	return to_return

def get_commands(bot):
	def key(c):
		return c.name

	entries = sorted(bot.commands, key=key)
	entries = [entry for entry in entries if not entry.hidden]

	display_commands = []
	for command in entries:
		display_commands.append({"signature" : get_command_signature(command), "description" : command.short_doc})

	return display_commands
