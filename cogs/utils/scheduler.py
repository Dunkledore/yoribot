import functools
import asyncio
import datetime
import inspect

class Event:

		def __init__(self, **kwargs):
			self.id = kwargs.pop("id")
			self.cog = kwargs.pop("cog")
			self.args = kwargs.pop("params")
			self.kwargs = kwargs.pop("kwargs")
			self.time_of_execution = kwargs.pop("time_of_execution")
			self.method_name = kwargs.pop("method_name")
			self.actual_method = None

		async def schedule(self):
			now = datetime.datetime.utcnow()
			asyncio.sleep((self.time_of_execution-now).total_seconds())
			if inspect.iscoroutinefunction(self.actual_method):
				await self.actual_method()
			else:
				self.actual_method()




class EventManager:

		def __init__(self, events_dict):
			self.events_dict = events_dict
			self.events = []

		async def create_events(self):
			for event in self.events_dict:
				self.events.append(Event(**dict(event)))

		async def schedule_events(self, bot):
			for event in self.events:
				event_cog = bot.get_cog(event.cog)
				method = getattr(event_cog, event.method_name)
				event.actual_method = functools.partial(method, *event.args, **event.kwargs)
				event.schedule()





