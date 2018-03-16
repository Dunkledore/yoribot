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
		

		app = Flask(__name__)

		app.route('/form')
		def my_form():
		    return render_template('my-form.html')

		app.route('/')
		def index():
			return render_template('index.html')

		app.route('/downloads')
		def downloads():
			return render_template('downloads.html')

		app.route('/', methods=['POST'])
		def my_form_post():
		    text = request.form['text']
		    processed_text = text.upper()
		    return processed_text

		self.app = app

def setup(bot):
    bot.add_cog(Flask(bot))




