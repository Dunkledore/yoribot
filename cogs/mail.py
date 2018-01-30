import discord, asyncio, imaplib, json, os, colorama, threading, time
colorama.init()
from .utils import checks
from .utils.dataIO import dataIO
from discord.ext import commands



class Mail2Discord():

    def __init__(self, bot):
        self.bot = bot
        self.settings = dataIO.load_json("data/mail/settings.json")

    def save_settings(self):
        dataIO.save_json("data/rolemanager/settings.json", self.settings)

    @commands.command()
    #@checks.is_guild_owner()
    @checks.is_developer()
    async def imapcreds(self, ctx):
        author = ctx.author
        def check(m):
            return m.author == author

        await ctx.author.send("Please send your IMAP address. Usually something like imap.somehost.com")
        imapaddress = await self.bot.wait_for('message', check=check, timeout=30.0)
        imapaddress = imapaddress.content
        await asyncio.sleep(1)

        await ctx.author.send("Please email username. Usually your full email address.")
        username = await self.bot.wait_for('message', check=check, timeout=30.0)
        username = username.content
        await asyncio.sleep(1)

        await ctx.author.send("Please send your password")
        password = await self.bot.wait_for('message', check=check, timeout=30.0)
        password = password.content
        await asyncio.sleep(1)

        insertquery = "INSERT INTO mail_config (guild_id, imap) VALUES ($1, $2)"
        alterquery = "UPDATE mail_config SET imap = $2 WHERE guild_id = $1"

        imap_creds = [imapaddress,username,password]

        try:
            await ctx.db.execute(insertquery, ctx.guild.id, imap_creds)
        except asyncpg.UniqueViolationError:
            await ctx.db.execute(alterquery, ctx.guild.id, imap_creds)
        await ctx.author.send('Details Saved')

    @commands.command()
    @checks.is_admin()
    async def fetchmail(self, ctx):
        mails = await get_mails(ctx.guild.id)

        await ctx.send(_mails[1][:2000])



    def good_print( self, text, center=0, color=0 ):
        # Makes printing with colors / centering easier for me
        _c = color if color else ""
        print(_c+("{:!^50}" if center else "{}").format(text))

    async def get_mails(self, guild_id ):

        query = "SELECT guild_id, imap_creds FROM social_config WHERE guild_id = $1"
        results = await self.bot.pool.fetch(query, guild_id)

        if not results:
            return

        imap_address = results[0][0]
        username = results[0][1]
        password = results[0][2]

        _mail = imaplib.IMAP4_SSL(imapaddress)
        _mail.login(username, password)
        print("Getting mails from "+ username)
        _mail.list()
        _mail.select("inbox")
        result, data = _mail.search(None, "ALL")
        newest_mail = data[0].split()[-1]
        raw_nmail = _mail.fetch(newest_mail, "(RFC822)")[1][0][1]
        with open("lastmail.txt","rb") as _f:
            _response = 1 if not _f.read() == raw_nmail else 0
            print("New mail!" if _response else "No new mails")
            _f.close()
        with open("lastmail.txt","wb") as _f:
            _f.write(raw_nmail)
            _f.close()
        return _response, raw_nmail


    def get_config( self ):
        # Get Discord token, e-mail SMTP data and e-mail credentials.
        with open( "config.json" ) as _f:
            _conf = json.loads(_f.read())
            _f.close()
        return _conf

    async def on_ready(self):
        # Function run when successfully logged in to Discord
        self.good_print(" Connected to Discord ", 1, colorama.Back.GREEN)
        while( 1 ):
            _result = self.get_mails()
            if( _result[0] ):
                _owner = await self.get_user_info(self.get_config()["discord"]["ownerid"])
                _pmowner = await self.start_private_message(_owner)
                await self.send_message(_pmowner, _result[1][:2000])
            asyncio.sleep(120)



def check_folders():
    if not os.path.exists("data/mail"):
        print("Creating data/mail folder...")
        os.makedirs("data/mail")

def check_files():
    if not os.path.isfile("data/mail/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/mail/settings.json", {})

def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Mail2Discord(bot))

