from typing import List, Union, Callable

from discord import Status, Embed, Color, Intents, Game
from discord.ext.commands import Bot
from discord.ext.tasks import loop

from pymongo import MongoClient

from json import loads

from .cmdManager import gather_events, gather_commands
from .mongoDB import Collection


class Discommu(Bot):
    def __init__(self, **kwargs):
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config: dict = loads(f.read())

        self.db = MongoClient(
            f'mongodb+srv://admin:{self.config["db"]["password"]}@{self.config["db"]["url"]}/discommu?retryWrites=true&w=majority'
        )['discommu']

        self.categoryDB = Collection(self.db["categories"])
        self.postDB = Collection(self.db["posts"])
        self.userDB = Collection(self.db["users"])
        self.commentDB = Collection(self.db["comments"])

        super().__init__(self.config['command_prefix'], intents=Intents.all(), **kwargs)
        self.remove_command('help')

        gather_events(self)
        gather_commands(self)

    def run(self):
        super().run(self.config["token"])

    @loop(minutes=1)
    async def change_presence_loop(self):
        await self.change_presence(status=Status.online, activity=Game(f'{len(self.userDB)}명의 유저가 있어요...!'))

    async def check_registered(self, ctx):
        if not self.userDB.getOne({'discordID': str(ctx.author.id)}):
            await ctx.send(embed=Embed(title='가입이 안되있습니다', color=Color.red()))
            return False
        return True

    async def check_owner(self, ctx):
        user = self.userDB.getOne({'discordID': str(ctx.author.id)})
        if (not user) or ('admin' not in user['permissions']):
            await ctx.send(embed=Embed(title='오너가 아닙니다', color=Color.red()))
            return False
        return True
