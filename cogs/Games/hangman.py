from discord.ext import commands
import discord

import re
import random

phrases = ["Eat My Hat", "Par For the Course", "Raining Cats and Dogs", "Roll With the Punches",
           "Curiosity Killed The Cat", "Man of Few Words", "Cry Over Spilt Milk", "Scot-free", "Rain on Your Parade",
           "Go For Broke", "Shot In the Dark", "Mountain Out of a Molehill", "Jaws of Death", "A Dime a Dozen",
           "Jig Is Up", "Elvis Has Left The Building", "Wake Up Call", "Jumping the Gun", "Up In Arms",
           "Beating Around the Bush", "Flea Market", "Playing For Keeps", "Cut To The Chase", "Fight Fire With Fire",
           "Keep Your Shirt On", "Poke Fun At", "Everything But The Kitchen Sink", "Jaws of Life",
           "What Goes Up Must Come Down", "Give a Man a Fish", "Plot Thickens - The",
           "Not the Sharpest Tool in the Shed", "Needle In a Haystack", "Right Off the Bat", "Throw In the Towel",
           "Down To Earth", "Lickety Split", "I Smell a Rat", "Long In The Tooth",
           "You Can't Teach an Old Dog New Tricks", "Back To the Drawing Board", "Down For The Count",
           "On the Same Page", "Under Your Nose", "Cut The Mustard",
           "If You Can't Stand the Heat, Get Out of the Kitchen", "Knock Your Socks Off", "Playing Possum",
           "No-Brainer", "Money Doesn't Grow On Trees", "In a Pickle", "In the Red", "Fit as a Fiddle", "Hear, Hear",
           "Hands Down", "Off One's Base", "Wild Goose Chase", "Keep Your Eyes Peeled", "A Piece of Cake",
           "Foaming At The Mouth", "Go Out On a Limb", "Quick and Dirty", "Hit Below The Belt",
           "Birds of a Feather Flock Together", "Wouldn't Harm a Fly", "Son of a Gun",
           "Between a Rock and a Hard Place", "Down And Out", "Cup Of Joe", "Down To The Wire",
           "Don't Look a Gift Horse In The Mouth", "Talk the Talk", "Close But No Cigar",
           "Jack of All Trades Master of None", "High And Dry", "A Fool and His Money are Soon Parted",
           "Every Cloud Has a Silver Lining", "Tough It Out", "Under the Weather", "Happy as a Clam",
           "An Arm and a Leg", "Read 'Em and Weep", "Right Out of the Gate", "Know the Ropes",
           "It's Not All It's Cracked Up To Be", "On the Ropes", "Burst Your Bubble", "Mouth-watering",
           "Swinging For the Fences", "Fool's Gold", "On Cloud Nine", "Fish Out Of Water", "Ring Any Bells?",
           "There's No I in Team", "Ride Him, Cowboy!", "Top Drawer", "No Ifs, Ands, or Buts",
           "You Can't Judge a Book By Its Cover", "Don't Count Your Chickens Before They Hatch", "Cry Wolf",
           "Beating a Dead Horse", "Goody Two-Shoes", "Heads Up", "Drawing a Blank", "Keep On Truckin'", "Tug of War",
           "Short End of the Stick", "Hard Pill to Swallow", "Back to Square One", "Love Birds", "Dropping Like Flies",
           "Break The Ice", "Knuckle Down", "Lovey Dovey", "Greased Lightning", "Let Her Rip", "All Greek To Me",
           "Two Down, One to Go", "What Am I, Chopped Liver?", "It's Not Brain Surgery", "Like Father Like Son",
           "Easy As Pie", "Elephant in the Room", "Quick On the Draw", "Barking Up The Wrong Tree",
           "A Chip on Your Shoulder", "Put a Sock In It", "Quality Time", "Yada Yada", "Head Over Heels",
           "My Cup of Tea", "Ugly Duckling", "Drive Me Nuts", "When the Rubber Hits the Road", "Sexiest Man Alive"]


