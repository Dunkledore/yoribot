from quart import Quart

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
		return "<br><br>".join(["<br>".join([f'{key} : {value}' for key, value in record]) for record in logs])





