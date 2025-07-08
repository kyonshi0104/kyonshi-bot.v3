import discord
from discord.ext import commands
from discord import app_commands
import json

with open("data/owner.json", "r") as f:
    owners = json.load(f)

with open("data/developer.json") as f:
    developers = json.load(f)

with open("data/blockuser.json") as f:
    blackusers = json.load(f)

with open("data/blockserver.json") as f:
    blackservers = json.load(f)

class DebugCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developers = developers
        self.owners = owners
        self.blackusers = blackusers
        self.blackservers = blackservers

        async def cog_check(self,ctx):
            if ctx.author.id in blackusers:
                return False
            return True

    @commands.group(name="debug",hidden=True)
    async def debug(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('有効なサブコマンドを指定してください。')
            return

        if ctx.author.id not in (self.developers + self.owners):
            await ctx.send("開発者用の機能です。")
            return

    @debug.command()
    async def developers(self, ctx):
        devs = ""
        for dev in self.developers:
            name = await self.bot.fetch_user(dev)
            devs += f"{name.name} - {dev}\n"
        await ctx.send(embed=discord.Embed(title="Kyonshi-Bot Developers", description=devs, color=discord.Color.blue()))

    @debug.command()
    async def blacklist(self, ctx, list_type: str):
        if list_type not in ["users", "servers"]:
            await ctx.send("users,またはserversのどちらかを指定してください。")
            return

        blacks = ""
        if list_type == "users":
            listtype = self.blackusers
            cmd = self.bot.fetch_user
            title = "ユーザー"
        else:
            listtype = self.blackservers
            cmd = self.bot.fetch_guild
            title = "サーバー"

        for black in listtype:
            name = await cmd(black)
            blacks += f"{name.name} - {black}\n"
        await ctx.send(embed=discord.Embed(title=f"ブロック中の{title}", description=blacks, color=discord.Color.red()))

    @debug.command()
    async def blacklist_add(self, ctx, list_type: str, item_id: int):
        try:
            if list_type == "user":
                if item_id in self.blackusers:
                    await ctx.send("そのユーザーは既にブラックリストに追加されています。")
                    return
                if item_id in (developers + owners):
                    if ctx.author.id in owners:
                        user = await self.bot.fetch_user(item_id)
                        self.developers.remove(item_id)
                        with open("data/developer.json", "w") as f:
                            json.dump(self.developers, f)
                        await ctx.send(f"{user.name} を開発者から削除しました。")
                    else:
                        await ctx.send("開発者ユーザーをブラックリストに登録することはできません。")
                        return
                user = await self.bot.fetch_user(item_id)
                self.blackusers.append(item_id)
                with open("data/blockuser.json", "w") as f:
                    json.dump(self.blackusers, f)
                await ctx.send(f"{user.name} をブラックリストに追加しました。")
            elif list_type == "server":
                if item_id in self.blackservers:
                    await ctx.send("そのサーバーは既にブラックリストに追加されています。")
                    return
                server = await self.bot.fetch_guild(item_id)
                self.blackservers.append(item_id)
                with open("data/blockserver.json", "w") as f:
                    json.dump(self.blackservers, f)
                await ctx.send(f"サーバー - {server.name} をブラックリストに追加しました。")
            else:
                await ctx.send("user,またはserverのどちらかを指定してください。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def blacklist_remove(self, ctx, list_type: str, item_id: int):
        try:
            if list_type == "user":
                if not item_id in self.blackusers:
                    await ctx.send("そのユーザーはブラックリスト内に存在しません。")
                    return
                user = await self.bot.fetch_user(item_id)
                self.blackusers.remove(item_id)
                with open("data/blockuser.json", "w") as f:
                    json.dump(self.blackusers, f)
                await ctx.send(f"{user.name} をブラックリストから削除しました。")
            elif list_type == "server":
                if not item_id in self.blackservers:
                    await ctx.send("そのサーバーはブラックリスト内に存在しません。")
                    return
                server = await self.bot.fetch_guild(item_id)
                self.blackservers.remove(item_id)
                with open("data/blockserver.json", "w") as f:
                    json.dump(self.blackservers, f)
                await ctx.send(f"サーバー - {server.name} をブラックリストから削除しました。")
            else:
                await ctx.send("user,またはserverのどちらかを指定してください。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def developer_add(self, ctx, user_id: int):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return

        try:
            if user in blackusers:
                userA = await self.bot.fetch_user(user)
                self.blackusers.remove(user)
                with open("data/blockuser.json", "w") as f:
                    json.dump(self.blackusers, f)
                await ctx.send(f"{userA.name} をブラックリストから削除しました。")
            user = await self.bot.fetch_user(user_id)
            self.developers.append(user_id)
            with open("data/developer.json", "w") as f:
                json.dump(self.developers, f)
            await ctx.send(f"{user.name} を開発者に設定しました。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def developer_remove(self, ctx, user_id: int):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return

        try:
            user = await self.bot.fetch_user(user_id)
            self.developers.remove(user_id)
            with open("data/developer.json", "w") as f:
                json.dump(self.developers, f)
            await ctx.send(f"{user.name} を開発者から削除しました。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def owner_add(self, ctx, user_id: int):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return

        try:
            user = await self.bot.fetch_user(user_id)
            self.owners.append(user_id)
            with open("data/owner.json", "w") as f:
                json.dump(self.owners, f)
            await ctx.send(f"{user.name} をオーナーに設定しました。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def owner_remove(self, ctx, user_id: int):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return

        try:
            user = await self.bot.fetch_user(user_id)
            self.owners.remove(user_id)
            with open("data/owner.json", "w") as f:
                json.dump(self.owners, f)
            await ctx.send(f"{user.name} をオーナーから除外しました。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def global_ban(self, ctx ,user_id: int):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return

        try:
            guilds = self.bot.builds
            user = self.bot.fetch_user(user_id)

            for server in guilds:
                try:
                    await server.ban(user=user,reason="開発者が危険なユーザーと判断したため,global_banコマンドが実行されました。")
                    await ctx.send(f"Banned from {server.name}")
                except:
                    await ctx.send(f"{server.name}にて権限不足または何らかの例外が発生しました。")
        except Exception as e:
            await ctx.send(embed=discord.Embed(title="エラー", description=str(e), color=discord.Color.red()))

    @debug.command()
    async def botexec(self, ctx):
        if ctx.author.id not in self.owners:
            await ctx.send("BOT所有者用のコマンドです。")
            return
        await ctx.send("開発中です")

class tester(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.developers = developers
        self.owners = owners
        self.blackusers = blackusers
        self.blackservers = blackservers

    @app_commands.command()
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("TEST OK")

async def setup(bot):
    await bot.add_cog(DebugCommands(bot))
    await bot.add_cog(tester(bot))