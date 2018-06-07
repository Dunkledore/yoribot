from quart import Quart, session, flash, redirect
from functools import wraps


def require_login(function_):
	@wraps(function_)
	async def wrapper(*args, **kwargs):
		if "user" not in session or not session["user"]:
			await flash("Login Required", "error")
			return redirect('/index')
		return await function_(*args, **kwargs)
	return wrapper

def add_views(website : Quart, bot):
	@website.route("/")
	async def index():
		return "Index"

	@website.route('/logs/<int:guild_id>/<int:user_id>', methods=['GET'])
	async def logs_for_user(guild_id, user_id):
		query = "SELECT * FROM event_logs WHERE (guild_id = $1) and (target_id = $2)"
		logs = await bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])

	@website.route('/messages/<int:guild_id>/<int:user_id>', methods=['GET'])
	async def messages_for_user(guild_id, user_id):
		query = "SELECT * FROM message_logs WHERE (guild_id = $1) and (author_id = $2)"
		logs = await bot.pool.fetch(query, guild_id, user_id)
		if not logs:
			return f"No logs for user {user_id}"
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record.items()]) for record in logs])





