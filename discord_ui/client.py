from .cogs import BaseCallable, CogCommand, CogMessageCommand, CogSubCommandGroup, ListeningComponent
from .components import Component, ComponentType
from .slash.errors import NoAsyncCallback
from .errors import MissingListenedComponentParameters, WrongType
from .slash.tools import ParseMethod, cache_data, format_name, handle_options, handle_thing
from .slash.http import create_global_command, create_guild_command, delete_global_command, delete_guild_command, delete_guild_commands, edit_global_command, edit_guild_command, get_command, get_command_permissions, get_global_commands, get_guild_commands, delete_global_commands, get_id, update_command_permissions
from .slash.types import AdditionalType, CommandType, ContextCommand, MessageCommand, OptionType, SlashCommand, SlashOption, SlashSubcommand, UserCommand
from .tools import MISSING, _or, get_index, setup_logger
from .http import jsonifyMessage, BetterRoute, send_files
from .receive import Interaction, Message, PressedButton, SelectedMenu, SlashedContext, WebhookMessage, SlashedCommand, SlashedSubCommand, getMessage
from .override import override_dpy as override_it

import discord
from discord.ext import commands as com
from discord.ext.commands.errors import CommandNotFound
from discord.errors import Forbidden, InvalidArgument, NotFound

import zlib
import json
import inspect
import asyncio
import contextlib
from typing import Coroutine, Dict, List, Literal, Tuple, Union

logging = setup_logger(__name__)

