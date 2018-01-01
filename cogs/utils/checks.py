from discord.ext import commands


# The permission system of the bot is based on a "just works" basis
# You have permissions and the bot has permissions. If you meet the permissions
# required to execute the command (and the bot does as well) then it goes through
# and you can execute the command.
# Certain permissions signify if the person is a moderator (Manage Server) or an
# admin (Administrator). Having these signify certain bypasses.
# Of course, the owner will always be able to execute commands.

async def check_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True


async def check_guild_permissions(ctx, perms, *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.guild is None:
        return False

    resolved = ctx.author.guild_permissions
    return check(getattr(resolved, name, None) == value for name, value in perms.items())


def has_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)


def has_guild_permissions(*, check=all, **perms):
    async def pred(ctx):
        return await check_guild_permissions(ctx, perms, check=check)

    return commands.check(pred)


def is_nsfw():
    def pred(ctx):
        return ctx.message.channel.is_nsfw()

    return commands.check(pred)


async def has_level(level, ctx):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if ctx.author.id in [146893225850961920, 234353120455426048, 123900100081745922]:
        levels = ["developer", "admin", "mod"]
        return level in levels

    admin = await check_guild_permissions(ctx, {'administrator': True})
    if admin:
        levels = ["admin", "mod"]
        return level in levels

    query = "SELECT * FROM mod_config WHERE guild_id = $1"
    results = await ctx.db.fetch(query, ctx.guild.id)

    mod_role = None
    if results:
        mod_role = results[0]["mod_role"]
    else:
        mod_role = None

    for role in ctx.author.roles:
        if role.id == mod_role:
            levels = ["mod"]
            return level in levels

    return False


def is_mod():
    async def pred(ctx):
        return await has_level("mod", ctx)

    return commands.check(pred)


def is_admin():
    async def pred(ctx):
        return await has_level("admin", ctx)

    return commands.check(pred)


def is_developer():
    async def pred(ctx):
        return await has_level("developer", ctx)

    return commands.check(pred)


def is_owner():
    async def pred(ctx):
        return await has_level("owner", ctx)

    return commands.check(pred)


def is_guild_owner():
    async def pred(ctx):
        return ctx.author == ctx.guild.owner

    return commands.check(pred)


def is_tweeter():
    async def pref(ctx):
        if ctx.message.author == ctx.guild.owner:
            return True
        query = "SELECT * FROM social_config WHERE guild_id = $1"
        results = await ctx.db.fetch(query, ctx.guild.id)
        tweeter_role = results[0]["tweeter_role_id"]
        for role in ctx.author.roles:
            if role.id == tweeter_role:
                return True
        return False

    return commands.check(pref)


def is_greeter():
    async def pref(ctx):
        if ctx.message.author == ctx.guild.owner:
            return True
        query = "SELECT * FROM greet WHERE guild_id = $1"
        results = await ctx.db.fetch(query, ctx.guild.id)
        tweeter_role = results[0]["greeter_role_id"]
        for role in ctx.author.roles:
            if role.id == tweeter_role:
                return True
        return False

    return commands.check(pref)


def is_in_guilds(*guild_ids):
    def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        return guild.id in guild_ids

    return commands.check(predicate)
