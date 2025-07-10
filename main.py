import os
import json
import logging
import urllib.request
from datetime import timezone, timedelta,datetime
import discord
from discord.ext import commands
from discord import app_commands, AuditLogAction, Colour

import logs

intents = discord.Intents.all()

COLORS = {
    "join": Colour.blue(),
    "leave": Colour.green(),
    "ban": Colour.purple(),
    "unban": Colour.green(),
    "update": Colour.orange(),
    "kick": Colour.red(),
    "timeout": Colour.gold(),
    "delete": Colour.orange(),
    "channel_create": Colour.teal(),
    "channel_delete": Colour.gold(),
    "channel_update": Colour.green()
}

def create_log_embed(title, color, fields: list[tuple], icon_url: str = None):
    embed = discord.Embed(title=title, color=color)
    for name, value in fields:
        embed.add_field(name=name, value=value, inline=False)
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    return embed


class CustomHelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        super().__init__()

    async def send_bot_help(self, mapping):
        embed = discord.Embed(
            title="Help",
            description="利用可能なコマンドの一覧です。",
            color=discord.Color.blue()
        )

        for cog, commands in mapping.items():
            command_list = "\n".join([command.name for command in commands])
            if cog:
                embed.add_field(name=cog.qualified_name, value=command_list, inline=False)
            else:
                embed.add_field(name="その他", value=command_list, inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group):
        embed = discord.Embed(
            title=f"{group.name} グループのヘルプ",
            description=group.help or "説明がありません。",
            color=discord.Color.green()
        )
        for command in group.commands:
            embed.add_field(name=command.name, value=command.help or "説明がありません。", inline=False)

    async def send_command_help(self, command):
        embed = discord.Embed(
            title=command.name,
            description=command.help or "説明がありません。",
            color=discord.Color.green()
        )
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description or "説明がありません。",
            color=discord.Color.green()
        )

        command_list = "\n".join([command.name for command in cog.get_commands()])
        embed.add_field(name="コマンド", value=command_list, inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="ky!",intents=intents)
tree = app_commands.CommandTree(client)
bot.help_command = CustomHelpCommand()

async def load_extensions():
    #load_commands
    for filename in os.listdir('./events/command'):
        if filename.endswith('.py'):
            await bot.load_extension(f'events.command.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f"Logged into {bot.user.id}.")
    await load_extensions()
    await bot.tree.sync()

# Member Join / Leave
@bot.event
async def on_member_join(member):
    now = datetime.now(timezone(timedelta(hours=9)))

    embed = create_log_embed(
        title="🟢 メンバー参加",
        color=COLORS["join"],
        fields=[
            ("ユーザー", member.mention),
            ("参加日時", now.strftime('%Y-%m-%d %H:%M:%S JST')),
            ("Bot", "✅" if member.bot else "❌")
        ],
        icon_url=member.display_avatar.url
    )
    await logs.send_log(bot, member.guild.id, "member_log", "", embed)

@bot.event
async def on_member_remove(member):
    now = datetime.now(timezone(timedelta(hours=9)))
    kicked = False

    async for entry in member.guild.audit_logs(limit=5, action=AuditLogAction.kick):
        if entry.target.id == member.id and (now - entry.created_at).total_seconds() < 10:
            # Kick用ログ（moderate_log）
            embed_kick = create_log_embed(
                title="🥾 キック",
                color=COLORS["kick"],
                fields=[
                    ("対象", member.mention),
                    ("実行者", entry.user.mention),
                    ("理由", entry.reason or "なし"),
                    ("参加日時", member.joined_at.strftime('%Y-%m-%d %H:%M:%S UTC') if member.joined_at else "不明"),
                    ("退出日時", now.strftime('%Y-%m-%d %H:%M:%S UTC')),
                    ("Bot", "✅" if member.bot else "❌")
                ],
                icon_url=member.display_avatar.url
            )
            await logs.send_log(bot, member.guild.id, "moderate_log", "", embed_kick)

            # member_log にも記録
            embed_member = create_log_embed(
                title="🔴 メンバー退出（※キック）",
                color=COLORS["leave"],
                fields=[
                    ("ユーザー", member.mention),
                    ("参加日時", member.joined_at.strftime('%Y-%m-%d %H:%M:%S UTC') if member.joined_at else "不明"),
                    ("退出日時", now.strftime('%Y-%m-%d %H:%M:%S UTC')),
                    ("Bot", "✅" if member.bot else "❌")
                ],
                icon_url=member.display_avatar.url
            )
            await logs.send_log(bot, member.guild.id, "member_log", "", embed_member)
            return

    # 通常の退出（非キック）
    embed = create_log_embed(
        title="🔴 メンバー退出",
        color=COLORS["leave"],
        fields=[
            ("ユーザー", member.mention),
            ("参加日時", member.joined_at.strftime('%Y-%m-%d %H:%M:%S UTC') if member.joined_at else "不明"),
            ("退出日時", now.strftime('%Y-%m-%d %H:%M:%S UTC')),
            ("Bot", "✅" if member.bot else "❌")
        ],
        icon_url=member.display_avatar.url
    )
    await logs.send_log(bot, member.guild.id, "member_log", "", embed)

@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=AuditLogAction.ban):
        embed = create_log_embed(
            "⛔ BAN 実行",
            COLORS["ban"],
            [
                ("対象", user.mention),
                ("実行者", entry.user.mention),
                ("理由", entry.reason or "なし")
            ],
            icon_url=user.display_avatar.url
        )
        await logs.send_log(bot, guild.id, "moderate_log", "", embed)

