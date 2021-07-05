from discord.ext import commands
from .slash_commands import BaseSlashCommand
from discord_message_components.tools import V8Route


async def create_command(command: BaseSlashCommand, client: commands.Bot):
    r = await client.http.request(
        V8Route("POST", f"/applications/{client.user.id}/commands"),
        json=command.to_dict(),
    )
    print(r)


async def create_guild_command(
    command: BaseSlashCommand, client: commands.Bot, guild_id
):
    r = await client.http.request(
        V8Route("POST", f"/applications/{client.user.id}/guilds/{guild_id}/commands"),
        json=command.to_dict(),
    )
    print(r)


async def get_commands(client):
    return await client.http.request(
        V8Route("GET", f"/applications/{client.user.id}/commands")
    )


async def get_guild_commands(client, guild_id):
    return await client.http.request(
        V8Route("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands")
    )
