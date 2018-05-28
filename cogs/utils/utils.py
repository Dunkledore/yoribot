import traceback
import discord


def traceback_from_exc(e, stack=4):
	return "\n".join(traceback.format_exception(type(e), e, e.__traceback__, stack))


def get_webhook(details, session):
	wh_id = details["wh_id"]
	wh_token = details["wh_token"]
	hook = discord.Webhook.partial(id=int(wh_id), token=wh_token,
	                               adapter=discord.AsyncWebhookAdapter(session))
	return hook
