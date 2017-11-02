import asyncio
from os.path import join

import discord
import youtube_dl
from discord.ext import commands

# Suppress noise about console usage from errors


class VoiceRift:
    def __init__(self, bot):
        self.bot = bot

    


def setup(bot):
    bot.add_cog(VoiceRift(bot))