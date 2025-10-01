from discord.ext import commands
from discord import app_commands, Color, Embed, Member, File
import discord
import json
import requests
import datetime
import zoneinfo
import qrcode
from PIL import Image
import io

def resize_contain_with_padding(img: Image.Image, target_size: tuple, bg_color="white") -> Image.Image:
    img_copy = img.copy()
    img_copy.thumbnail(target_size, Image.LANCZOS)
    background = Image.new("RGBA", target_size, bg_color)
    offset = (
        (target_size[0] - img_copy.width) // 2,
        (target_size[1] - img_copy.height) // 2
    )
    background.paste(img_copy, offset)
    return background

with open("data/blockuser.json") as f:
    blackusers = json.load(f)

with open("data/owner.json", "r") as f:
    owners = json.load(f)

with open("data/developer.json") as f:
    developers = json.load(f)

class GeneralCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="コマンド一覧を表示します")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(title="ヘルプ", description="利用可能なコマンド一覧", color=discord.Color.blue())

        text_commands = []
        for cmd in self.bot.commands:
            if not cmd.hidden:
                text_commands.append(f"`{cmd.name}` - {cmd.help or '説明なし'}")
        embed.add_field(name="テキストコマンド (!)", value="\n".join(text_commands) or "なし", inline=False)

        slash_commands = []
        for cmd in self.bot.tree.get_commands():
            if isinstance(cmd, app_commands.Command):
                slash_commands.append(f"`/{cmd.name}` - {cmd.description or '説明なし'}")
        embed.add_field(name="スラッシュコマンド (/)", value="\n".join(slash_commands) or "なし", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="BOTのPing値を返します")
    async def ping(self, interaction: discord.Interaction):
        ping = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"Pong!\nPing値は {ping}ms だよ。")

    @app_commands.command(name="invite", description="BOTの招待リンクを表示します")
    async def invite(self, interaction: discord.Interaction):
        await interaction.response.send_message("[BOTのリンクだよ](<https://discord.com/oauth2/authorize?client_id=1314806640968597536&permissions=598532641123830&scope=bot>)")

    @app_commands.command(name="time", description="指定したタイムゾーンの現在時刻を表示します")
    @app_commands.describe(timezone="例: Asia/Tokyo または +9")
    async def time(self, interaction: discord.Interaction, timezone: str):
        try:
            if timezone.startswith("+"):
                now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=int(timezone))))
            else:
                dt = datetime.datetime.now()
                now = dt.astimezone(zoneinfo.ZoneInfo(timezone))
            await interaction.response.send_message(embed=Embed(title=f"Time in {timezone}", description=str(now), color=Color.light_gray()))
        except Exception:
            await interaction.response.send_message("サポートされていません。", ephemeral=True)

    @app_commands.command(name="server", description="BOTが参加しているサーバー数を表示します")
    async def server(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"今は {len(self.bot.guilds)} サーバーに参加してるよ")

    @app_commands.command(name="airest", description="AIにメッセージを送信して応答を受け取ります")
    @app_commands.describe(message="AIに送るメッセージ")
    async def airest(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer()
        headers = {"Content-Type": "application/json"}
        payload = {"model": "airest-2.5-turbo", "message": message}
        response = requests.post("https://api2-airest.onrender.com/chat", headers=headers, json=payload)
        await interaction.followup.send(response.json()["message"]["content"])

    @app_commands.command(name="qrcode",description="任意のQRコードを生成します")
    @app_commands.describe(data="QRコードに埋め込む文字列",
        fill_color="QRコードの色（デフォルト：#000000）",
        background_color="背景色（デフォルト：#ffffff）",
        background_image="背景画像（アップロード）")
    async def qrcode(
        self,
        interaction: discord.Interaction,
        data: str,
        fill_color: str = "#000000",
        background_color: str = "#ffffff",
        background_image: discord.Attachment = None
    ):
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color=fill_color, back_color="transparent").convert("RGBA")

        if background_image:
            image_bytes = await background_image.read()
            bg = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
            bg = resize_contain_with_padding(bg, qr_img.size, background_color)
        else:
            bg = Image.new("RGBA", qr_img.size, background_color)

        final_img = Image.alpha_composite(bg, qr_img)

        buffer = io.BytesIO()
        final_img.save(buffer, format="PNG")
        buffer.seek(0)
        file = File(buffer, filename="qrcode.png")

        # 埋め込みメッセージ
        embed = Embed(title="QRコード", description=f"```{data}```", color=0x2ecc71)
        embed.set_image(url="attachment://qrcode.png")
        embed.set_footer(text="made by kyonshi-bot", icon_url="https://kyonshi.com/res/kyonshi.png")

        await interaction.response.send_message(embed=embed, file=file)

    @app_commands.command(name="say",description="任意の文字列をメッセージとして送信します。")
    @app_commands.describe(message="喋らせたいメッセージ")
    async def say(self, interaction:discord.Interaction, message:str):
        await interaction.channel.send(f"{message}\n-# saycommandによるメッセージ")
        await interaction.response.send_message("送信しました。",ephemeral=True)

class SystemCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="指定したメンバーをBANします")
    @app_commands.describe(member="BAN対象", delete_message_days="削除する日数", reason="BAN理由")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: Member, delete_message_days: int = 0, reason: str = None):
        if member.id in owners + developers:
            await interaction.response.send_message("このBOTではそのユーザーはBANできません。", ephemeral=True)
            return
        if member.id == interaction.user.id or member.id == interaction.guild.me.id:
            await interaction.response.send_message("自分自身またはBOTをBANすることはできません。", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role or member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("対象の権限が高いためBANできません。", ephemeral=True)
            return
        await interaction.guild.ban(member, delete_message_days=delete_message_days, reason=reason)
        await interaction.response.send_message(f"✅ {member.name} をBANしました！")

    @app_commands.command(name="kick", description="指定したメンバーをKickします")
    @app_commands.describe(member="Kick対象", reason="Kick理由")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: Member, reason: str = None):
        if member.id in owners + developers:
            await interaction.response.send_message("このBOTではそのユーザーはKickできません。", ephemeral=True)
            return
        if member.id == interaction.user.id or member.id == interaction.guild.me.id:
            await interaction.response.send_message("自分自身またはBOTをKickすることはできません。", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role or member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("対象の権限が高いためKickできません。", ephemeral=True)
            return
        await interaction.guild.kick(member, reason=reason)
        await interaction.response.send_message(f"✅ {member.name} をKickしました！")

    @app_commands.command(name="timeout", description="指定したメンバーをタイムアウトします")
    @app_commands.describe(member="タイムアウト対象", minutes="タイムアウト時間（分）", reason="理由")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: Member, minutes: int, reason: str = None):
        timeout_duration = datetime.timedelta(minutes=minutes)
        if member.id in owners + developers:
            await interaction.response.send_message("このBOTではそのユーザーはタイムアウトできません。", ephemeral=True)
            return
        if member.id == interaction.user.id or member.id == interaction.guild.me.id:
            await interaction.response.send_message("自分自身またはBOTをタイムアウトすることはできません。", ephemeral=True)
            return
        if member.top_role >= interaction.guild.me.top_role or member.top_role >= interaction.user.top_role:
            await interaction.response.send_message("対象の権限が高いためタイムアウトできません。", ephemeral=True)
            return
        await member.timeout(timeout_duration, reason=reason)
        await interaction.response.send_message(f"✅ {member.name} を {minutes} 分間タイムアウトしました！")


async def setup(bot):
    await bot.add_cog(GeneralCommands(bot))
    await bot.add_cog(SystemCommands(bot))
