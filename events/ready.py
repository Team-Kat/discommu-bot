from discord import Game

from extension import BaseEvent


class Event(BaseEvent):
    async def trigger(self):
        print(f'''
        ==========================================
        BotID: {self.bot.user.id}
        BotName: {self.bot.user}
        BotToken: {self.bot.config["token"][:10] + "*" * (len(self.bot.config["token"]) - 10)}
        ==========================================
        ''')

        self.bot.change_presence_loop.start()
