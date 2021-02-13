import discord

from discord import Embed, Color
from discord.ext.commands import command

from ast import parse, Expr, If, With, Return, fix_missing_locations
from subprocess import check_output

from extension import BaseCommand


class Command(BaseCommand):
    name = '관리자'
    description = '관리자들만 사용할수 있는 명령어입니다'

    def __init__(self, bot):
        super().__init__(bot)

        for cmd in self.get_commands():
            cmd.add_check(self.bot.check_owner)

    @command(name='eval', help='코드를 실행합니다', usage='eval [코드]')
    async def eval(self, ctx, *, code: str = None):
        def insert_returns(body):
            if isinstance(body[-1], Expr):
                body[-1] = Return(body[-1].value)
                fix_missing_locations(body[-1])

            if isinstance(body[-1], If):
                insert_returns(body[-1].body)
                insert_returns(body[-1].orelse)

            if isinstance(body[-1], With):
                insert_returns(body[-1].body)

        if not code:
            await ctx.send(embed=Embed(title='코드를 입력해주세요', color=Color.red()))
            return

        func_content = '\n'.join(f'    {line}' for line in code.strip('```').lstrip('py').strip('\n').splitlines())
        code = f'async def _eval_exp():\n{func_content}'

        parsed = parse(code)
        insert_returns(parsed.body[0].body)

        try:
            env = {
                'bot': self.bot,
                'ctx': ctx,
                'discord': discord
            }
            exec(compile(parsed, filename='<ast>', mode='exec'), env)
            res = await eval('_eval_exp()', env)
        except Exception as e:
            await ctx.send(embed=Embed(title='처리중 오류가 생겼습니다', description=f'```py\n{repr(e)}\n```', color=Color.red()))
            return

        await ctx.send(embed=Embed(title='EVAL 결과', description=f'```py\n{res}\n```', color=Color.green()))

    @command(name='shell', description='콘솔 명령어를 실행합니다', usage='shell [명령어]')
    async def shell(self, ctx, *, command: str = None):
        if not command:
            await ctx.send(embed=Embed(title='명령어를 입력해주세요', color=Color.red()))
            return

        command = command.strip('```').lstrip('sh').strip('\n')

        try:
            res = check_output(command, shell=True, encoding='utf-8')
        except Exception:
            await ctx.send(embed=Embed(title='실행 중 오류가 생겼습니다', color=Color.red()))
            return

        await ctx.send(embed=Embed(title='SHELL 결과', description=f'```sh\n{res}\n```', color=Color.green()))
