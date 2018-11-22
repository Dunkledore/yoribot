from datetime import datetime, timedelta


class Cooldown:
	"""A class to manage cooldowns. Construct with the max amount in a time.

	To use run the check_reset then increment then is_allowed"""

	def __init__(self, amount, per_seconds):
		self.amount = amount
		self.per_seconds = per_seconds
		self.current_amount = 0
		self.last_check = datetime.utcnow()

	def is_allowed(self):
		return self.current_amount <= self.amount

	def reset_current_amount(self):
		self.current_amount = 0

	def check_reset(self):
		if self.last_check+timedelta(seconds=self.per_seconds) < datetime.utcnow():
			self.reset_current_amount()
			self.last_check = datetime.utcnow()

	def increment(self):
		self.current_amount += 1