from discord import Embed, Color
from discord.ext.commands import command, group

from asyncio import TimeoutError
from EZPaginator import Paginator

from extension import BaseCommand
from utils import divide


class Command(BaseCommand):
    name = '카테고리'
    description = '카테고리 관련 명령어들입니다'

    def __init__(self, bot):
        super().__init__(bot)

        for cmd in self.get_commands():
            cmd.add_check(self.bot.check_registered)
            if 'commands' in dir(cmd):
                for child_cmd in cmd.commands:
                    child_cmd.add_check(self.bot.check_registered)

    @group(name='카테고리', aliases=['category'], help='카테고리 명령어 그룹입니다')
    async def category(self, ctx):
        if not ctx.invoked_subcommand:
            await self.list_category(ctx)

    @category.command(name='추가', usage='추가 [이름] [설명]', aliases=['add', 'new'], help='카테고리를 추가합니다', brief='usingcommand')
    async def add_category(self, ctx, name: str, *, description: str):
        if self.bot.categoryDB.getOne({'name': name}):
            await ctx.send(embed=Embed(title='같은 이름을 가진 카테고리가 이미 존재합니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='카테고리 추가', description=f'**이름:** `{name}`\n**설명:** `{description}`', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message.channel == ctx.channel) and (u == ctx.author)), timeout=30)
        except TimeoutError:
            await msg.edit(embed=Embed(title='카테고리 추가를 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='카테고리 추가를 취소했습니다', color=Color.green()))
            return

        self.bot.categoryDB.insert_one({
            'authorID': str(ctx.author.id),
            'name': name,
            'description': description
        })
        await msg.edit(embed=Embed(title='카테고리를 추가했습니다', color=Color.green()))

    @category.command(name='삭제', usage='삭제 [이름]', aliases=['del', 'delete', 'remove'], help='카테고리를 삭제합니다', brief='usingcommand')
    async def del_category(self, ctx, name: str):
        if not self.bot.categoryDB.getOne({'name': name}):
            await ctx.send(embed=Embed(title='그런 이름을 가진 카테고리가 없습니다', color=Color.red()))
            return

        category = self.bot.categoryDB.getOne({'name': name})
        if category['authorID'] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='님이 만드신 카테고리만 삭제 가능합니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='카테고리 삭제', description=f'정말 카테고리 `{name}`를 삭제하시겠습니까?', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message.channel == ctx.channel) and (u == ctx.author)), timeout=30)
        except TimeoutError:
            await msg.edit(embed=Embed(title='카테고리 삭제를 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='카테고리 삭제를 취소했습니다', color=Color.green()))
            return

        self.bot.categoryDB.delete_one({
            'authorID': str(ctx.author.id),
            'name': name
        })
        await msg.edit(embed=Embed(title='카테고리를 삭제했습니다', color=Color.green()))

    @category.command(name='수정', usage='수정 [이름]', aliases=['edit', 'update'], help='카테고리의 설명을 수정합니다', brief='usingcommand')
    async def edit_category(self, ctx, name: str):
        if not self.bot.categoryDB.getOne({'name': name}):
            await ctx.send(embed=Embed(title='그런 이름을 가진 카테고리가 없습니다', color=Color.red()))
            return

        category = self.bot.categoryDB.getOne({'name': name})
        if category['authorID'] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='님이 만드신 카테고리만 수정 가능합니다', color=Color.red()))
            return

        await ctx.send(embed=Embed(title='카테고리 수정', description=f'카테고리 `{name}`의 설명을 무엇으로 바꿀까요? (1분이 지나면 자동으로 취소됩니다)', color=Color.orange()))

        try:
            msg = await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=60)
        except TimeoutError:
            await msg.edit(embed=Embed(title='카테고리 수정을 취소했습니다', color=Color.green()))
            return

        desc = msg.content
        msg = await ctx.send(embed=Embed(title='카테고리 수정', description=f'정말 카테고리 `{name}`의 설명을 `{desc}`로 수정하겠습니까?', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message.channel == ctx.channel) and (u == ctx.author)), timeout=30)
        except TimeoutError:
            await msg.edit(embed=Embed(title='카테고리 수정을 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='카테고리 수정을 취소했습니다', color=Color.green()))
            return

        self.bot.categoryDB.update_one({
            'authorID': str(ctx.author.id),
            'name': name
        }, {
            '$set': {
                'description': desc
            }
        })
        await msg.edit(embed=Embed(title='카테고리를 수정했습니다', color=Color.green()))

    @category.command(name='정보', usage='정보 [이름]', aliases=['info'], help='카테고리의 정보를 알려줍니다')
    async def info_category(self, ctx, name: str):
        if not self.bot.categoryDB.find({'name': name}):
            await ctx.send(embed=Embed(title='그런 이름을 가진 카테고리가 없습니다', color=Color.red()))
            return

        category = self.bot.categoryDB.getOne({'name': name})
        await ctx.send(embed=Embed(
            title=f'{name} 카테고리 정보',
            description=f'**설명:** `{category["description"]}`\n**글 수:** `{len(list(self.bot.postDB.find({"category": name})))}`',
            color=Color.green()
        ))

    @category.command(name='목록', usage='목록', aliases=['list'], help='카테고리 리스트를 알려줍니다')
    async def list_category(self, ctx):
        embeds = []

        for categories in divide(list(self.bot.categoryDB.find()), 10):
            embed = Embed(
                title='카테고리 목록',
                color=Color.green()
            )

            for category in categories:
                embed.add_field(name=category['name'], value=f'`{category["description"]}`')

            embeds.append(embed)

        if embeds:
            msg = await ctx.send(embed=embeds[0])
            await Paginator(self.bot, msg, embeds=embeds).start()
        else:
            await ctx.send(embed=Embed(title='카테고리 목록', description='카테고리가 없습니다', color=Color.green()))
