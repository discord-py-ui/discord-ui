import aiohttp
from ..tools import MISSING, get
from ..http import BetterRoute

from discord.ext import commands
from discord.errors import Forbidden, HTTPException

from requests import put

async def get_command(command_name, client: commands.Bot, guild_id=MISSING):
    return get(
        (await get_global_commands(client)) if guild_id is MISSING else (await get_guild_commands(client, guild_id)),
        command_name, lambda x: x.get("name")
    )
async def get_id(command_name, client: commands.bot, guild_id=MISSING):
    found = (await get_command(command_name, client, guild_id))
    if found is None:
        raise Exception("No slash command found with name '" + command_name + "'")
    return found.get('id')

async def delete_global_commands(client: commands.Bot):
    commands = await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/commands"))
    for x in commands:
        await delete_global_command(client, x["id"])
       
async def delete_guild_commands(client: commands.Bot, guild_id):
    try:
        commands = await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands"))
        for x in commands:
            await delete_guild_command(client, x["id"], guild_id)
    except Forbidden:
        print("got forbidden in", guild_id)

async def delete_global_command(client: commands.Bot, command_id):
    return await client.http.request(BetterRoute("DELETE", f"/applications/{client.user.id}/commands/{command_id}"))
async def delete_guild_command(client: commands.Bot, command_id, guild_id):
    return await client.http.request(BetterRoute("DELETE", f"/applications/{client.user.id}/guilds/{guild_id}/commands/{command_id}"))

async def update_command_permission(id, token, guild_id, command_id, permissions):
    async with aiohttp.ClientSession() as client:
        async with client.put(f"https://discord.com/api/v9/applications/{id}/guilds/{guild_id}/commands/{command_id}/permissions", 
            headers={"Authorization": "Bot " + token}, json={"permissions": permissions}) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise HTTPException(response, response.content)
        
async def create_global_command(command: dict, client: commands.Bot):
    return await client.http.request(BetterRoute("POST", f"/applications/{client.user.id}/commands"), json=command)
async def create_guild_command(command, client: commands.Bot, guild_id, permissions = []):
    data = await client.http.request(BetterRoute("POST", f"/applications/{client.user.id}/guilds/{guild_id}/commands"), json=command)
    return await update_command_permission(client.user.id, client.http.token, guild_id, data["id"], permissions)


async def edit_global_command(command_id: str, client: commands.Bot, new_command: dict):
    return await client.http.request(BetterRoute("PATCH", f"/applications/{client.user.id}/commands/{command_id}"), json=new_command)
async def edit_guild_command(command_id, client: commands.Bot, guild_id: str, new_command: dict, permissions: dict):
    data = await client.http.request(BetterRoute("PATCH", f"/applications/{client.user.id}/guilds/{guild_id}/commands/{command_id}"), json=new_command)
    return await update_command_permission(client.user.id, client.http.token, guild_id, data["id"], permissions)

async def get_global_commands(client):
    return await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/commands"))
async def get_guild_commands(client, guild_id):
    return await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands"))
