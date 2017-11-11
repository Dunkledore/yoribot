from discord.ext import commands
from random import choice
from .utils.dataIO import dataIO
from .utils import checks
from .utils.chat_formatting import box
from collections import Counter, defaultdict, namedtuple
import discord
import time
import os
import asyncio
import chardet
import re

DEFAULTS = {"MAX_SCORE"    : 10,
            "TIMEOUT"      : 120,
            "DELAY"        : 15,
            "BOT_PLAYS"    : False,
            "REVEAL_ANSWER": True}

TriviaLine = namedtuple("TriviaLine", "question answers")


class Trivia:
    def __init__(self, bot):
        self.bot = bot
        self.trivia_sessions = []
        self.file_path = "data/trivia/settings.json"
        settings = dataIO.load_json(self.file_path)
        self.settings = defaultdict(lambda: DEFAULTS.copy(), settings)

    @commands.group(pass_context=True, no_pm=True)
    @checks.mod_or_permissions(administrator=True)
    async def triviaset(self, ctx):
        guild = ctx.message.guild
        if ctx.invoked_subcommand is None:
            settings = self.settings[guild.id]
            msg = box("Red gains points: {BOT_PLAYS}\n"
            "Seconds to answer: {DELAY}\n"
            "Points to win: {MAX_SCORE}\n"
            "Reveal answer on timeout: {REVEAL_ANSWER}\n"
            "".format(**settings))
            msg += "\n {}triviaset maxscore <maxscore>".format(ctx.prefix)
            msg += "\n {}triviaset timelimit <timelimit>".format(ctx.prefix)
            msg += "\n {}triviaset botplays <true/false>".format(ctx.prefix)
            msg += "\n {}triviaset revealanswer <true/false>".format(ctx.prefix)
            em = discord.Embed(color=ctx.message.author.color, description=msg)
            em.set_author(name="Trivia Settings Help", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)

    @triviaset.command(pass_context=True)
    async def maxscore(self, ctx, score : int=-1):
        guild = ctx.message.guild
        if score < 0:
            settings = self.settings[guild.id]
            msg = box("Points to win: {MAX_SCORE}\n"
            "".format(**settings))
            msg += "\n {}triviaset maxscore <maxscore>".format(ctx.prefix)
            msg += "The max score must be higher than 0."
            em = discord.Embed(color=ctx.message.author.color, description=msg)
            em.set_author(name="Trivia Settings - Max Score", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        elif score > 0:
            self.settings[guild.id]["MAX_SCORE"] = score
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description=score)
            em.set_author(name="Points Required to Win Set To", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        else:
            em = discord.Embed(color=ctx.message.author.color, description="Score must be higher than 0")
            em.set_author(name="Uh-Oh!", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)

    @triviaset.command(pass_context=True)
    async def timelimit(self, ctx, seconds : int=-1):
        guild = ctx.message.guild
        if seconds < 0:
            settings = self.settings[guild.id]
            msg = box("Seconds to answer: {DELAY}\n"
            "".format(**settings))
            msg += "\n {}triviaset timelimit <timelimit>".format(ctx.prefix)
            msg += " The time limit must be more than 5 seconds."
            em = discord.Embed(color=ctx.message.author.color, description=msg)
            em.set_author(name="Trivia Settings - Time Limit", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        elif seconds > 4:
            self.settings[guild.id]["DELAY"] = seconds
            self.save_settings()
            em = discord.Embed(color=ctx.message.author.color, description=seconds)
            em.set_author(name="Maximum time to answer (in seconds):", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        else:
            em = discord.Embed(color=ctx.message.author.color, description="Must allow at least 5 seconds to answer.")
            em.set_author(name="Uh-Oh!", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)

    @triviaset.command(pass_context=True)
    async def botplays(self, ctx):
        guild = ctx.message.guild
        if self.settings[guild.id]["BOT_PLAYS"]:
            self.settings[guild.id]["BOT_PLAYS"] = False
            em = discord.Embed(color=ctx.message.author.color, description="Alright the bot will stop kicking your butt.")
            em.set_author(name="Trivia Settings - Bot Plays", icon_url="http://bit.ly/2qrhjLu")
            em.set_footer(text= "To re-enable use *triviaset botplays")
            await ctx.send(embed=em)
        else:
            self.settings[guild.id]["BOT_PLAYS"] = True
            em = discord.Embed(color=ctx.message.author.color, description="The bot will now gain a point for answering before you do.")
            em.set_author(name="Trivia Settings - Bot Plays", icon_url="http://bit.ly/2qrhjLu")
            em.set_footer(text= "To disable use *triviaset botplays")
            await ctx.send(embed=em)
        self.save_settings()

    @triviaset.command(pass_context=True)
    async def revealanswer(self, ctx):
        guild = ctx.message.guild
        if self.settings[guild.id]["REVEAL_ANSWER"]:
            self.settings[guild.id]["REVEAL_ANSWER"] = False
            em = discord.Embed(color=ctx.message.author.color, description="The bot won't show answers anymore.")
            em.set_author(name="Trivia Settings - Reveal Answer", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        else:
            self.settings[guild.id]["REVEAL_ANSWER"] = True
            em = discord.Embed(color=ctx.message.author.color, description="The bot will show answers if nobody knows it.")
            em.set_author(name="Trivia Settings - Reveal Answer", icon_url="http://bit.ly/2qrhjLu")
            await ctx.send(embed=em)
        self.save_settings()

    @commands.group(pass_context=True, invoke_without_command=True, no_pm=True)
    async def trivia(self, ctx, list_name: str):
        message = ctx.message
        guild = message.guild
        session = self.get_trivia_by_channel(message.channel)
        if not session:
            try:
                trivia_list = self.parse_trivia_list(list_name)
            except FileNotFoundError:
                em = discord.Embed(color=ctx.message.author.color, description="That trivia list doesn't exist.")
                em.set_author(name=list_name, icon_url="http://bit.ly/2qlsl5I")
                await ctx.send(embed=em)
            except Exception as e:
                print(e)
                em = discord.Embed(color=ctx.message.author.color, description="Error loading trivia list.")
                em.set_author(name=list_name, icon_url="http://bit.ly/2qlsl5I")
                await ctx.send(embed=em)
            else:
                settings = self.settings[guild.id]
                t = TriviaSession(self.bot, trivia_list, message, settings)
                self.trivia_sessions.append(t)
                await t.new_question(ctx)
        else:
            em = discord.Embed(color=ctx.message.author.color, description="Trivia has already started in this channel.")
            em.set_author(name="OOPS!", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)

    @commands.command(pass_context=True, no_pm=True)
    async def triviastop(self, ctx):
        author = ctx.message.author
        guild = author.guild
        admin_role = self.bot.settings.get_guild_admin(guild)
        mod_role = self.bot.settings.get_guild_mod(guild)
        is_admin = discord.utils.get(author.roles, name=admin_role)
        is_mod = discord.utils.get(author.roles, name=mod_role)
        is_owner = author.id == self.bot.settings.owner
        is_guild_owner = author == guild.owner
        is_authorized = is_admin or is_mod or is_owner or is_guild_owner

        session = self.get_trivia_by_channel(ctx.message.channel)
        if session:
            if author == session.starter or is_authorized:
                await session.end_game()
            else:
                em = discord.Embed(color=ctx.message.author.color, description="You are not allowed to do that.")
                em.set_author(name="Uh-oh!", icon_url="http://bit.ly/2qlsl5I")
                await ctx.send(embed=em)
        else:
            em = discord.Embed(color=ctx.message.author.color, description="There wasn't any trivia going in this channel.")
            em.set_author(name="Uh-oh!", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)

    @trivia.group(name="list", pass_context=True)
    async def trivia_list(self, ctx):
        message = ctx.message
        guild = message.guild
        lists = os.listdir("data/trivia/")
        lists = [l for l in lists if l.endswith(".txt") and " " not in l]
        lists = [l.replace(".txt", "") for l in lists]

        if lists:
            msg = "\n ".join(sorted(lists))
            msg = box(msg, lang="diff")
            if len(lists) < 100:
                em = discord.Embed(color=ctx.message.author.color, description=msg)
                em.set_author(name="Available trivia lists:", icon_url="http://bit.ly/2rnwE4T")
                em.set_footer(text= "To start a round of trivia type *trivia <listname>")
                await ctx.send(embed=em)
            else:
                await self.bot.whisper(msg)
        else:
            em = discord.Embed(color=ctx.message.author.color, description="There are no trivia lists available.")
            em.set_author(name="Uh-oh!", icon_url="http://bit.ly/2qlsl5I")
            await ctx.send(embed=em)


    def parse_trivia_list(self, filename):
        path = "data/trivia/{}.txt".format(filename)
        parsed_list = []

        with open(path, "rb") as f:
            try:
                encoding = chardet.detect(f.read())["encoding"]
            except:
                encoding = "ISO-8859-1"

        with open(path, "r", encoding=encoding) as f:
            trivia_list = f.readlines()

        for line in trivia_list:
            if "`" not in line:
                continue
            line = line.replace("\n", "")
            line = line.split("`")
            question = line[0]
            answers = []
            for l in line[1:]:
                answers.append(l.strip())
            if len(line) >= 2 and question and answers:
                line = TriviaLine(question=question, answers=answers)
                parsed_list.append(line)

        if not parsed_list:
            raise ValueError("Empty trivia list")

        return parsed_list

    def get_trivia_by_channel(self, channel):
        for t in self.trivia_sessions:
            if t.channel == channel:
                return t
        return None

    async def on_message(self, message):
        if message.author != self.bot.user:
            session = self.get_trivia_by_channel(message.channel)
            if session:
                await session.check_answer(message)

    async def on_trivia_end(self, instance):
        if instance in self.trivia_sessions:
            self.trivia_sessions.remove(instance)

    def save_settings(self):
        dataIO.save_json(self.file_path, self.settings)


class TriviaSession():
    def __init__(self, bot, trivia_list, message, settings, pass_context=True):
        self.bot = bot
        self.reveal_messages = ("I know this one! {}!",
                                "Easy: {}.",
                                "Oh really? It's {} of course.")
        self.fail_messages = ("To the next one I guess...",
                              "Moving on...",
                              "I'm sure you'll know the answer of the next one.",
                              "\N{PENSIVE FACE} Next one.")
        self.current_line = None # {"QUESTION" : "String", "ANSWERS" : []}
        self.question_list = trivia_list
        self.channel = message.channel
        self.starter = message.author
        self.scores = Counter()
        self.status = "new question"
        self.timer = None
        self.timeout = time.perf_counter()
        self.count = 0
        self.settings = settings

    async def stop_trivia(self):
        self.status = "stop"
        self.bot.dispatch("trivia_end", self)

    async def end_game(self):
        self.status = "stop"
        if self.scores:
            await self.send_table()
        self.bot.dispatch("trivia_end", self)


    async def new_question(self, ctx):
        message = ctx.message
        guild = message.guild
        for score in self.scores.values():
            if score == self.settings["MAX_SCORE"]:
                await self.end_game()
                return True
        if self.question_list == []:
            await self.end_game()
            return True
        self.current_line = choice(self.question_list)
        self.question_list.remove(self.current_line)
        self.status = "waiting for answer"
        self.count += 1
        self.timer = int(time.perf_counter())

        msg = "Question number {}!".format(self.count)
        current_question = self.current_line.question

        # Check if line contains an url
        imgurl = re.compile("https?://.*?/.*?.(jpg|png|gif)")
        match = imgurl.search(current_question)
        if match:
            msg2 = "{}".format(current_question[:match.start()]+current_question[match.end():])
        else:
            msg2 = "{}".format(current_question)
        em = discord.Embed(color=ctx.message.author.color, description=msg2)
        if match:
            em.set_image(url=match.group(0))
        em.set_author(name=msg, icon_url="http://bit.ly/2qogYtY")
        await ctx.send(embed=em)

        while self.status != "correct answer" and abs(self.timer - int(time.perf_counter())) <= self.settings["DELAY"]:
            if abs(self.timeout - int(time.perf_counter())) >= self.settings["TIMEOUT"]:
                await ctx.send("Guys...? Well, I guess I'll stop then.")
                await self.stop_trivia()
                return True
            await asyncio.sleep(1) #Waiting for an answer or for the time limit
        if self.status == "correct answer":
            self.status = "new question"
            await asyncio.sleep(3)
            if not self.status == "stop":
                await self.new_question(ctx)
        elif self.status == "stop":
            return True
        else:
            if self.settings["REVEAL_ANSWER"]:
                msg = choice(self.reveal_messages).format(self.current_line.answers[0])
            else:
                msg = choice(self.fail_messages)
            if self.settings["BOT_PLAYS"]:
                msg += " **+1** for me!"
                self.scores[self.bot.user] += 1
            self.current_line = None
            await ctx.send(msg)
            await ctx.message.channel.trigger_typing()
            await asyncio.sleep(3)
            if not self.status == "stop":
                await self.new_question(ctx)

    async def send_table(self, ctx):
        t = "+ Results: \n\n"
        for user, score in self.scores.most_common():
            t += "+ {}\t{}\n".format(user, score)
        await ctx.send(box(t, lang="diff"))

    async def check_answer(self, message):
        if message.author == self.bot.user:
            return
        elif self.current_line is None:
            return

        self.timeout = time.perf_counter()
        has_guessed = False

        for answer in self.current_line.answers:
            answer = answer.lower()
            guess = message.content.lower()
            if " " not in answer:  # Exact matching, issue #331
                guess = guess.split(" ")
                for word in guess:
                    if word == answer:
                        has_guessed = True
            else:  # The answer has spaces, we can't be as strict
                if answer in guess:
                    has_guessed = True

        if has_guessed:
            self.current_line = None
            self.status = "correct answer"
            self.scores[message.author] += 1
            msg = "You got it {}! **+1** to you!".format(message.author.name)
            await message.channel.send(msg)


def check_folders():
    folders = ("data", "data/trivia/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)


def check_files():
    if not os.path.isfile("data/trivia/settings.json"):
        print("Creating empty settings.json...")
        dataIO.save_json("data/trivia/settings.json", {})


def setup(bot):
    check_folders()
    check_files()
    bot.add_cog(Trivia(bot))
