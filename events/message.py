from extension import BaseEvent


class Event(BaseEvent):
    async def trigger(self, message):
        if message.author.bot:
            return

        await self.bot.process_commands(message)