class Slash():
    """
    A class for using slash commands
    
    Parameters
    ----------
        client: :class:`commands.Bot`
            The bot client

        parse_method: :class:`bool`, optional
            How received option data should be treated; Default ``ParseMethod.AUTO``

        delete_unused: :class:`bool`, optional
            Whether the commands that are not registered by this slash extension should be deleted in the api; Default ``False``

        sync_on_cog: .class:`bool`, optional
            Whether the slashcommands should be updated whenever a new cog is added; Default ``True``

        wait_sync: :class:`float`, optional
            How many seconds will be waited until the commands are going to be synchronized; Default ``1``

        auto_defer: Tuple[:class:`bool`, :class:`bool`]
            Settings for the auto-defer; Default ``(True, False)``

            ``[0]``: Whether interactions should be deferred automatically

            ``[1]``: Whether the deferration should be hidden (True) or public (False)

    Example
    ------------------
    Example for using slash commands

    .. code-block::

        ...
        # Your bot declaration and everything
        slash = Slash(client)

    For creating a slash command use

    .. code-block::

        ...
        @slash.command(name="my_command", description="this is my slash command", options=[SlashOption(str, "option", "this is an option")])
        async def command(ctx: SlashedCommand):
            ...
    
    And for subcommand groups use

    .. code-block::

        ...
        @slash.subcommand_group(base_names=["base", "group"], name="sub", description="this is a sub command group")
        async def subgroup(ctx: SlasedSubCommand):
            ...
        

    """
    def __init__(self, client, parse_method = ParseMethod.AUTO, auto_sync=True, delete_unused = False, sync_on_cog=True, wait_sync = 1, auto_defer = False) -> None:
        """Creates a new slash command thing
        
        Example
        ```py
        Slash(client)
        ```
        """
        self._buffer = bytearray()
        self._zlib = zlib.decompressobj()

        self.ready = False
        self.parse_method: int = parse_method
        self.delete_unused: bool = delete_unused
        self.wait_sync: float = wait_sync
        self.auto_defer: Tuple[bool, bool] = (auto_defer, False) if type(auto_defer) is bool else auto_defer
        self.auto_sync = auto_sync

        self._discord: com.Bot = client
        self.commands: Dict[(str, SlashCommand)] = {}
        self.subcommands: Dict[(str, Dict[(str, Union[dict, SlashSubcommand])])] = {}
        self.context_commands: Dict[str, ContextCommand] = {"message": {}, "user": {}}
        if discord.__version__.startswith("2"):
            self._discord.add_listener(self._on_response, "on_socket_raw_receive")
        elif discord.__version__.startswith("1"):
            self._discord.add_listener(self._on_response, 'on_socket_response')

        
        old_add = self._discord.add_cog
        def add_cog_override(*args, **kwargs):
            cog = args[0] if len(args) > 0 else kwargs.get("cog")
            for com in self._get_cog_commands(cog):
                com.cog = cog
                self._add_to_cache(com)
            old_add(*args, **kwargs)
            if self.ready is True and sync_on_cog is True:
                self._discord.loop.create_task(self.sync_commands(self.delete_unused))
        self._discord.add_cog = add_cog_override

        old_remove = self._discord.remove_cog
        def remove_cog_override(*args, **kwargs):
            cog = args[0] if len(args) > 0 else kwargs.get("cog")
            for com in self._get_cog_commands(cog):
                com.cog = cog
                self._remove_from_cache(com)
            old_remove(*args, **kwargs)
            if self.ready is True and sync_on_cog is True:
                self._discord.loop.create_task(self.sync_commands(self.delete_unused))
        self._discord.remove_cog = remove_cog_override
        
        async def on_connect():
            if self.auto_sync is False:
                return
            await asyncio.sleep(_or(self.wait_sync, 1))
            await self.sync_commands(self.delete_unused)
            self.ready = True
        self._discord.add_listener(on_connect)

    async def _on_response(self, msg):
        if discord.__version__.startswith("2"):
            if type(msg) is bytes:
                self._buffer.extend(msg)

                if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                    return
                msg = self._zlib.decompress(self._buffer)
                msg = msg.decode('utf-8')
                self._buffer = bytearray()
        if type(msg) is str:
            msg = json.loads(msg)

        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]

        if int(data["type"]) not in [1, 2]:
            return

        guild = None
        if data.get("guild_id") is not None:
            guild = cache_data(data["guild_id"], AdditionalType.GUILD, data, self._discord._connection)
        user = discord.Member(data=data["member"], guild=guild, state=self._discord._connection) if data.get("member") is not None else discord.User(state=self._discord._connection, data=data["user"])
        channel = await handle_thing(data["channel_id"], OptionType.CHANNEL, data, self.parse_method, self._discord)

        interaction = Interaction(self._discord._connection, data, user)
        if self.auto_defer[0] is True:
            await interaction.defer(self.auto_defer[1])
        self._discord.dispatch("interaction_received", interaction)

        #region basic commands
        if data["data"]["type"] == CommandType.SLASH and not (data["data"].get("options") and data["data"]["options"][0]["type"] in [OptionType.SUB_COMMAND, OptionType.SUB_COMMAND_GROUP]):
            x = self.commands.get(data["data"]["name"])
            if x is None:
                cog_commands = {}
                for x in self._discord.cogs:
                    cog_commands = self._get_cog_slash_commands(x)
                x = cog_commands.get(data["data"]["name"])
            if x is not None:
                options = {}
                if data["data"].get("options") is not None:
                    options = await handle_options(data, data["data"]["options"], self.parse_method, self._discord)
                context = SlashedCommand(self._discord, command=x, data=data, user=user, args=options, guild_ids=x.guild_ids, guild_permissions=x.guild_permissions)
                # Handle autodefer
                context._handle_auto_defer(self.auto_defer)
                self._discord.dispatch("slash_command", context)
                if hasattr(x, "invoke"):
                    await x.invoke(context, **options)
                elif x.callback is not None:
                    await x.callback(context, **options)
                return
        elif data["data"]["type"] == CommandType.USER:
            x = self.context_commands["user"].get(data["data"]["name"])
            if x is not None:
                member = await handle_thing(data["data"]["target_id"], OptionType.MEMBER, data, self.parse_method, self._discord)
                context = SlashedContext(self._discord, command=x, data=data, user=user, channel=channel, param=member, guild_ids=x.guild_ids, guild_permissions=x.guild_permissions)
                # Handle autodefer
                context._handle_auto_defer(self.auto_defer)

                self._discord.dispatch("context_command", context, member)
                if x.callback is not None:
                    await x.callback(context, member)
                return
        elif data["data"]["type"] == CommandType.MESSAGE:
            x = self.context_commands["message"].get(data["data"]["name"])
            if x is not None:
                message = await handle_thing(data["data"]["target_id"], 44, data, self.parse_method, self._discord)
                context = SlashedContext(self._discord, command=x, data=data, user=user, param=message, guild_ids=x.guild_ids)
                # Handle autodefer
                context._handle_auto_defer(self.auto_defer)
                
                self._discord.dispatch("context_command", context, message)
                if x.callback is not None:
                    await x.callback(context, message)
                return
        #endregion

        fixed_options = []
        x_base = self.subcommands.get(data["data"]["name"])
        if not x_base:
            cog_commands = {}
            for x in self._discord.cogs:
                cog_commands = self._get_cog_subgroup_commands(x)
            x_base = cog_commands.get(data["data"]["name"])

        if x_base:
            op = data["data"]["options"][0]
            while op["type"] != 1:
                op = op["options"][0]
            fixed_options = op.get("options", [])
            
            x = x_base.get(data["data"]["options"][0]["name"])
            if type(x) is dict:
                x = x.get(data["data"]["options"][0]["options"][0]["name"])

            options = await handle_options(data, fixed_options, self.parse_method, self._discord)

            if x:
                context = SlashedSubCommand(self._discord, x, data, user, options, x.guild_ids, x.guild_permissions)
                # Handle auto_defer
                context._handle_auto_defer(self.auto_defer)

                self._discord.dispatch("slash_command", context)
                if hasattr(x, "invoke"):
                    await x.invoke(context, **options)
                elif x.callback is not None:
                    await x.callback(context, **options)
                return
    

    def _get_cog_commands(self, cog):
        # Get all BaseCallables with __type__ of 1 (Slash)
        return [x[1] for x in inspect.getmembers(cog, lambda x: isinstance(x, BaseCallable) and x.__type__ == 1)]
        
    def _get_commands_from_cog(self, cog, cls):
        commands = {x.name: x for x in self._get_cog_commands(cog) if type(x) is cls}
        for x in commands:
            commands[x].cog = cog
        if cls is CogSubCommandGroup:
            back = commands
            commands = {}
            for _, x in list(back.items()):
                commands[x.base_names[0]] = {}
                if len(x.base_names) > 1:
                    commands[x.base_names[0]][x.base_names[1]] = {x.name: x}
                else:
                    commands[x.base_names[0]] = {x.name: x}
        return commands
    def _get_cog_slash_commands(self, name):
        """Returns all slash commands registered in the cogs"""
        return self._get_commands_from_cog(self._discord.get_cog(name), CogCommand)
    def _get_cog_subgroup_commands(self, name):
        return self._get_commands_from_cog(self._discord.get_cog(name), CogSubCommandGroup)


    async def sync_commands(self, delete_unused=False):
        """Synchronizes the slash commands with the api
        
        Parameters
        ----------
            delete_unused: :class:`bool`, optional
                Whether the unused command should be deleted from the api; default ``False``
        
        Raises
        ------
            :raises: :class:`InvalidArgument` : A slash command has an invalid guild_id
            :raises: :class:`InvalidArgument` : A slash command has an invalid id specified in the guild_permissions 
        
        """
        added_commands = {
            "globals": {},
            "guilds": {}
        }
        own_guild_ids = [x.id for x in self._discord.guilds]
        
        
        #region gather commands
        commands = self.commands
        for _base in self.subcommands:
            # get first base
            for _sub in self.subcommands[_base]:
                # get second base/command
                sub = self.subcommands[_base][_sub]
                # when command has subcommand groups
                if type(sub) is dict:
                    for _group in self.subcommands[_base][_sub]:
                        # the subcommand group
                        group = self.subcommands[_base][_sub][_group]
                        # if there's already a base command
                        if commands.get(_base) is not None:
                            # Check if base already has an option with the subs name
                            index = get_index(commands[_base].options, _sub, lambda x: getattr(x, "name"))
                            # if first base_name already exists
                            if index > -1:
                                # add to sub options
                                base_ops = commands[_base].options
                                base_ops[index].options += [group.to_option()]
                                commands[_base].options = base_ops
                            # if not exists
                            else:
                                # create sub option + group option
                                commands[_base].options += [SlashOption(OptionType.SUB_COMMAND_GROUP, _sub, options=[group.to_option()])]
                        # if no base command
                        else:
                            # create base0 command together with base1 option and groupcommand option
                            commands[_base] = SlashCommand(None, _base, MISSING, [
                                    SlashOption(OptionType.SUB_COMMAND_GROUP, _sub, options=[group.to_option()])
                                ],
                                guild_ids=group.guild_ids, default_permission=group.default_permission, guild_permissions=group.guild_permissions)
                # if is basic subcommand
                else:
                    # If base exists
                    if commands.get(_base) is not None:
                        commands[_base].options += [sub.to_option()]
                    else:
                        # create base0 command with name option
                        commands[_base] = SlashCommand(None, _base, options=[sub.to_dict()], guild_ids=sub.guild_ids, default_permission=sub.default_permission, guild_permissions=sub.guild_permissions)
        #endregion

        async def guild_stuff(command, guild_ids):
            """Adds the command to the guilds"""
            for x in guild_ids:
                if command.guild_permissions is not MISSING:
                    for x in list(command.guild_permissions.keys()):
                        if int(x) not in own_guild_ids:
                            raise InvalidArgument("guild_permissions invalid! Client is not in a guild with the id " + str(x))
                if int(x) not in own_guild_ids:
                    raise InvalidArgument("guild_ids invalid! Client is not in a server with the id '" + str(x) + "'")
            
                if added_commands["guilds"].get(x) is None:
                    added_commands["guilds"][x] = {}

                if command.guild_permissions is not MISSING:
                    command.permissions = command.guild_permissions.get(x)
                
                await self.add_guild_command(command, x)
                added_commands["guilds"][x][command.name] = command
        async def global_stuff(command):
            await self.add_global_command(command)
            added_commands["globals"][command.name] = command

        async def add_command(command):
            # guild only command
            if command.guild_ids is not MISSING:
                logging.debug("adding '" + str(command.name) + "' as guild_command")
                await guild_stuff(command, command.guild_ids)
            # global command with guild permissions
            elif command.guild_ids is MISSING and command.guild_permissions is not MISSING:
                logging.debug("adding '" + str(command.name) + "' as guild_command and global")
                await global_stuff(command)
                for guild in list(command.guild_permissions.keys()):
                    await self.update_permissions(command.name, command.type, guild_id=guild, permissions=command.guild_permissions[guild], global_command=True)
            # global command
            else:
                logging.debug("adding '" + str(command.name) + "' as global command")
                await global_stuff(command)
        
        for x in commands:
            await add_command(commands[x])

        for x in self.context_commands:
            for com in self.context_commands[x]:
                await add_command(self.context_commands[x][com])
        
        if delete_unused:
            api_coms = await self._get_global_commands()
            for apic in api_coms:
                logging.debug("deleting global command '" + str(apic["name"]) + "'")
                if added_commands["globals"].get(apic["name"]) is None:
                    await delete_global_command(self._discord, apic["id"])
            async for x in self._discord.fetch_guilds():
                _id = str(x.id)
                api_coms = await self._get_guild_commands(_id)
                for apic in api_coms:
                    if added_commands["guilds"].get(int(_id)) is not None:
                        _id = int(_id)
                    elif added_commands["guilds"].get(str(_id)) is not None:
                        _id = str(_id)
                    if added_commands["guilds"].get(_id) is None or added_commands["guilds"][_id].get(apic["name"]) is None:
                        logging.debug("deleting guild command '" + str(apic["name"]) + "' in guild " + str(_id))
                        await delete_guild_command(self._discord, apic["id"], _id)

        logging.info("synchronized slash commands")
    
    async def _get_api_command(self, name) -> Union[dict, None]:
        for x in await self._get_commands():
            if x["name"] == name:
                return x
    async def _get_guild_api_command(self, name, typ, guild_id) -> Union[dict, None]:
        for x in await self._get_guild_commands(guild_id):
            if x["name"] == name and x["type"] == typ:
                return x
    async def _get_global_api_command(self, name, typ) -> Union[dict, None]:
        for x in await self._get_global_commands():
            if x["name"] == name and x["type"] == typ:
                return x

    async def _get_commands(self) -> List[dict]:
        return await self._get_global_commands() + await self._get_all_guild_commands()
    async def _get_global_commands(self) -> List[dict]:
        return await get_global_commands(self._discord)
    async def _get_all_guild_commands(self):
        commands = []
        async for x in self._discord.fetch_guilds():
            try:
                commands += await get_guild_commands(self._discord, x.id)
            except Forbidden:
                logging.warn("Got forbidden in " + str(x.name) + " (" + str(x.id) + ")")
                continue
        return commands
    async def _get_guild_commands(self, guild_id: str) -> List[dict]:
        logging.debug("getting guild commands in " + str(guild_id))
        return await get_guild_commands(self._discord, guild_id)
    

    async def create_command(self, command):
        """Adds a command to the api. You shouldn't use this method unless you know what you're doing
        
        Parameters
        ----------
            command: :class:`SlashCommand` | :class:`ContextCommand`
                The command that should be added
        
        Raises
        ------
            :raises: :class:`InvalidArgument` : When a guild-id in ``guild_ids`` is not a valid server where the bot client is in it
            :raises: :class:`InvalidArgument` : When a guild-id in ``guild_permissions`` is not a valid server where the bot client is in it
        
        """
        if command.guild_ids is not MISSING:
            guild_ids = command.guild_ids
            own_guild_ids = [x.id for x in self._discord.guilds]
            for x in guild_ids:
                if command.guild_permissions is not MISSING:
                    for x in list(command.guild_permissions.keys()):
                        if int(x) not in own_guild_ids:
                            raise InvalidArgument("guild_permissions invalid! Client is not in a guild with the id " + str(x))
                if int(x) not in own_guild_ids:
                    raise InvalidArgument("guild_ids invalid! Client is not in a server with the id '" + str(x) + "'")

                if command.guild_permissions is not MISSING:
                    command.permissions = command.guild_permissions.get(x)
                
                await self.add_guild_command(command, x)
        else:
            await self.add_global_command(command)
    async def add_global_command(self, base):
        """Adds a slash command to the global bot commands
        
        Parameters
        ----------
            base: :class:`~SlashCommand`
                The slash command to add
        
        """
        api_command = await self._get_global_api_command(base.name, base._json["type"])
        if api_command is None:
            await create_global_command(base.to_dict(), self._discord)
        else:
            if api_command != base:
                await edit_global_command(api_command["id"], self._discord, base.to_dict())
    async def add_guild_command(self, base, guild_id):
        """Adds a slash command to a guild
        
        Parameters
        ----------
            base: :class:`~SlashCommand`
                The guild slash command which should be added
            guild_id: :class:`str`
                The ID of the guild where the command is going to be added
        
        """
        target_guild = guild_id
        api_command = await self._get_guild_api_command(base.name, base._json["type"], guild_id)
        if api_command is not None:
            api_permissions = await get_command_permissions(self._discord, api_command["id"], guild_id)
        global_command = await self._get_global_api_command(base.name, base._json["type"])
        # If no command in that guild or a global one was found
        if api_command is None or global_command is not None:
            # # Check global commands
            # If global command exists, it will be deleted
            if global_command is not None:
                await delete_global_command(self._discord, global_command["id"])
            await create_guild_command(base.to_dict(), self._discord, target_guild, base.permissions.to_dict())
        elif api_command != base:
            await edit_guild_command(api_command["id"], self._discord, target_guild, base.to_dict(), base.permissions.to_dict())
        elif api_permissions != base.permissions:
            await update_command_permissions(self._discord.user.id, self._discord.http.token, guild_id, api_command["id"], base.permissions.to_dict())

    async def update_permissions(self, name, typ: Literal["slash", 1, "user", 2, "message", 3] = 1, *, guild_id=MISSING, default_permission=MISSING,  permissions=MISSING, global_command=False):
        """Updates the permissions for a command
        
        Parameters
        ----------
            name: :class:`str`
                The name of the command that should be updated
            typ: :class:`str` | :class:`int`
                The type of the command (one of ``"slash", CommandType.SLASH, "user", CommandType.USER "message", CommandType.MESSAGE``)
            default_permission: :class:`bool`, optional
                The default permission for the command if users can use it
            guild_id: :class:`int` | :class:`str`, optional
                The ID of the guild where the permissions should be updated.
                    This needs to be passed when you use the `permissions` parameter or want to update a guild command
            permissions: :class:`SlashPermission`, optional
                The new permissions for the command
            global_command: :class:`bool`, optional
                If the command is a global command or a guild command; default ``False``
        
        """
        if guild_id is not MISSING:
            guild_id = int(guild_id)
        if type(typ) is str:
            if typ.lower() == "slash":
                typ = CommandType.SLASH
            elif typ.lower() == "user":
                typ = CommandType.USER
            elif typ.lower() == "message":
                typ = CommandType.MESSAGE
        if global_command is True:
            api_command = await self._get_global_api_command(name, typ)
        else:
            api_command = await self._get_guild_api_command(name, typ, guild_id)
        if api_command is None:
            raise CommandNotFound("Slash command with name " + str(name) + " and type " + str(typ) + " not found in the api!")
        if permissions is not MISSING:
            await update_command_permissions(self._discord.user.id, self._discord._connection.http.token, guild_id, api_command["id"], permissions.to_dict())
        if default_permission is not MISSING:
            default_permission = default_permission or False
            api_command["default_permission"] = default_permission
            if global_command is True:
                await edit_global_command(api_command["id"], self._discord, api_command)
            else:
                await edit_guild_command(api_command["id"], self._discord, guild_id, api_command)
    async def edit_command(self, old_name, typ: Literal["slash", 1, "user", 2, "message", 3] = 1, guild_id=MISSING, *, name, description, options, guild_ids, default_permission, guild_permissions, callback=MISSING):
        """Edits a command
        
        Parameters
        ----------
            old_name: :class:`str`
                The original name of the command
            typ: Literal[``'slash'``, ``1`` | ``'user'``, ``2`` | ``'message'``, ``3``], optional
                The type of the command; default ``1`` (slashcommand)
            guild_id: :class:`[type]`, optional
                The guild id of the command; default ``MISSING``
            name: :class:`str`, optional
                The new name of the command
            description: :class:`str`, optional
                The new description of the command
            options: List[:class:`~SlashOption`], optional
                The new
            guild_ids: List[:class:`int` | :class:`str`], optional
                The list of new guild_ids where the command is available
            default_permission: :class:`bool`, optional
                The new default permissions for the command
            guild_permissions: :class:`dict`, optional
                The new guild permissions for the command
            callback: :class:`function`, optional, optional
                The new command callback; default ``MISSING``
        
        Raises
        ------
            :raises: :class:`NotFound` : When a command in the internal cache doesn't exsist
            :raises: :class:`NotFound` : When a command in the api doesn't exist
        
        """
        typ = CommandType.from_string(typ)
        old_name = format_name(old_name)

        old_command = self._get_command(old_name, typ)
        if old_command is None:
            raise NotFound("Could not find a command in the internal cache with the name " + str(old_name) + " and the type " + str(typ))
        command = old_command
        if guild_id is not MISSING:
            api_command = await self._get_guild_api_command(old_name, typ, guild_id)
        else:
            api_command = await self._get_global_api_command(old_name, typ)
        if old_command is None:
            raise NotFound("Could not find a command in the api with the name " + str(old_name) + " and the type " + str(typ))

        if name is not None:
            command.name = name
        if description is not None:
            command.description = _or(description, inspect.getdoc(callback) if callback is not None else None, name, old_name)
        if options is not None:
            command.options = options
        if default_permission is not None:
            command.default_permission = default_permission
        if guild_permissions is not None:
            command.guild_permissions = guild_permissions
        if guild_ids is not MISSING:
            command.guild_ids = guild_ids
        if callback is not MISSING:
            command.callback = callback
        # When command only should be edited in one guild
        if guild_id is not MISSING and guild_ids is MISSING or old_command.guild_ids == guild_ids:
            await edit_guild_command(api_command["id"], self._discord, guild_id, command.to_dict(), command.guild_permissions.get(guild_id))
        # When guild_ids were changed
        elif guild_ids is not MISSING and guild_ids != old_command.guild_ids:
            for x in guild_ids:
                await self.add_guild_command(command, x)
        # When guild command is changed to global command
        elif guild_id is not MISSING and guild_ids is MISSING and old_command.guild_ids is not MISSING:
            for x in old_command.guild_ids:
                com = await self._get_guild_api_command(old_command.name, old_command.command_type, x)
                await delete_guild_command(self._discord, com["id"], x)
            await self.add_global_command(command)
        # When global command is changed to guild command
        elif old_command.guild_ids is MISSING and command.guild_ids is not MISSING:
            com = await self._get_global_api_command(old_command.name, old_command.command_type)
            await delete_global_command(self._discord, com["id"])
            await self.create_command(command)
        else:
            await self.create_command(command)
        self._set_command(old_name, command)
            
    def _get_command(self, name, typ: Literal["slash", 1, "user", 2, "message", 3]) -> SlashCommand:
        typ = CommandType.from_string(typ)
        if typ == CommandType.SLASH:
            return self.commands.get(name)
        elif typ == CommandType.USER:
            return self.context_commands["user"].get(name)
        else:
            return self.context_commands["message"].get(name)
    def _set_command(self, old_name, command: SlashCommand):
        if command.command_type == CommandType.SLASH:
            del self.commands[old_name]
            self.commands[command.name] = command
        elif command.command_type == CommandType.MESSAGE:
            del self.context_commands["message"][old_name]
            self.context_commands["message"][command.name] = command
        else:
            del self.context_commands["user"][old_name]
            self.context_commands["user"][command.name] = command
    def _add_to_cache(self, base: Union[SlashCommand, SlashSubcommand]):
        if base.command_type is CommandType.Slash:
            # basic slash command
            if type(base) in [SlashCommand, CogCommand]:
                self.commands[base.name] = base
            # subcommand or subgroup
            else:
                # when subcommands is missing base
                if self.subcommands.get(base.base_names[0]) is None:
                    self.subcommands[base.base_names[0]] = {}
                # subgroup
                if len(base.base_names) > 1:
                    # if cache is missing second base_name 
                    if self.subcommands[base.base_names[0]].get(base.base_names[1]) is None:
                        self.subcommands[base.base_names[0]][base.base_names[1]] = {}
                    # add to internal cache
                    self.subcommands[base.base_names[0]][base.base_names[1]][base.name] = base
                # subcommand
                else:
                    # add to cache
                    self.subcommands[base.base_names[0]][base.name] = base
        # context user command
        elif base.command_type == CommandType.User:
            self.context_commands["user"][base.name] = base
        # context message command
        elif base.command_type == CommandType.Message:
            self.context_commands["message"][base.name] = base

    async def delete_global_commands(self):
        """**Deletes all global commands**"""
        await delete_global_commands(self._discord)
    async def delete_guild_commands(self, guild_id: str):
        """
        **Deletes all commands in a guild**

        Parameters
        ----------
            guild_id: :class:`str`
                The id of the guild where all commands are going to be deleted
        
        """
        await delete_guild_commands(self._discord, guild_id)
    async def nuke_commands(self):
        """**Deletes every command for the bot, including globals and commands in every guild**"""
        logging.debug("nuking...")
        await self.delete_global_commands()
        logging.debug("nuked global commands")
        async for guild in self._discord.fetch_guilds():
            logging.debug("nuking commands in" + str(guild.id))
            await self.delete_guild_commands(guild.id)
            logging.debug("nuked commands in" + str(guild.name) + " (" + str(guild.id) + ")")
        logging.info("nuked all commands")


    def add_command(self, name, callback=None, description=MISSING, options=[], guild_ids=MISSING, default_permission=True, guild_permissions=MISSING, api=False) -> Union[None, Coroutine]:
        """Adds a new slashcommand

        name: :class:`str`
            1-32 characters long name

            .. note::

                The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
        callback: :class:`function`, optional
            A callback that will be called when the command was received
        description: :class:`str`, optional
            1-100 character description of the command; default the command name
        options: List[:class:`~SlashOptions`], optional
            The parameters for the command; default MISSING
        choices: List[:class:`dict`], optional
            Choices for string and int types for the user to pick from; default MISSING
        guild_ids: List[:class:`str` | :class:`int`], optional
            A list of guild ids where the command is available; default MISSING
        default_permission: :class:`bool`, optional
            Whether the command can be used by everyone or not
        guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
            The permissions for the command in guilds
                Format: ``{"guild_id": SlashPermission}``
        api: :class:`bool`, optional
            Whether the command should be registered to the api (True) or just added in the internal cache
                If it's added to the internal cache, it will be registered to the api when calling the `sync_commands` function.
                If ``api`` is True, this function will return a promise
        """
        command = SlashCommand(callback, name, description, options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
        self._add_to_cache(command)
        if api is True:
            if self.ready is False:
                raise Exception("Slashcommands are not ready yet")
            return self.create_command(command) 
    def command(self, name=MISSING, description=MISSING, options=[], guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """A decorator for a slash command
        
        command in discord:
            ``/name [options]``

        Parameters
        ----------
            name: :class:`str`, optional
                1-32 characters long name; default MISSING
                
                .. note::

                    The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
            
            description: :class:`str`, optional
                1-100 character description of the command; default the command name
            options: List[:class:`~SlashOptions`], optional
                The parameters for the command; default MISSING
            choices: List[:class:`dict`], optional
                Choices for string and int types for the user to pick from; default MISSING
            guild_ids: List[:class:`str` | :class:`int`], optional
                A list of guild ids where the command is available; default MISSING
            default_permission: :class:`bool`, optional
                Whether the command can be used by everyone or not
            guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
                The permissions for the command in guilds
                    Format: ``{"guild_id": SlashPermission}``

        Decorator
        ---------

            callback: :class:`method(ctx)`
                The asynchron function that will be called if the command was used
                    ctx: :class:`~SlashedCommand`
                        The used slash command

                    .. note::

                        ``ctx`` is just an example name, you can use whatever you want for that

        Example
        -------
        .. code-block::

            @slash.command(name="hello_world", description="This is a test command", 
            options=[
                SlashOption(str, name="parameter", description="this is a parameter", choices=[{ "name": "choice 1", "value": "test" }])
            ], guild_ids=["785567635802816595"], default_permission=False, 
            guild_permissions={
                    "785567635802816595": SlashPermission(allowed={"539459006847254542": SlashPermission.USER})
                }
            )
            async def command(ctx, parameter = None):
                ...
        """
        def wrapper(callback):
            """The wrapper for the callback function. The function's parameters have to have the same name as the parameters specified in the slash command.

            `ctx` is of type :class:`~SlashedCommand` and is used for responding to the interaction and more

            Examples
            --------
            - no parameter:
                `async def command(ctx): ...`
            - required parameter "number":
                `async def command(ctx, number): ...`
            - optional parameter "user":
                `async def command(ctx, user=default_value)`
            - multiple optional parameters "user", "number":
                `async def command(ctx, user=default_value, number=default_value)`
            - one required and one optional parameter "user", "text":
                `async def command(ctx, user, text=default_value)`

            Note: Replace `default_value` with a value you want to be used if the parameter is not specified in discord, if you don't want a default value, just set it to `None`
            """
            self.add_command(name, callback, description, options, guild_ids, default_permission, guild_permissions)
        return wrapper
    def subcommand(self, base_names, name=MISSING, description=MISSING, options=[], guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """A decorator for a subcommand group
        
        command in discord
            ``/base_names... name [options]``

        Parameters
        ----------
            base_names: List[:class:`str`] | :class:`str`
                The names of the parent bases, currently limited to 2
                    If you want to make a subcommand (``/base name``), you have to use a str instead of a list
            name: :class:`str`, optional
                1-32 characters long name; default MISSING
                
                .. note::

                    The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
            description: :class:`str`, optional
                1-100 character description of the command; default the command name
            options: List[:class:`~SlashOptions`], optional
                The parameters for the command; default MISSING
            choices: List[:class:`dict`], optional
                Choices for string and int types for the user to pick from; default MISSING
            guild_ids: List[:class:`str` | :class:`int`], optional
                A list of guild ids where the command is available; default MISSING
            default_permission: :class:`bool`, optional
                Whether the command can be used by everyone or not
            guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
                The permissions for the command in guilds
                    Format: ``{"guild_id": SlashPermission}``

            .. note::

                Permissions will be the same for every subcommand with the same base

        Decorator
        ---------

            callback: :class:`method(ctx)`
                The asynchron function that will be called if the command was used
                    ctx: :class:`~SlashedSubCommand`
                        The used slash command

                    .. note::

                        ``ctx`` is just an example name, you can use whatever you want for that
        
        Example
        -------
        
        subcommand

        .. code-block::

            @slash.subcommand_group(base_names="hello", name="world", options=[
                SlashOption(argument_type="user", name="user", description="the user to tell the holy words")
            ], guild_ids=["785567635802816595"])
            async def command(ctx, user):
                ...

        subcommand-group

        .. code-block::

            @slash.subcommand_group(base_names=["hello", "beautiful"], name="world", options=[
                SlashOption(argument_type="user", name="user", description="the user to tell the holy words")
            ], guild_ids=["785567635802816595"])
            async def command(ctx, user):
                ...

        """
        def wrapper(callback):
            """The wrapper for the callback function. The function's parameters have to have the same name as the parameters specified in the slash command.

            `ctx` is of type :class:`~SlashedCommand` and is used for responding to the interaction and more

            Examples
            --------
            - no parameter:
                `async def command(ctx): ...`
            - required parameter "number":
                `async def command(ctx, number): ...`
            - optional parameter "user":
                `async def command(ctx, user=default_value)`
            - multiple optional parameters "user", "number":
                `async def command(ctx, user=default_value, number=default_value)`
            - one required and one optional parameter "user", "text":
                `async def command(ctx, user, text=default_value)`

            Note: Replace `default_value` with a value you want to be used if the parameter is not specified in discord, if you don't want a default value, just set it to `None`
            """
            base = format_name(base_names[0])
            sub = None
            if len(base_names) > 1:
                sub = format_name(base_names[1])
            if self.subcommands.get(base) is None:
                self.subcommands[base] = {}
            if sub is not None and self.subcommands[base].get(sub) is None:
                self.subcommands[base][sub] = {}
            
            command = SlashSubcommand(callback, base_names, name, description, options=options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
            self._add_to_cache(command)

        return wrapper
    def user_command(self, name=MISSING, guild_ids=MISSING, default_permission=True, guild_permissions = MISSING):
        """Decorator for user context commands in discord.
            ``Right-click username`` -> ``apps`` -> ``commands is displayed here``


        Parameters
        ----------
            name: :class:`str`, optional
                The name of the command; default MISSING
            guild_ids: List[:class:`str` | :class:`int`]
                A list of guilds where the command can be used
            default_permission: :class:`bool`, optional
                Whether the command can be used by everyone; default True
            guild_permissions: Dict[:class:`SlashPermission`], optional
                Special permissions for guilds; default MISSING

        Decorator
        ---------

            callback: :class:`method(ctx, user)`
                The asynchron function that will be called if the command was used
                    ctx: :class:`~SlashedSubCommand`
                        The used slash command
                    user: :class:`discord.Member`
                        The user on which the command was used
                    
                    .. note::

                        ``ctx`` and ``user`` are just example names, you can use whatever you want for that

        Example
        -------
        
        .. code-block::

            @slash.user_command(name="call", guild_ids=["785567635802816595"], default_permission=False, guild_permissions={
                "785567635802816595": SlashPermission(allowed={
                    "585567635802816595": SlashPermission.USER
                })
            })
            async def call(ctx, message):
                ...
        """
        def wraper(callback):
            self.context_commands["user"][format_name(name)] = UserCommand(callback, name, guild_ids, default_permission, guild_permissions)
        return wraper
    def message_command(self, name=MISSING, guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """Decorator for message context commands in discord.
            ``Right-click message`` -> ``apps`` -> ``commands is displayed here``


        Parameters
        ----------
            name: :class:`str`, optional
                The name of the command; default MISSING
            guild_ids: List[:class:`str` | :class:`int`]
                A list of guilds where the command can be used
            default_permission: :class:`bool`, optional
                Whether the command can be used by everyone; default True
            guild_permissions: Dict[:class:`SlashPermission`], optional
                Special permissions for guilds; default MISSING

        Decorator
        ---------

            callback: :class:`method(ctx, message)`
                The asynchron function that will be called if the command was used
                    ctx: :class:`~SlashedSubCommand`
                        The used slash command
                    message: :class:`~Message`
                        The message on which the command was used
              
                    .. note::

                        ``ctx`` and ``message`` are just example names, you can use whatever you want for that
        
        Example
        -------
        
        .. code-block::

            @slash.message_command(name="quote", guild_ids=["785567635802816595"], default_permission=False, guild_permissions={
                "785567635802816595": SlashPermission(allowed={
                    "585567635802816595": SlashPermission.USER
                })
            })
            async def quote(ctx, message):
                ...
        """
        def wraper(callback):
            self.context_commands["message"][format_name(name)] = MessageCommand(callback, name, guild_ids, default_permission, guild_permissions)
        return wraper

class Components():
    """A class for using and receiving message components in discord
    
    Parameters
    -----------
        client: :class:`discord.Client`
            The main discord client

        override_dpy: :class:`bool`
            Whether some of discord.py'ss default methods should be overriden with this libary's; Default ``True``
                For more information see https://github.com/discord-py-ui/discord-ui/blob/main/discord_ui/override.py

        auto_defer: Tuple[:class:`bool`, :class:`bool`]
            Settings for the auto-defer; Default ``(True, False)``

            ``[0]``: Whether interactions should be deferred automatically

            ``[1]``: Whether the deferration should be hidden (True) or public (False)

    Example
    ------------------
    Example for using the listener

    
    .. code-block::

        ...
        # Your bot declaration should be here
        components = components(client)
        
    
    for listening to button presses, use
    
    .. code-block::

        ...
        @client.event("on_button_press")
        async def on_button(pressedButton):
            ...


    for listening to select menu selections, use

    .. code-block::

        ...
        @client.event("on_menu_select")
        async def on_select(seletedMenu):
            ...

    For components that will listen to a custom id, use

    .. code-block::

        ...
        @components.listening_component(custom_id="custom_id_here")
        async def my_func(ctx):
            ...

    """
    def __init__(self, client: com.Bot, override_dpy=True, auto_defer=False):
        """Creates a new compnent listener
        
        Example
        ```py
        Components(client, auto_defer=(True, False))
        ```
        """
        if override_dpy:
            override_it()

        self._buffer = bytearray()
        self._zlib = zlib.decompressobj()

        self.auto_defer: Tuple[bool, bool] = (auto_defer, False) if type(auto_defer) is bool else auto_defer
        self.listening_components: Dict[str, List[ListeningComponent]] = {}
        """A list of components that are listening for interaction"""
        self._discord: com.Bot = client
        if discord.__version__.startswith("2"):
            self._discord.add_listener(self._on_response, "on_socket_raw_receive")
        elif discord.__version__.startswith("1"):
            self._discord.add_listener(self._on_response, 'on_socket_response')

        old_add = self._discord.add_cog
        def add_cog_override(*args, **kwargs):
            cog = args[0] if len(args) > 0 else kwargs.get("cog")
            for com in self._get_listening_cogs(cog):
                com.cog = cog
                if self.listening_components.get(com.custom_id) is None:
                    self.listening_components[com.custom_id] = []
                self.listening_components[com.custom_id].append(com)
            old_add(*args, **kwargs)
        self._discord.add_cog = add_cog_override

        old_remove = self._discord.remove_cog
        def remove_cog_override(*args, **kwargs):
            cog = args[0] if len(args) > 0 else kwargs.get("cog")
            for com in self._get_listening_cogs(cog):
                com.cog = cog
                self.remove_listening_component(com)
            old_remove(*args, **kwargs)
        self._discord.remove_cog = remove_cog_override
    
    async def _on_response(self, msg):
        if discord.__version__.startswith("2"):
            if type(msg) is bytes:
                self._buffer.extend(msg)

                if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                    return
                msg = self._zlib.decompress(self._buffer)
                msg = msg.decode('utf-8')
                self._buffer = bytearray()
            if type(msg) is str:
                msg = json.loads(msg)
        
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]
        
        if data["type"] != 3:
            return
        
        guild = None
        if data.get("guild_id") is not None:
            guild = cache_data(data["guild_id"], AdditionalType.GUILD, data, self._discord._connection)
        user = discord.Member(data=data["member"], guild=guild, state=self._discord._connection) if data.get("member") is not None else discord.User(state=self._discord._connection, data=data["user"])
        msg = await getMessage(self._discord._connection, data=data, response=True)
        
        interaction = Interaction(self._discord._connection, data, user, msg)
        if self.auto_defer[0] is True:
            await interaction.defer(self.auto_defer[1])
        self._discord.dispatch("interaction_received", interaction)

        # Handle auto_defer
        if int(data["data"]["component_type"]) == 2:
            for x in msg.buttons:
                if hasattr(x, 'custom_id') and x.custom_id == data["data"]["custom_id"]:
                    component = PressedButton(data, user, x, msg, self._discord)
        elif int(data["data"]["component_type"]) == 3:
            for x in msg.select_menus:
                if x.custom_id == data["data"]["custom_id"]:
                    component = SelectedMenu(data, user, x, msg, self._discord)
        component._handle_auto_defer(self.auto_defer)

        
        # Get listening components with the same custom id
        listening_components = self.listening_components.get(data["data"]["custom_id"])
        if listening_components is not None:
            for listening_component in listening_components:
                await listening_component.invoke(component)

        if data["data"]["component_type"] == ComponentType.BUTTON:
            self._discord.dispatch("button_press", component)
        elif data["data"]["component_type"] == ComponentType.SELECT_MENU:
            self._discord.dispatch("menu_select", component)

    async def send(self, channel, content=MISSING, *, tts=False, embed=MISSING, embeds=MISSING, file=MISSING, 
            files=MISSING, delete_after=MISSING, nonce=MISSING, allowed_mentions=MISSING, reference=MISSING, 
            mention_author=MISSING, components=MISSING) -> Message:
        """Sends a message to a textchannel

        Parameters
        ----------
        channel: :class:`discord.TextChannel` | :class:`int` | :class:`str`
            The target textchannel or the id of it
        content: :class:`str`, optional
            The message text content; default None
        tts: :class:`bool`, optional
            True if this is a text-to-speech message; default False
        embed: :class:`discord.Message`, optional
            Embedded rich content (up to 6000 characters)
        embeds: List[:class:`discord.Embed`], optional
            Up to 10 embeds; default None
        file: :class:`discord.File`, optional
            A file sent as an attachment to the message; default None
        files: List[:class:`discord.File`], optional
            A list of file attachments; default None
        delete_after: :class:`float`, optional
            After how many seconds the message should be deleted; default None
        nonce: :class:`int`, optional
            The nonce to use for sending this message. If the message was successfully sent, then the message will have a nonce with this value; default None
        allowed_mentions: :class:`discord.AllowedMentions`, optional
            A list of mentions proceeded in the message; default None
        reference: :class:`discord.MessageReference` | :class:`discord.Message`, optional
            A message to refer to (reply); default None
        mention_author: :class:`bool`, optional
            True if the author should be mentioned; default None
        components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`], optional
            A list of message components included in this message; default None

        Returns
        -------
        :return: Returns the sent message
        :type: :class:`~Message`
        """

        if type(channel) not in [discord.TextChannel, int, str]:
            raise WrongType("channel", channel, "discord.TextChannel")

        channel_id = channel.id if type(channel) is discord.TextChannel else channel
        payload = jsonifyMessage(content=content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, components=components)

        route = BetterRoute("POST", f"/channels/{channel_id}/messages")

        r = None
        if file is MISSING and files is MISSING:
            r = await self._discord.http.request(route, json=payload)
        else:
            r = await send_files(route, files=_or(files, [file]), payload=payload, http=self._discord.http)

        msg = Message(state=self._discord._get_state(), channel=channel, data=r)
            
        if delete_after is not None:
            await msg.delete(delay=delete_after)
        
        return msg
    def send_webhook(self, webhook, content=MISSING, *, wait=False, username=MISSING, avatar_url=MISSING, tts=False, files=MISSING, embed=MISSING, embeds=MISSING, allowed_mentions=MISSING, components=MISSING) -> Union[WebhookMessage, None]:
        """Sends a webhook message
        
        Parameters
        ----------
            webhook: :class:`discord.Webhook`
                The webhook which will send the message
            content: :class:`str`, optional
                the message contents (up to 2000 characters); default None
            wait: :class:`bool`, optional
                if `True`, waits for server confirmation of message send before response, and returns the created message body; default False
            username: :class:`str`, optional
                override the default username of the webhook; default None
            avatar_url: :class:`str`, optional
                override the default avatar of the webhook; default None
            tts: :class:`bool`, optional
                true if this is a TTS message; default False
            files: :class:`discord.File`
                A list of files which will be sent as attachment
            embed: :class:`discord.Embed`
                Embed rich content, optional
            embeds: List[:class:`discord.Embed`], optional
                embedded rich content; default None
            allowed_mentions: :class:`discord.AllowedMentions`, optional
                allowed mentions for the message; default None
            components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`], optional
                the message components to include with the message; default None
        
        Returns
        -------
            :returns: The message sent, if wait was True, else nothing will be returned
            :type: :class:`~WebhookMessage` | :class:`None`
        
        """
        payload = jsonifyMessage(content, tts=tts, embed=embed, embeds=embeds, allowed_mentions=allowed_mentions, components=components)
        payload["wait"] = wait
        if username is not None:
            payload["username"] = username
        if avatar_url is not None:
            payload["avatar_url"] = str(avatar_url)

        return webhook._adapter.execute_webhook(payload=payload, wait=wait, files=files)
    def listening_component(self, custom_id, messages=MISSING, users=MISSING, component_type: Literal["button", "select"]=MISSING, check=lambda component: True):
        """Decorator for ``add_listening_component``

        Parameters
        ----------
            custom_id: :class:`str`
                The custom_id of the components to listen to
            messages: List[:class:`discord.Message` | :class:`int` :class:`str`], Optional
                A list of messages or message ids to filter the listening component
            users: List[:class:`discord.User` | :class:`discord.Member` | :class:`int` | :class:`str`], Optional
                A list of users or user ids to filter
            omponent_type: Literal[``'button'`` | ``'select'``]
                What type the used component has to be of (select: SelectMenu, button: Button)
            check: :class:`function`, Optional
                A function that has to return True in order to invoke the listening component
                    The check function takes to parameters, the component and the message

        Decorator
        ---------
            callback: :class:`method(ctx)`
                The asynchron function that will be called if a component with the custom_id was invoked

                There will be one parameters passed

                    ctx: :class:`~PressedButton` or :class:`~SelectedMenu`
                        The invoked component
                    
                    .. note::

                        ``ctx`` is just an example name, you can use whatever you want for it

        Example
        -------
        .. code-block::

            @ui.components.listening_component("custom_id", [539459006847254542], [53945900682362362])
            async def callback(ctx):
                ...
            
        """
        def wrapper(callback):
            self.add_listening_component(callback, custom_id, messages, users, component_type, check)
        return wrapper
    def add_listening_component(self, callback, custom_id, messages=MISSING, users=MISSING, component_type: Literal["button", 2, "select", 3]=MISSING, check=lambda component: True):
        """
        Adds a listener to received components

        Parameters
        ----------
            callback: :class:`function`
                The callback function that will be called when the component was received
            custom_id: :class:`str`
                The custom_id of the components to listen to
            messages: List[:class:`discord.Message` | :class:`int` :class:`str`], Optional
                A list of messages or message ids to filter the listening component
            users: List[:class:`discord.User` | :class:`discord.Member` | :class:`int` | :class:`str`], Optional
                A list of users or user ids to filter
            component_type: :class:`str` | :class:`int`
                The type of which the component has to be
            check: :class:`function`, Optional
                A function that has to return True in order to invoke the listening component
                    The check function takes to parameters, the component and the message

        """
        if not inspect.iscoroutinefunction(callback):
            raise NoAsyncCallback()
        if len(inspect.signature(callback).parameters) < 2:
            raise MissingListenedComponentParameters()
        
        if self.listening_components.get(custom_id) is None:
            self.listening_components[custom_id] = []
        self.listening_components[custom_id].append(ListeningComponent(callback, messages, users, check, custom_id))
    def remove_listening_components(self, custom_id):
        """Removes all listening components for a custom_id
        
        Parameters
        ----------
            custom_id: :class:`str`
                The custom_id for the listening component
        
        """
        if self.listening_components.get(custom_id) is not None:
            del self.listening_components[custom_id]
    def remove_listening_component(self, listening_component):
        """Removes a listening component
        
        Parameters
        ----------
            listening_component: :class:`ListeningComponent`
                The listening component which should be removed
        
        """
        with contextlib.supress(KeyError): 
            self.listening_components[listening_component.custom_id].remove(listening_component)

    def _get_listening_cogs(self, cog):
        return [x[1] for x in inspect.getmembers(cog, lambda x: isinstance(x, ListeningComponent))]
        

class UI():
    """The main extension for the package to use slash commands and message components
        
        Parameters
        ----------
            client: :class:`discord.ext.commands.Bot`
                The discord bot client

            override_dpy: :class:`bool`
                Whether some of discord.py'ss default methods should be overriden with this libary's; Default ``True``
                    For more information see https://github.com/discord-py-ui/discord-ui/blob/main/discord_ui/override.py

            slash_options: :class:`dict`, optional
                Settings for the slash command part; Default `{parse_method: ParseMethod.AUTO, delete_unused: False, wait_sync: 1}`
                
                ``parse_method``: :class:`int`, optional
                    How the received interaction argument data should be treated; Default ``ParseMethod.AUTO``

                ``auto_sync``: :class:`bool`, optional
                    Whether the libary should sync the slash commands automatically; Default ``True``

                ``delete_unused``: :class:`bool`, optional
                    Whether the commands that are not registered by this slash ui should be deleted in the api; Default ``False``

                ``sync_on_cog``: .class:`bool`, optional
                    Whether the slashcommands should be updated whenever a new cog is added; Default ``True``

                ``wait_sync``: :class:`float`, optional
                    How many seconds will be waited until the commands are going to be synchronized; Default ``1``

        auto_defer: Tuple[:class:`bool`, :class:`bool`]
            Settings for the auto-defer; Default ``(True, False)``

            ``[0]``: Whether interactions should be deferred automatically

            ``[1]``: Whether the deferration should be hidden (True) or public (False)
    """
    def __init__(self, client, override_dpy=True, slash_options = {"parse_method": ParseMethod.AUTO, "auto_sync": True, "delete_unused": False, "sync_on_cog": True, "wait_sync": 1}, auto_defer = False) -> None:
        """Creates a new ui object
        
        Example
        ```py
        UI(client, slash_options={"delete_unused": True, "wait_sync": 2}, auto_defer=True)
        ```
        """
        self.components = Components(client, override_dpy=override_dpy, auto_defer=auto_defer)
        """For using message components
        
        :type: :class:`~Components`
        """
        if slash_options is None:
            slash_options = {"resolve_data": True, "delete_unused": False, "wait_sync": 1, "auto_defer": auto_defer}
        if slash_options.get("auto_defer") is None:
            slash_options["auto_defer"] = auto_defer
        self.slash = Slash(client, **slash_options)
        """For using slash commands
        
        :type: :class:`~Slash`
        """