from ..tools import MISSING, get, setup_logger
from ..http import BetterRoute, handle_rate_limit

from discord.ext import commands as com
from discord.errors import Forbidden, HTTPException, NotFound

import aiohttp

logging = setup_logger(__name__)

async def get_command(command_name, client: com.Bot, guild_id=None):
    return get(
        (
            await get_global_commands(client)
        ) if guild_id is None else (
            await get_guild_commands(client, guild_id)
        ),
        command_name, lambda x: x.get("name")
    )
async def get_id(command_name, client: com.bot, guild_id=None):
    found = (await get_command(command_name, client, guild_id))
    if found is None:
        raise Exception("No slash command found with name '" + command_name + "'")
    return found.get('id')

async def delete_global_commands(client: com.Bot):
    commands = await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/commands"))
    for x in commands:
        await delete_global_command(client, x["id"])
async def delete_guild_commands(client: com.Bot, guild_id):
    try:
        commands = await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands"))
        for x in commands:
            await delete_guild_command(client, x["id"], guild_id)
    except Forbidden:
        logging.warn("got forbidden in " + str(guild_id))

async def delete_global_command(client: com.Bot, command_id):
    try:
        return await client.http.request(BetterRoute("DELETE", f"/applications/{client.user.id}/commands/{command_id}"))
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await delete_global_command(client, command_id)
        raise ex
async def delete_guild_command(client: com.Bot, command_id, guild_id):
    try:
        return await client.http.request(BetterRoute("DELETE", f"/applications/{client.user.id}/guilds/{guild_id}/commands/{command_id}"))
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await delete_guild_command(client, command_id, guild_id)
        else:
            raise ex
    except Exception as ex:
        raise ex

async def get_command_permissions(client: com.Bot, command_id, guild_id):
    try:
        return await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands/{command_id}/permissions"))
    except NotFound:
        return {"id": command_id, "application_id": client.user.id, "permissions": []}
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await get_command_permissions(client, command_id, guild_id)
        else:
            raise ex
async def update_command_permissions(application_id, token, guild_id, command_id, permissions):
    async with aiohttp.ClientSession() as client:
        async with client.put(f"https://discord.com/api/v9/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions", 
            headers={"Authorization": "Bot " + token}, json={"permissions": permissions}) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 429:
                await handle_rate_limit(await response.json())
                return await update_command_permissions(application_id, token, guild_id, command_id, permissions)
            raise HTTPException(response, response.content)

async def create_global_command(command: dict, client: com.Bot):
    try:
        return await client.http.request(BetterRoute("POST", f"/applications/{client.user.id}/commands"), json=command)
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await create_global_command(command, client)
        raise ex
async def create_guild_command(command, client: com.Bot, guild_id, permissions = []):
    try:
        data = await client.http.request(BetterRoute("POST", f"/applications/{client.user.id}/guilds/{guild_id}/commands"), json=command)
        return await update_command_permissions(client.user.id, client.http.token, guild_id, data["id"], permissions)
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await create_guild_command(command, client, guild_id, permissions)
        raise ex


async def edit_global_command(command_id: str, client: com.Bot, new_command: dict):
    try:
        return await client.http.request(BetterRoute("PATCH", f"/applications/{client.user.id}/commands/{command_id}"), json=new_command)
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await edit_global_command(command_id, client, new_command)
        raise ex
async def edit_guild_command(command_id, client: com.Bot, guild_id: str, new_command: dict, permissions: dict=None):
    try:
        data = await client.http.request(BetterRoute("PATCH", f"/applications/{client.user.id}/guilds/{guild_id}/commands/{command_id}"), json=new_command)
        if permissions is not None:
            return await update_command_permissions(client.user.id, client.http.token, guild_id, data["id"], permissions)
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await edit_guild_command(command_id, client, guild_id, new_command, permissions)
        raise ex

async def get_global_commands(client):
    try:
        return await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/commands"))
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await get_global_commands(client)
        raise ex
async def get_guild_commands(client, guild_id):
    try:
        return await client.http.request(BetterRoute("GET", f"/applications/{client.user.id}/guilds/{guild_id}/commands"))
    except HTTPException as ex:
        if ex.status == 429:
            await handle_rate_limit(await ex.response.json())
            return await get_guild_commands(client, guild_id)
        if ex.status == 403:
            logging.warning("got forbidden in " + str(guild_id))
            return []
        raise ex
