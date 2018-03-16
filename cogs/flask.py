import discord 
from discord.ext import commands
from flask import Flask, request, render_template
from .utils import checks

class Flask:
	"""The Welcome Related Commands"""

	def __init__(self, bot):
		self.bot = bot
		self.app = None

	@commands.command()
	@checks.is_developer()
	async def run_app(self, ctx):
		self.app.run()


	@commands.command()
	@checks.is_developer()
	async def build_app(self, ctx):
		

		self.app = Flask(__name__)

		self.app.add_url_rule('/', 'index', index)

		def index():
			return render_template('index.html')

def setup(bot):
    bot.add_cog(Flask(bot))




