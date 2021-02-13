from discord import Embed, Color
from discord.ext.commands import Context

from discord.errors import (
    Forbidden
)
from discord.ext.commands.errors import (
    CommandNotFound, BotMissingPermissions, NoPrivateMessage,
    UserNotFound, MissingPermissions, BadArgument,
    MissingRequiredArgument, ConversionError, NotOwner,
    CheckFailure
)

from extension import BaseEvent


class Event(BaseEvent):
    async def trigger(self, ctx: Context, e: Exception):
        switch = {
            NotOwner: '오너가 아닙니다',
            NoPrivateMessage: 'DM에서는 사용 불가한 명령어입니다',
            ConversionError: '양식이 잘못되었습니다',
            MissingRequiredArgument: '양식이 잘못되었습니다',
            BadArgument: '양식이 잘못되었습니다',
            BotMissingPermissions: '봇에게 권한이 부족합니다',
            MissingPermissions: '유저에게 권한이 부족합니다',
            Forbidden: '권한이 부족합니다',
            UserNotFound: '없는 유저입니다'
        }

        if isinstance(e, CommandNotFound):
            cmd = ctx.message.content[len(self.bot.config['command_prefix']): ctx.message.content.index(' ') if ' ' in ctx.message.content else len(ctx.message.content)]
            await ctx.send(embed=Embed(title=f'{cmd} 명령어를 찾을수 없습니다', color=Color.red()))

        elif isinstance(e, CheckFailure):
            return

        for error in switch:
            if not isinstance(e, error):
                continue
            await ctx.send(embed=Embed(title=switch[error], color=Color.red()))
            return

        await ctx.send(embed=Embed(title='등록되지 않은 ERRrOR가 발생했습니다', description=f'```py\n{repr(e)}\n```', color=Color.red()))
