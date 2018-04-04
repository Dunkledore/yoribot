
import discord


class UI:
    def __init__(self, bot, channel, title, description,
                 modulename="Modis", creator="anonymous", colour=0xAAFF00, thumbnail=None, image=None, datapacks=()):
        """Initialises variables and builds GUI

        Args:
            channel (discord.Channel): Channel to lock UI to
            title (str): GUI title, in bold
            description (str): GUI description
            modulename (str): Name of your module, default "Modis"
            creator (str): Your name/screen name, default "anonymous"
            colour (int): Colour of line on left, default 0xAAFF00
            thumbnail (str): URL to picture shown in top right corner, default None
            datapacks (list): Contains tuples of (title str, data str, inline bool)
        """

        self.channel = channel
        self.title = title
        self.description = description
        self.modulename = modulename
        self.creator = creator
        self.colour = colour
        self.thumbnail = thumbnail
        self.image = image
        self.datapacks = datapacks

        self.built_embed = self.build()
        self.sent_embed = None
        self.bot = bot

    def build(self):
        """Builds Discord embed GUI

        Returns:
            discord.Embed: Built GUI
        """

        embed = discord.Embed(
            title=self.title,
            type='rich',
            description=self.description,
            colour=self.colour)

        if self.thumbnail:
            embed.set_thumbnail(url=self.thumbnail)

        if self.image:
            embed.set_image(url=self.image)

        embed.set_author(
            name="Yori",
            url="https://yoribot.com/",
            icon_url="http://img.lgbtdis.co/image/h0RD")

        for pack in self.datapacks:
            embed.add_field(
                name=pack[0],
                value=pack[1],
                inline=pack[2]
            )

        return embed

    async def send(self):
        """Send new GUI"""
        async with self.channel.typing():
            self.sent_embed = await self.channel.send(self.channel, embed=self.built_embed)

    async def usend(self):
        """Edit existing GUI if available, else send new GUI"""

        try:
            await self.sent_embed.edit(embed=self.built_embed)
        except:
            pass

    async def delete(self):
        """Deletes the existing GUI if available"""

        try:
            await self.sent_embed.delete()
        except:
            pass

        self.sent_embed = None

    def update_data(self, index, data):
        """Updates a particular datapack's data

        Args:
            index (int): The index of the datapack
            data (str): The new value to set for this datapack
        """

        datapack = self.built_embed.to_dict()["fields"][index]
        self.built_embed.set_field_at(index, name=datapack["name"], value=data, inline=datapack["inline"])
