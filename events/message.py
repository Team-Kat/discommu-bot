from extension import BaseEvent


class Event(BaseEvent):
    async def trigger(self, message):
        if message.author.bot:
            return
        if not message.content.startswith(self.bot.config["command_prefix"]):
            return

        await self.bot.process_commands(message)
        self.bot.userCommands[str(message.author.id)] = False
