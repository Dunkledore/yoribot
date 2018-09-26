import aiohttp
import asyncio

async def do():
	async with aiohttp.ClientSession() as cs:
		payload = {'q': "Basinfffgstoke", 'appid': "6962668e218f2fefbdf322b129d94dd9"}
		url = 'http://api.openweathermap.org/data/2.5/weather?'
		async with cs.get(url, params=payload) as r:
			res = await r.json()
			print(res)

loop = asyncio.get_event_loop()
loop.run_until_complete(do())
