from discord.ext import commands
from discord import Color,Embed,Member
import json
import requests
import datetime
import pytz
import zoneinfo

with open("data/blockuser.json") as f:
    blackusers = json.load(f)

with open("data/owner.json", "r") as f:
    owners = json.load(f)

with open("data/developer.json") as f:
    developers = json.load(f)

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blackusers = blackusers

        async def cog_check(self,ctx):
            if ctx.author.id in blackusers:
                return False
            return True

    @commands.command()
    async def ping(self, ctx):
        raw_ping = self.bot.latency
        ping = round(raw_ping * 1000)
        await ctx.reply(f"Pong!\nPing値は{ping}msだよ。")

    @commands.command()
    async def invite(self, ctx):
        await ctx.reply(f"[BOTのリンクだよ](<https://discord.com/oauth2/authorize?client_id=1314806640968597536&permissions=598532641123830&scope=bot>)")

    @commands.command()
    async def time(self, ctx, timezone:str):

        if timezone.startswith("+"):
            now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=int(timezone))))
        else:
            try:
                dt = datetime.datetime.now()
                now = dt.astimezone(zoneinfo.ZoneInfo(timezone))
            except:
                now = "サポートされていません。"
        await ctx.send(embed=Embed(title=f"Time in {timezone}",description=now,color=Color.light_gray()))

    @commands.command()
    async def server(self, ctx):
        await ctx.send(f"今は{len(self.bot.guilds)}に参加してるよ")

    @commands.command()
    async def airest(self, ctx, message:str):
        await ctx.defer()
        headers = {"Content-Type": "application/json"}
        payload = {"model": "airest-2.5-turbo","message": message}
        response = requests.post("https://api2-airest.onrender.com/chat",headers=headers,json=payload)
        await ctx.send(response.json()["message"]["content"])


class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blackusers = blackusers

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member:Member, delete_message_days:int=0, reason:str=None):
        membername = "ユーザー" if not member.bot else "アプリ"
        if ctx.guild.me.guild_permissions.ban_members == False:
            await ctx.send(f"このBOTに{membername}をBANする権限がありません。")
            return
        if member in (owners + developers):
            await ctx.send(f"このBOTではその{membername}はBANできません。")
        elif member.id == ctx.guild.me.id:
            await ctx.send("このBOTでこのBOTをBANすることはできません。")
        elif member.id == ctx.author.id:
            await ctx.send("自分自身をBANすることはできません。")
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send("BAN対象の権限がこのBOTよりも高いためBANできません。")
        elif member.top_role >= ctx.author.top_role:
            await ctx.send("BAN対象の権限があなたより高いためBANをキャンセルしました。")
        else:
            await member.guild.ban(member,delete_message_days=delete_message_days,reason=reason)
            await ctx.send(f"✅{member.name}をBANしました！")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member:Member, reason:str=None):
        membername = "ユーザー" if not member.bot else "アプリ"
        if ctx.guild.me.guild_permissions.kick_members == False:
            await ctx.send(f"このBOTに{membername}をkickする権限がありません。")
            return
        if member in (owners + developers):
            await ctx.send(f"このBOTではその{membername}はkickできません。")
        elif member.id == ctx.guild.me.id:
            await ctx.send("このBOTでこのBOTをkickすることはできません。")
        elif member.id == ctx.author.id:
            await ctx.send("自分自身をBANすることはできません。")
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send("BAN対象の権限がこのBOTよりも高いためkickできません。")
        elif member.top_role >= ctx.author.top_role:
            await ctx.send("BAN対象の権限があなたより高いためkickをキャンセルしました。")
        else:
            await member.guild.kick(member,reason=reason)
            await ctx.send(f"✅{member.name}をKickしました！")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member:Member, minutes:int, reason:str=None):
        timeout_minutes = datetime.timedelta(minutes=minutes)
        membername = "ユーザー" if not member.bot else "アプリ"
        if ctx.guild.me.guild_permissions.moderate_members == False:
            await ctx.send(f"このBOTに{membername}をタイムアウトする権限がありません。")
            return
        if member in (owners + developers):
            await ctx.send(f"このBOTではその{membername}はタイムアウトできません。")
        elif member.id == ctx.guild.me.id:
            await ctx.send("このBOTでこのBOTをタイムアウトすることはできません。")
        elif member.id == ctx.author.id:
            await ctx.send("自分自身をBANすることはできません。")
        elif member.top_role >= ctx.guild.me.top_role:
            await ctx.send("BAN対象の権限がこのBOTよりも高いためタイムアウトできません。")
        elif member.top_role >= ctx.author.top_role:
            await ctx.send("BAN対象の権限があなたより高いためタイムアウトをキャンセルしました。")
        else:
            await member.timeout(timeout_minutes,reason=reason)
            await ctx.send(f"✅{member.name}を{minutes}分間タイムアウトしました！")



async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(SystemCommands(bot))