class Game:

	def __init__(self, word):
		self.word = word
		# This converts everything but spaces to a blank
		self.blanks = "".join(letter if not re.search("[a-zA-Z0-9]", letter) else "_" for letter in word)
		self.failed_letters = []
		self.guessed_letters = []
		self.fails = 0
		self.catagory = "Games"

	def guess_letter(self, letter):
		# No matter what, add this to guessed letters so we only have to do one check if a letter was already guessed
		self.guessed_letters.append(letter)
		if letter.lower() in self.word.lower():
			# Replace every occurence of the guessed letter, with the correct letter
			# Use the one in the word instead of letter, due to capitalization
			self.blanks = "".join(
				word_letter if letter.lower() == word_letter.lower() else self.blanks[i] for i, word_letter in
				enumerate(self.word))
			return True
		else:
			self.fails += 1
			self.failed_letters.append(letter)
			return False

	def guess_word(self, word):
		if word.lower() == self.word.lower():
			self.blanks = self.word
			return True
		else:
			self.fails += 1
			return False

	def win(self):
		return self.word == self.blanks

	def failed(self):
		return self.fails == 7

	def __str__(self):
		# Here's our fancy formatting for the hangman picture
		# Each position in the hangman picture is either a space, or part of the man, based on how many fails there are
		man = "     ——\n"
		man += "    |  |\n"
		man += "    {}  |\n".format("o" if self.fails > 0 else " ")
		man += "   {}{}{} |\n".format("/" if self.fails > 1 else " ", "|" if self.fails > 2 else " ",
		                              "\\" if self.fails > 3 else " ")
		man += "    {}  |\n".format("|" if self.fails > 4 else " ")
		man += "   {} {} |\n".format("/" if self.fails > 5 else " ", "\\" if self.fails > 6 else " ")
		man += "       |\n"
		man += "    ———————\n"
		fmt = "```\n{}```".format(man)
		# Then just add the guesses and the blanks to the string
		fmt += "```\nGuesses: {}\nWord: {}```".format(", ".join(self.failed_letters), " ".join(self.blanks))
		return fmt


class Hangman:
	"""
	Start a game of hangman where members can guess letters or even the phrase - be careful though - you don't want to guess wrong too many times!
	"""

	def __init__(self, bot):
		self.bot = bot
		self.games = {}

	def start(self, word, ctx):
		# Create a new game, then save it as the guild's game
		game = Game(word)
		self.games[ctx.message.guild.id] = game
		return game

	@commands.group(invoke_without_command=True)
	@commands.guild_only()
	async def guess(self, ctx, *, guess):
		"""Makes a guess towards the guild's currently running hangman game
		EXAMPLE: !hangman e (or) !hangman The Phrase!
		RESULT: Hopefully a win!"""
		game = self.games.get(ctx.message.guild.id)
		if not game:
			await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
			                                   title="⚠ Error",
			                                   description="There are currently no hangman games running!"))
			return

		# Check if we are guessing a letter or a phrase. Only one letter can be guessed at a time
		# So if anything more than one was provided, we're guessing at the phrase
		# We're creating a fmt variable, so that we can  add a message for if a guess was correct or not
		# And also add a message for a loss/win
		if len(guess) == 1:
			if guess in game.guessed_letters:
				await ctx.send("❕ That letter has already been guessed!")
				# Return here as we don't want to count this as a failure
				return
			if game.guess_letter(guess):
				fmt = "✅ That's correct!"
			else:
				fmt = "⚠ Sorry, that letter is not in the phrase..."
		else:
			if game.guess_word(guess):
				fmt = "✅ That's correct!"
			else:
				fmt = "⚠ Sorry that's not the correct phrase..."

		if game.win():
			fmt += "\n You guys got it! The word was `{}`".format(game.word)
			del self.games[ctx.message.guild.id]
		elif game.failed():
			fmt += "\n Sorry, you guys failed...the word was `{}`".format(game.word)
			del self.games[ctx.message.guild.id]

		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
		                                   title=fmt,
		                                   description=str(game)))

	@commands.command()
	@commands.guild_only()
	async def starthangman(self, ctx):
		"""This is used to create a new hangman game
		A predefined phrase will be randomly chosen as the phrase to use
		EXAMPLE: !hangman start
		RESULT: This is pretty obvious .-."""

		# Only have one hangman game per guild, since anyone
		# In a guild (except the creator) can guess towards the current game
		if self.games.get(ctx.message.guild.id) is not None:
			await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
			                                   title="⚠ Error",
			                                   description="Sorry but only one Hangman game can be running per guild!"))
			return

		game = self.start(random.SystemRandom().choice(phrases), ctx)
		# Let them know the game has started, then print the current game so that the blanks are shown
		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
		                                   title="✅ Success",
		                                   description=
		                                   "Alright, a hangman game has just started, you can start guessing now!\n{}".format(
			                                   str(game))))

	@commands.command()
	@commands.guild_only()
	async def stophangman(self, ctx):
		"""Force stops a game of hangman
		This should realistically only be used in a situation like one player leaves
		Hopefully a moderator will not abuse it, but there's not much we can do to avoid that
		EXAMPLE: !hangman stop
		RESULT: No more men being hung"""
		if self.games.get(ctx.message.guild.id) is None:
			await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
			                                   title="⚠ Error",
			                                   description="There are no Hangman games running on this guild!"))
			return

		del self.games[ctx.message.guild.id]
		await ctx.send(embed=discord.Embed(color=ctx.message.author.color,
		                                   title="⚠ Error",
		                                   description="I have just stopped the game of Hangman, a new should be able to be started now!"))


def setup(bot):
	bot.add_cog(Hangman(bot))