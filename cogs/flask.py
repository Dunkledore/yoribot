import discord 
from discord.ext import commands
from flask import Flask, request, render_template
from .utils import checks

class Website:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = Flask(__name__)

		
	@commands.command()
	@checks.is_developer()
	async def run_app(self, ctx):
		self.app.add_url_rule('/', 'index,', self.index)
		self.app.run()


	def index():
		return render_template('index.html')

def setup(bot):
    bot.add_cog(Website(bot))





