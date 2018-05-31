from discord import Game
import asyncio


class Cron:

    def __init(self, bot):
        self.bot = bot
        self.unloaded = False

    async def statuses(self):
        count = 0
        while not self.unloaded:
            asyncio.sleep(60)
            guilds = await self.bot.guilds()
            try:
                presenceText = ""
                if count == 0:
                    presenceText = "yoribot.com"
                elif count == 1:
                    presenceText = "{}help"
                elif count == 2:
                    presenceText = f"{str(len(guilds))} Servers"
                elif count == 3:
                    sum = 0
                    for g in guilds:
                        sum += g.member_count()
                    presenceText = f"{str(sum)} Users"

                await self.bot.change_presence(activity=Game(name=presenceText))
                count = count + 1
                if count > 3:
                    count = 0
                
            except asyncio.CancelledError:
                self.unloaded = True


def setup(bot):
    n = Cron(bot)
    bot.add_cog(n)
    global task
    task = bot.loop.create_task(n.statuses())

def teardown(bot):
    task.cancel()
