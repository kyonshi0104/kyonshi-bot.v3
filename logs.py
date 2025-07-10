import json
import discord

LOG_CONFIG_PATH = "data/logs.json"

def load_log_config():
    try:
        with open(LOG_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_log_channel_id(server_id: int, log_type: str):
    config = load_log_config()
    server_config = config.get(str(server_id), {})
    return server_config.get(log_type)

async def send_log(bot: discord.Client, guild_id: int, log_type: str, content: str, embed: discord.Embed = None):
    channel_id = get_log_channel_id(guild_id, log_type)
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            await channel.send(content, embed=embed)