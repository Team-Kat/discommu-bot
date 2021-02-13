from discord import Embed, Color
from discord.ext.commands import Cog, Context

from extension.bot import Discommu


class BaseEvent:
    bot: Discommu

    def __init__(self, bot: Discommu):
        self.bot = bot


class BaseCommand(Cog):
    bot: Discommu

    def __init__(self, bot: Discommu):
        self.bot = bot

    async def cog_before_invoke(self, ctx: Context):
        setattr(ctx, 'userDBval', self.bot.userDB.getOne({'discordID': str(ctx.author.id)}))
