from datetime import datetime, timedelta




class Cooldown:

    def __init__(self, amount, per_seconds):
    	self.amount = amount
    	self.per_seconds = per_seconds
    	self.current_amount = 0
    	self.last_check = datetime.utcnow()

    def is_allowed(self)
    	return self.current_amount < self.amount

    def reset_current_amount(self):
    	self.current_amount = 0

    def check_time(self):
    	if self.last_check + timedelta(seconds=per_seconds) < datetime.utcnow():
    		self.reset_current_amount()
    		self.last_check = datetime.utcnow()