@bot.event
async def on_member_unban(guild, user):
    async for entry in guild.audit_logs(limit=1, action=AuditLogAction.unban):
        embed = create_log_embed(
            "🔓 BAN解除",
            COLORS["unban"],
            [
                ("対象", user.mention),
                ("実行者", entry.user.mention),
                ("理由", entry.reason or "なし")
            ],
            icon_url=entry.user.display_avatar.url
        )
        await logs.send_log(bot, guild.id, "moderate_log", "", embed)

@bot.event
async def on_member_update(before, after):
    if before.timed_out_until != after.timed_out_until:
        async for entry in after.guild.audit_logs(limit=1, action=AuditLogAction.member_update):
            is_timeout = after.timed_out_until is not None
            embed = create_log_embed(
                "⏱️ タイムアウト" if is_timeout else "🔓 タイムアウト解除",
                COLORS["timeout"] if is_timeout else COLORS["update"],
                [
                    ("対象", after.mention),
                    ("実行者", entry.user.mention),
                    ("理由", entry.reason or "なし")
                ],
                icon_url=after.display_avatar.url if is_timeout else entry.user.display_avatar.url
            )
            await logs.send_log(bot, after.guild.id, "moderate_log", "", embed)

@bot.event
async def on_message_edit(before, after):
    if before.content == after.content or before.author.bot:
        return  # 内容に変化がない or Botの編集はスキップ

    embed = create_log_embed(
        title="✏️ メッセージ編集",
        color=COLORS["update"],
        fields=[
            ("ユーザー", before.author.mention),
            ("チャンネル", before.channel.mention),
            ("編集前", before.content or "（空）"),
            ("編集後", after.content or "（空）")
        ],
        icon_url=before.author.display_avatar.url
    )
    await logs.send_log(bot, before.guild.id, "message_log", "", embed)

@bot.event
async def on_message_delete(message):
    if not message.author.bot:
        embed = create_log_embed(
            "🗑️ メッセージ削除",
            COLORS["delete"],
            [
                ("ユーザー", message.author.mention),
                ("チャンネル", message.channel.mention),
                ("内容", message.content or "（空）")
            ],
            icon_url=message.author.display_avatar.url
        )
        await logs.send_log(bot, message.guild.id, "message_log", "", embed)

@bot.event
async def on_guild_channel_create(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=AuditLogAction.channel_create):
        embed = create_log_embed(
            "📡 チャンネル作成",
            COLORS["channel_create"],
            [
                ("チャンネル", channel.mention),
                ("実行者", entry.user.mention)
            ],
            icon_url=entry.user.display_avatar.url
        )
        await logs.send_log(bot, channel.guild.id, "channel_log", "", embed)

@bot.event
async def on_guild_channel_delete(channel):
    async for entry in channel.guild.audit_logs(limit=1, action=AuditLogAction.channel_delete):
        embed = create_log_embed(
            "❌ チャンネル削除",
            COLORS["channel_delete"],
            [
                ("チャンネル名", channel.name),
                ("実行者", entry.user.mention),
                ("理由", entry.reason or "なし")
            ],
            icon_url=entry.user.display_avatar.url
        )
        await logs.send_log(bot, channel.guild.id, "channel_log", "", embed)

@bot.event
async def on_guild_channel_update(before, after):
    changes = []
    if before.name != after.name:
        changes.append(f"🔤 名前変更: {before.name} → {after.name}")
    if hasattr(before, "topic") and before.topic != after.topic:
        changes.append(f"📝 トピック変更: {before.topic or 'なし'} → {after.topic or 'なし'}")
    if before.overwrites != after.overwrites:
        changes.append("🛡️ 権限が変更されました。")
    if getattr(before, "nsfw", None) != getattr(after, "nsfw", None):
        changes.append(f"🔞 NSFW: {before.nsfw} → {after.nsfw}")

    if changes:
        async for entry in after.guild.audit_logs(limit=1, action=AuditLogAction.channel_update):
            embed = create_log_embed(
                "🛠️ チャンネル更新",
                COLORS["channel_update"],
                [
                    ("チャンネル", after.mention),
                    ("変更点", "\n".join(changes)),
                    ("実行者", entry.user.mention)
                ],
                icon_url=entry.user.display_avatar.url
            )
            await logs.send_log(bot, after.guild.id, "channel_log", "", embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("このコマンドを実行する権限がありません。")
    elif isinstance(error, commands.MissingRole):
        await ctx.send("このコマンドを実行するためのロールがありません。")
    elif isinstance(error, commands.CommandNotFound):
        print("[LOG] Command not found")
    else:
        await ctx.send(embed=discord.Embed(title="error",description=error,color=discord.Color.red()))


class Client(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.tree = discord.CommandTree(client=self)

    async def setup_hook(self) -> None:
        await self.tree.sync()

class DiscordWebHookHandler(logging.Handler):
    webhook: str
    console: logging.StreamHandler

    def __init__(self):
        self.webhook = os.environ['DISCORD_WEBHOOK']
        self.console = logging.StreamHandler()
        super().__init__()

    def emit(self, record):
        try:
            self.console.emit(record)
            urllib.request.urlopen(
            urllib.request.Request(
                self.webhook,
                data=json.dumps({
                    "content":
                    "```js\n" + self.format(record) + "\n```"
                }).encode(),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "DiscordBot (private use) Python-urllib/3.10",
                },
            )).close()
        except Exception:
            self.handleError(record)

async def log(content):
    print(content)
    await discord.Webhook.from_url(os.environ['DISCORD_WEBHOOK'],
                                    client=client).send(content)

from dotenv import load_dotenv

load_dotenv()

my_secret = os.getenv("DISCORD_TOKEN")

def run():
    bot.run(my_secret,log_handler=DiscordWebHookHandler)

run()