import traceback
from dateutil.relativedelta import relativedelta
import datetime


def traceback_from_exc(e, stack=4):
	return "\n".join(traceback.format_exception(type(e), e, e.__traceback__, stack))


def get_webhook(details, session):
	wh_id = details["wh_id"]
	wh_token = details["wh_token"]
	hook = discord.Webhook.partial(id=int(wh_id), token=wh_token,
	                               adapter=discord.AsyncWebhookAdapter(session))
	return hook


def human_timedelta(dt, *, source=None):
	now = source or datetime.datetime.utcnow()
	if dt > now:
		delta = relativedelta(dt, now)
		suffix = ''
	else:
		delta = relativedelta(now, dt)
		suffix = ' ago'

	if delta.microseconds and delta.seconds:
		delta = delta+relativedelta(seconds=+1)

	attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']

	output = []
	for attr in attrs:
		elem = getattr(delta, attr)
		if not elem:
			continue

		if elem > 1:
			output.append(f'{elem} {attr}')
		else:
			output.append(f'{elem} {attr[:-1]}')

	if len(output) == 0:
		return 'now'
	elif len(output) == 1:
		return output[0]+suffix
	elif len(output) == 2:
		return f'{output[0]} and {output[1]}{suffix}'
	else:
		return f'{output[0]}, {output[1]} and {output[2]}{suffix}'

def check_hierarchy(user, target):
	return target.top_role < user.top_role


