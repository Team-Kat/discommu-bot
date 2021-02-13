from discord import Embed, Color
from discord.ext.commands import group

from os.path import splitext
from asyncio import TimeoutError as AsyncTimeoutError, gather
from EZPaginator import Paginator
from time import time
from re import compile as rcompile

from extension import BaseCommand
from utils import divide


class Command(BaseCommand):
    name = '글'
    description = '글 관련 명령어들입니다'

    def __init__(self, bot):
        super().__init__(bot)

        for cmd in self.get_commands():
            cmd.add_check(self.bot.check_registered)
            if 'commands' in dir(cmd):
                for child_cmd in cmd.commands:
                    child_cmd.add_check(self.bot.check_registered)

    @group(name='글', aliases=['post'], help='글 명령어 그룹입니다')
    async def post(self, ctx):
        if not ctx.invoked_subcommand:
            await self.list_post(ctx)

    @group(name='댓글', aliases=['comment'], help='댓글 명령어 그룹입니다')
    async def comment(self, ctx):
        if not ctx.invoked_subcommand:
            return

    @post.command(name='작성', usage='작성 [제목]', aliases=['write'], help='글을 작성합니다', brief='usingcommand')
    async def add_post(self, ctx, *, title: str):
        msg = await ctx.send(embed=Embed(title='카테고리', description='이 글의 카테고리를 무엇으로 할까요?', color=Color.orange()))

        try:
            category = (await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=60)).content
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 작성이 취소되었습니다', color=Color.green()))
            return

        if not len(list(self.bot.categoryDB.find({'name': category}))):
            await ctx.send(embed=Embed(title='그런 이름을 가진 카테고리가 없습니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='태그', description='이 글의 태그를 무엇으로 할까요?(`/`로 분리하면 여러개가 됩니다)', color=Color.orange()))

        try:
            tags = (await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=60)).content.split('/')
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 작성이 취소되었습니다', color=Color.green()))
            return

        msg = await ctx.send(embed=Embed(title='내용', description='이 글의 내용을 작성해주세요', color=Color.orange()))

        try:
            msg = (await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=600))
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 작성이 취소되었습니다', color=Color.green()))
            return

        content = msg.content
        if msg.attachments:
            if splitext(msg.attachments[0].filename)[1][1:] in ['png', 'jpg', 'jpeg', 'gif']:
                content += f'\n![Image]({msg.attachments[0].url})'

        try:
            msg = await ctx.send(embed=Embed(title='글 작성', description=f'**제목:** `{title}`\n**내용:** `{content}`\n**카테고리:** `{category}`\n**태그 목록:** {"**,** ".join([f"`{tag}`" for tag in tags])}', color=Color.orange()))
        except Exception:
            await ctx.send(embed=Embed(title='글 작성', description='정말로 글을 작성하시겠습니까?', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (msg == r.message) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 작성을 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='글 작성을 취소했습니다', color=Color.green()))
            return

        res = self.bot.postDB.insert_one({
            'authorID': str(ctx.author.id),
            'title': title,
            'content': content,
            'category': category,
            'tag': tags,
            'hearts': [],
            'timestamp': time()
        })
        await msg.edit(embed=Embed(title=f'글을 작성했습니다\n아이디: {res.inserted_id}', color=Color.green()))

        for u in map(lambda u: self.bot.get_user(int(u['discordID'])), list(filter(lambda u: str(ctx.author.id) in u['following'], self.bot.userDB.find()))):
            try:
                await u.send(embed=Embed(title=f'{ctx.author}님이 글을 쓰셨습니다 (제목: {title} 아이디: {res.inserted_id})', color=Color.green()))
            except Exception:
                continue

    @post.command(name='삭제', usage='삭제 [아이디]', aliases=['del', 'delete', 'remove'], help='글을 삭제합니다', brief='usingcommand')
    async def del_post(self, ctx, *, id: str):
        if not self.bot.postDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 글이 없습니다', color=Color.red()))
            return

        post = self.bot.postDB.getByID(id)
        if post['authorID'] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='님이 만드신 글만 삭제 가능합니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='글 삭제', description=f'정말 글을 삭제하시겠습니까?', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (msg == r.message) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 삭제를 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='글 삭제를 취소했습니다', color=Color.green()))
            return

        self.bot.postDB.deleteByID(id)
        await msg.edit(embed=Embed(title='글을 삭제했습니다', color=Color.green()))

    @post.command(name='수정', usage='수정 [아이디]', aliases=['edit', 'update'], help='글 내용을 수정합니다', brief='usingcommand')
    async def edit_post(self, ctx, *, id: str):
        if not self.bot.postDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 글이 없습니다', color=Color.red()))
            return

        post = self.bot.postDB.getByID(id)
        if post['authorID'] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='님이 만드신 글만 수정 가능합니다', color=Color.red()))
            return

        await ctx.send(embed=Embed(title='글 수정', description='글의 내용을 수정하세요? (10분이 지나면 자동으로 취소됩니다)', color=Color.orange()))

        try:
            msg = await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=600)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 수정을 취소했습니다', color=Color.green()))
            return

        content = msg.content
        if msg.attachments:
            if splitext(msg.attachments[0].filename)[1][1:] in ['png', 'jpg', 'jpeg', 'gif']:
                content += f'\n![Image]({msg.attachments[0].url})'

        msg = await ctx.send(embed=Embed(title='글 수정', description='정말 글을 수정하겠습니까?', color=Color.orange()))

        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message == msg) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='글 수정을 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='글 수정을 취소했습니다', color=Color.green()))
            return

        self.bot.postDB.updateByID(id, {
            'content': content
        })
        await msg.edit(embed=Embed(title='글 내용을 수정했습니다', color=Color.green()))

    @post.command(name='보기', aliases=['show'], usage='보기 [아이디]', help='글을 보여줍니다', brief='usingcommand')
    async def info_post(self, ctx, *, id: str):
        if not self.bot.postDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 글이 없습니다', color=Color.red()))
            return

        def format_post(content: str) -> str:
            for i in rcompile(r'!\[.+\]\((?P<url>.+)\)').finditer(content):
                content = content.replace(i.group(), f'[사진]({i.group("url")})')
            return content

        post = self.bot.postDB.getByID(id)
        msg = await ctx.send(embed=Embed(
            title=post['title'],
            description=f'{format_post(post["content"])}\n\n**작성자:** {self.bot.get_user(int(post["authorID"]))}\n**카테고리:** `{post["category"]}`\n**태그:** {"**,** ".join([f"`{tag}`" for tag in post["tag"]])}\n\n:heart: `{len(post["hearts"])}`\n:speech_balloon: `{len(self.bot.commentDB.get({"postID": id}))}`',
            color=Color.green()
        ))

        async def change_message():
            post = self.bot.postDB.getByID(id)
            await msg.edit(embed=Embed(
                title=post['title'],
                description=f'{format_post(post["content"])}\n\n**작성자:** {self.bot.get_user(int(post["authorID"]))}\n**카테고리:** `{post["category"]}`\n**태그:** {"**,** ".join([f"`{tag}`" for tag in post["tag"]])}\n\n:heart: `{len(post["hearts"])}`\n:speech_balloon: `{len(self.bot.commentDB.get({"postID": id}))}`',
                color=Color.green()
            ))

        hearted = str(ctx.author.id) in post['hearts']
        await msg.add_reaction('❤' if not hearted else '💔')
        await msg.add_reaction('💬')

        if str(ctx.author.id) == post['authorID']:
            do = {
                '✏': self.edit_post,
                '🗑': self.del_post
            }

            for emoji in do:
                await msg.add_reaction(emoji)
        else:
            do = {}

        while True:
            try:
                r = str(
                    list(
                        await self.bot.wait_for(
                            'reaction_add',
                            timeout=600,
                            check=lambda r, u: (u == ctx.author) and (str(r.emoji) in (['💬', '❤' if not hearted else '💔'] + list(do.keys()))) and (r.message == msg)
                        )
                    )[0].emoji
                )
            except Exception:
                try:
                    await gather(
                        msg.remove_reaction('❤' if not hearted else '💔', ctx.guild.me),
                        msg.remove_reaction('💬', ctx.guild.me)
                    )
                except Exception:
                    break
                break

            if r == ('❤' if not hearted else '💔'):
                if hearted:
                    post['hearts'].remove(str(ctx.author.id))
                    try:
                        await gather(
                            msg.remove_reaction('💔', ctx.guild.me),
                            msg.add_reaction('❤')
                        )
                    except Exception:
                        break

                else:
                    post['hearts'].append(str(ctx.author.id))
                    try:
                        await gather(
                            msg.remove_reaction('❤', ctx.guild.me),
                            msg.add_reaction('💔')
                        )
                    except Exception:
                        break

                    for u in map(lambda u: self.bot.get_user(int(u["discordID"])), list(filter(lambda u: str(ctx.author.id) in u["following"], self.bot.userDB.find()))):
                        try:
                            await u.send(embed=Embed(title=f'{ctx.author}님이 하트를 누르셨습니다 (제목: {post["title"]} 아이디: {id})', color=Color.green()))
                        except Exception:
                            continue

                self.bot.postDB.updateByID(id, {'hearts': post['hearts']})
                hearted = not hearted

            elif r == '💬':
                await self.show_comment(ctx, id=id)

            elif do:
                await do[r](ctx, id=id)
                if r == '🗑':
                    await msg.delete()
                    return

            await change_message()

    @post.command(name='검색', aliases=['search', '목록', 'list'], usage='검색 <쿼리>', help='글을 검색합니다(검색어가 없으면 모두 다 표시)')
    async def list_post(self, ctx, *, query: str = None):
        if not query:
            postlist = list(self.bot.postDB.find())
            title = '글 목록'
            no_description = '글이 없습니다'

        else:
            postlist = []
            _idlist = []

            _postlist = self.bot.postDB.get({'title': {'$regex': f'.*{query}.*'}}) + self.bot.postDB.get({'content': {'$regex': f'.*{query}.*'}})

            for data in _postlist:
                if data['_id'] in _idlist:
                    continue
                _idlist.append(data['_id'])
                postlist.append(data)

            title = f'"{query}" 검색 결과'
            no_description = '검색 결과가 없습니다'

        embeds = []

        for categories in divide(postlist, 10):
            embed = Embed(
                title=title,
                color=Color.green()
            )

            for post in categories:
                embed.add_field(name=f'{post["title"]} ({post["_id"]})', value=f'by `{self.bot.get_user(int(post["authorID"]))}` :heart: `{len(post["hearts"])}` :speech_balloon: `{len(self.bot.commentDB.get({"postID": post["_id"]}))}`', inline=False)

            embeds.append(embed)

        if embeds:
            msg = await ctx.send(embed=embeds[0])
            await Paginator(self.bot, msg, embeds=embeds).start()
        else:
            await ctx.send(embed=Embed(title=title, description=no_description, color=Color.green()))

    @comment.command(name='작성', aliases=['new', 'write'], usage='작성 [아이디]', help='댓글을 작성합니다', brief='usingcommand')
    async def write_comment(self, ctx, id: str):
        if not self.bot.postDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 글이 없습니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='댓글 작성', description='댓글의 내용을 입력해주세요 (5분동안 메시지가 없으면 취소됨)', color=Color.orange()))

        try:
            comment = (await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=300)).content
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='댓글 작성을 취소했습니다', color=Color.green()))
            return

        msg = await ctx.send(embed=Embed(title='댓글 작성', description='정말 댓글을 작성할까요?', color=Color.orange()))
        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message == msg) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='댓글 작성을 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='댓글 작성을 취소했습니다', color=Color.green()))
            return

        self.bot.commentDB.insert_one({'authorID': str(ctx.author.id), 'content': comment, 'timestamp': time(), 'reply': '', 'postID': id})
        await msg.edit(embed=Embed(title='댓글을 작성했습니다', color=Color.green()))
        return True

    @comment.command(name='삭제', aliases=['delete', 'remove'], usage='삭제 [댓글아이디]', help='댓글을 삭제합니다', brief='usingcommand')
    async def delete_comment(self, ctx, id: str):
        if not self.bot.commentDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 댓글이 없습니다', color=Color.red()))
            return

        comment = self.bot.commentDB.getByID(id)

        if comment['authorID'] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='자기가 작성한 댓글만 삭제 가능합니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='댓글 삭제', description='이 댓글을 삭제할까요?', color=Color.orange()))
        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message == msg) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='댓글 삭제를 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='댓글 삭제를 취소했습니다', color=Color.green()))
            return

        self.bot.commentDB.deleteByID(id)
        await msg.edit(embed=Embed(title='댓글을 삭제했습니다', color=Color.green()))
        return True

    @comment.command(name='수정', aliases=['edit'], usage='수정 [댓글아이디]', help='댓글을 수정합니다', brief='usingcommand')
    async def edit_comment(self, ctx, id: str):
        if not self.bot.commentDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 댓글이 없습니다', color=Color.red()))
            return

        comment = self.bot.commentDB.getByID(id)

        if comment["authorID"] != str(ctx.author.id):
            await ctx.send(embed=Embed(title='자기가 작성한 댓글만 삭제 가능합니다', color=Color.red()))
            return

        msg = await ctx.send(embed=Embed(title='댓글 수정', description='댓글 내용을 무엇으로 수정할까요?', color=Color.orange()))
        try:
            new_comment = (await self.bot.wait_for('message', check=(lambda m: (m.channel == ctx.channel) and (m.author == ctx.author)), timeout=600)).content
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='댓글 수정을 취소했습니다', color=Color.green()))
            return

        msg = await ctx.send(embed=Embed(title='댓글 수정', description=f'`{comment["content"]}` 이 댓글을 `{new_comment}`로 바꿀까요?', color=Color.orange()))
        await msg.add_reaction('⭕')
        await msg.add_reaction('❌')

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', check=(lambda r, u: (str(r.emoji) in ('⭕', '❌')) and (r.message == msg) and (u == ctx.author)), timeout=30)
        except AsyncTimeoutError:
            await msg.edit(embed=Embed(title='댓글 삭제를 취소했습니다', color=Color.green()))
            return

        if str(reaction) == '❌':
            await msg.edit(embed=Embed(title='댓글 삭제를 취소했습니다', color=Color.green()))
            return

        self.bot.commentDB.updateByID(id, {'content': new_comment})
        await msg.edit(embed=Embed(title='댓글을 수정했습니다', color=Color.green()))
        return True

    @comment.command(name='보기', aliases=['show'], usage='보기 [아이디]', help='댓글 리스트를 보여줍니다', brief='usingcommand')
    async def show_comment(self, ctx, id: str):
        if not self.bot.postDB.getByID(id):
            await ctx.send(embed=Embed(title='그런 아이디를 가진 글이 없습니다', color=Color.red()))
            return

        commentlist = self.bot.commentDB.get({'postID': id})
        if not commentlist:
            num = -1
            msg = await ctx.send(embed=Embed(title='이 글에 댓글이 없습니다', color=Color.green()))
        else:
            num = 0
            msg = await ctx.send(embed=Embed(title=f'#1 {commentlist[0]["content"]}', description=f'by `{self.bot.get_user(int(commentlist[0]["authorID"]))}`', color=Color.green()))

        while True:
            awaitreaction = []
            commentlist = self.bot.commentDB.get({'postID': id})

            if (num < -1) or (num >= len(commentlist)):
                num = 0

            if not commentlist:
                num = -1
                await msg.edit(embed=Embed(title='이 글에 댓글이 없습니다', color=Color.green()))
            else:
                await msg.edit(embed=Embed(title=f'#{num + 1} {commentlist[num]["content"]}', description=f'by `{self.bot.get_user(int(commentlist[num]["authorID"])) or "익명의 유저"}`', color=Color.green()))

            awaitreaction.extend(['◀', '▶', '➕'])

            if (num >= 0) and (commentlist[num]['authorID'] == str(ctx.author.id)):
                awaitreaction.extend(['✏', '🗑'])

            for r in awaitreaction:
                await msg.add_reaction(r)

            try:
                r = str(
                    list(
                        await self.bot.wait_for(
                            'reaction_add',
                            timeout=600,
                            check=lambda r, u: (u == ctx.author) and (str(r.emoji) in awaitreaction) and (r.message == msg)
                        )
                    )[0].emoji
                )
            except Exception:
                try:
                    await msg.delete()
                except Exception:
                    break
                break

            if r == '◀':
                if num == -1:
                    pass
                elif num <= 0:
                    num = len(commentlist) - 1
                else:
                    num -= 1

            elif r == '▶':
                if num == -1:
                    pass
                elif num >= len(commentlist) - 1:
                    if not commentlist:
                        num = -1
                    else:
                        num = 0
                num += 1

            elif r == '➕':
                res = await self.write_comment(ctx, id)
                if res and (num == -1):
                    num = 0

            elif r == '✏':
                await self.edit_comment(ctx, commentlist[num]['_id'])

            elif r == '🗑':
                await self.delete_comment(ctx, commentlist[num]['_id'])

            corlist = []
            for r in awaitreaction:
                if r in ['✏', '🗑']:
                    corlist.append(r)

            try:
                await gather(*[msg.remove_reaction(r, ctx.guild.me) for r in corlist])
            except Exception:
                pass
