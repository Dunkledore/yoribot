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

    resolved = ctx.channel.permissions_for(ctx.author)
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

async def has_level(level, author)
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is is_owner:
        return True

    query = "SELECT * FROM mod_config WHERE guild_id = $1"
    result = await ctx.db.fetch(query, ctx.guild.id)
    mod_role = results[0]["mod_role"]



    if (ctx.author.id in [146893225850961920,234353120455426048,123900100081745922]):
        levels = ["developers","admin","mod"]
        return (level in levels)
    if check_guild_permissions(ctx,{'administrator': True}):
        levels = ["admin","mod"]
        return (level in levels)
    for role in ctx.roles:
        if role.id = mod_role:
            levels = ["mod"]
            return (level in levels)
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

def is_in_guilds(*guild_ids):
    def predicate(ctx):
        guild = ctx.guild
        if guild is None:
            return False
        return guild.id in guild_ids
    return commands.check(predicate)
