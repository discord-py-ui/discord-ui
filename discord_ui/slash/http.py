from .errors import NoCommandFound
from ..tools import get, setup_logger
from ..http import BetterRoute, handle_rate_limit, send_files

from discord.http import HTTPClient
from discord.state import ConnectionState
from discord import NotFound, HTTPException, Forbidden


import aiohttp

logging = setup_logger(__name__)

class SlashHTTP():
    def __init__(self, client) -> None:
        self._http: HTTPClient = client.http
        self.token: str = client._connection.http.token
        self.application_id: int = client.user.id
    async def respond_to(self, interaction_id, interaction_token, response_type, data=None, files=None):
        route = BetterRoute("POST", f'/interactions/{interaction_id}/{interaction_token}/callback')
        payload = {
            "type": getattr(response_type, "value", response_type)
        }
        if data:
            payload["data"] = data
        if files is not None:
            return await send_files(route, files, payload, self._http)
        return await self._http.request(route, json=payload)
    async def fetch_command(self, id, guild_id=None):
        try:
            if guild_id:
                return await self._http.request(BetterRoute("GET",f"/applications/{self.application_id}/guilds/{guild_id}/commands/{id}"))
            return await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/commands/{id}"))
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.fetch_command(id, guild_id)
            raise ex
    async def get_command(self, command_name, guild_id=None, type=None):
        return get(
            (
                await self.get_global_commands()
            ) if guild_id is None else (
                await self.get_guild_commands(guild_id)
            ), check=lambda x: x.get("name") == command_name and (type or x.get("type")) == x.get("type")
        )
    async def get_id(self, command_name, guild_id=None, type=None):
        found = await self.get_command(command_name, guild_id, getattr(type, "value", type))
        if found is None:
            raise NoCommandFound("No command found with name '" + command_name + "'")
        return found.get('id')

    async def delete_global_commands(self):
        commands = await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/commands"))
        for x in commands:
            await self.delete_global_command(x["id"])
    async def delete_guild_commands(self, guild_id):
        try:
            commands = await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/guilds/{guild_id}/commands"))
            for x in commands:
                await self.delete_guild_command( x["id"], guild_id)
        except Forbidden:
            logging.warn("got forbidden in " + str(guild_id))

    async def delete_global_command(self, command_id):
        try:
            return await self._http.request(BetterRoute("DELETE", f"/applications/{self.application_id}/commands/{command_id}"))
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.delete_global_command(command_id)
            raise ex
    async def delete_guild_command(self, command_id, guild_id):
        try:
            return await self._http.request(BetterRoute("DELETE", f"/applications/{self.application_id}/guilds/{guild_id}/commands/{command_id}"))
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.delete_guild_command(command_id, guild_id)
            raise ex

    async def get_command_permissions(self, command_id, guild_id):
        try:
            return await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/guilds/{guild_id}/commands/{command_id}/permissions"))
        except NotFound:
            return {"id": command_id, "application_id": self.application_id, "permissions": []}
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.get_command_permissions(command_id, guild_id)
            else:
                raise ex
    async def update_command_permissions(self, guild_id, command_id, permissions):
        async with aiohttp.ClientSession() as client:
            async with client.put(f"https://discord.com/api/v9/applications/{self.application_id}/guilds/{guild_id}/commands/{command_id}/permissions",
                headers={"Authorization": "Bot " + self.token}, json={"permissions": permissions}) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    data = await handle_rate_limit(await response.json())
                    await self.update_command_permissions(guild_id, command_id, permissions)
                    return data
                raise HTTPException(response, response.content)

    async def create_global_command(self, command: dict):
        try:
            return await self._http.request(BetterRoute("POST", f"/applications/{self.application_id}/commands"), json=command)
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.create_global_command(command)
            raise ex
    async def create_guild_command(self, command, guild_id, permissions = []):
        try:
            data = await self._http.request(BetterRoute("POST", f"/applications/{self.application_id}/guilds/{guild_id}/commands"), json=command)
            await self.update_command_permissions(guild_id, data["id"], permissions)
            return data
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.create_guild_command(command, guild_id, permissions)
            raise ex


    async def edit_global_command(self, command_id: str, new_command: dict):
        try:
            return await self._http.request(BetterRoute("PATCH", f"/applications/{self.application_id}/commands/{command_id}"), json=new_command)
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.edit_global_command(command_id, new_command)
            raise ex
    async def edit_guild_command(self, command_id, guild_id: str, new_command: dict, permissions: dict=None):
        try:
            data = await self._http.request(BetterRoute("PATCH", f"/applications/{self.application_id}/guilds/{guild_id}/commands/{command_id}"), json=new_command)
            if permissions is not None:
                return await self.update_command_permissions(guild_id, data["id"], permissions)
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.edit_guild_command(command_id, guild_id, new_command, permissions)
            raise ex

    async def get_global_commands(self):
        try:
            return await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/commands"))
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.get_global_commands()
            raise ex
    async def get_guild_commands(self, guild_id):
        try:
            return await self._http.request(BetterRoute("GET", f"/applications/{self.application_id}/guilds/{guild_id}/commands"))
        except HTTPException as ex:
            if ex.status == 429:
                await handle_rate_limit(await ex.response.json())
                return await self.get_guild_commands(guild_id)
            if ex.status == 403:
                logging.warning("got forbidden in " + str(guild_id))
                return []
            raise ex

# just for typing
class ModifiedSlashState(ConnectionState):
    slash_http: SlashHTTP = None
    http: HTTPClient
