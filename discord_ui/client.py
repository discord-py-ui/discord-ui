from .slash.errors import NoAsyncCallback
from .errors import MissingListenedComponentParameters, WrongType
from .slash.tools import ParseMethod, cache_data, format_name, handle_options, handle_thing
from .slash.http import create_global_command, create_guild_command, delete_global_command, delete_guild_command, delete_guild_commands, edit_global_command, edit_guild_command, get_command, get_command_permissions, get_global_commands, get_guild_commands, delete_global_commands, get_id, update_command_permissions
from .slash.types import AdditionalType, ContextCommand, MessageCommand, OptionType, SlashCommand, SlashOption, SubSlashCommand, SubSlashCommandGroup, UserCommand
from .tools import MISSING, _or, get_index, setup_logger
from .http import jsonifyMessage, BetterRoute, send_files
from .receive import Interaction, Message, SlashedContext, WebhookMessage, SlashedCommand, SlashedSubCommand, getResponseMessage

import discord
from discord.ext import commands as com
from discord.errors import Forbidden, InvalidArgument

import zlib
import json
import inspect
import asyncio
from typing import Dict, List, Tuple, Union

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
    
    For subcommands use

    .. code-block::

        ...
        @slash.subcommand(base_name="base", name="sub", description="this is a sub command")
        async def subcommand(ctx: SlashedSubCommand):
            ...

    And for subcommand groups use

    .. code-block::

        ...
        @slash.subcommand_group(base_names=["base", "group"], name="sub", description="this is a sub command group")
        async def subcommand(ctx: SlasedSubCommand):
            ...
        

    """
    def __init__(self, client, parse_method = ParseMethod.AUTO, delete_unused = False, wait_sync = 1, auto_defer = True) -> None:
        """Creates a new slash command thing
        
        Example
        ```py
        Slash(client)
        ```
        """
        self._buffer = bytearray()
        self._zlib = zlib.decompressobj()

        self.parse_method: int = parse_method
        self.delete_unused: bool = delete_unused
        self.wait_sync: float = wait_sync
        self.auto_defer: Tuple[bool, bool] = auto_defer if type(auto_defer) in [list, tuple] else (auto_defer, False)

        self._discord: com.Bot = client
        self.commands: Dict[(str, SlashCommand)] = {}
        self.subcommands: Dict[(str, Dict[(str, SubSlashCommand)])] = {}
        self.context_commands: Dict[str, ContextCommand] = {"message": {}, "user": {}}
        if discord.__version__.startswith("2"):
            self._discord.add_listener(self._on_response, "on_socket_raw_receive")
        elif discord.__version__.startswith("1"):
            self._discord.add_listener(self._on_response, 'on_socket_response')

        self.ready = False
        async def client_ready():
            await asyncio.sleep(_or(self.wait_sync, 1))
            self._discord.loop.create_task(self.add_commands())
            self.ready = True
        self._discord.add_listener(client_ready, "on_ready")

    async def _on_response(self, msg):
        if discord.__version__.startswith("2"):
            if type(msg) is bytes:
                self._buffer.extend(msg)

                if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                    return
                msg = self._zlib.decompress(self._buffer)
                msg = msg.decode('utf-8')
                self._buffer = bytearray()
                msg = json.loads(msg)
        
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]

        if int(data["type"]) not in [1, 2]:
            return

        guild = cache_data(data["guild_id"], AdditionalType.GUILD, data, self._discord._connection)
        user = discord.Member(data=data["member"], guild=guild, state=self._discord._connection)
        channel = await handle_thing(data["channel_id"], OptionType.CHANNEL, data, self.parse_method, self._discord)

        interaction = Interaction(self._discord._connection, data, user)
        if self.auto_defer[0] is True:
            await interaction.defer(self.auto_defer[1])
        self._discord.dispatch("interaction_received", interaction)

        #region basic commands
        if data["data"]["type"] == 1 and not (data["data"].get("options") and data["data"]["options"][0]["type"] in [OptionType.SUB_COMMAND, OptionType.SUB_COMMAND_GROUP]):
            x = self.commands.get(data["data"]["name"])
            if x is not None:
                options = {}
                if data["data"].get("options") is not None:
                    options = await handle_options(data, data["data"]["options"], self.parse_method, self._discord)
                context = SlashedCommand(self._discord, command=x, data=data, user=user, channel=channel, guild_ids=x.guild_ids)
                # Handle autodefer
                context._handle_auto_defer(self.auto_defer)

                await x.callback(context, **options)
                return
        elif data["data"]["type"] == 2:
            x = self.context_commands["user"].get(data["data"]["name"])
            if x is not None:
                member = await handle_thing(data["data"]["target_id"], OptionType.MEMBER, data, self.parse_method, self._discord)
                await x.callback(SlashedContext(self._discord, command=x, data=data, user=user, channel=channel, guild_ids=x.guild_ids), member)
                return
        elif data["data"]["type"] == 3:
            x = self.context_commands["message"].get(data["data"]["name"])
            if x is not None:
                message = await handle_thing(data["data"]["target_id"], 44, data, self.parse_method, self._discord)
                context = SlashedContext(self._discord, command=x, data=data, user=user, channel=channel, guild_ids=x.guild_ids)
                # Handle autodefer
                context._handle_auto_defer(self.auto_defer)

                await x.callback(context, message)
                return
        #endregion

        fixed_options = []
        x_base = self.subcommands.get(data["data"]["name"])
        if x_base:
            op = data["data"]["options"][0]
            while op["type"] != 1:
                op = op["options"][0]
            fixed_options = op.get("options", [])
            
            x = x_base.get(data["data"]["options"][0]["name"])
            if type(x) is dict:
                x = x.get(data["data"]["options"][0]["options"][0]["name"])

            if x is None:
                x = x_base.get(op["name"])
            options = await handle_options(data, fixed_options, self.parse_method, self._discord)

            if x:
                context = SlashedSubCommand(self._discord, x, data, user, channel, x.guild_ids)
                if self.auto_defer[0] is True:
                    await context.defer(self.auto_defer[1])
                await x.callback(context, **options)
                return

    async def add_commands(self):
        added_commands = {
            "globals": {},
            "guilds": {}
        }
        own_guild_ids = [str(x.id) for x in self._discord.guilds]
        
        #region gather commands
        commands = self.commands
        for x in self.subcommands:
            for y in self.subcommands[x]:
                sub = self.subcommands[x][y]
                if type(sub) is dict:
                    for z in self.subcommands[x][y]:
                        group = self.subcommands[x][y][z]
                        if commands.get(group.base_names[0]) is not None:
                            index = get_index(commands[group.base_names[0]].options, group.base_names[1], lambda x: getattr(x, "name"))
                            if index > -1:
                                _ops = commands[group.base_names[0]].options[index].options
                                _ops.append(group.to_option())
                                commands[group.base_names[0]].options[index].options = _ops
                            else:
                                _ops = commands[group.base_names[0]].options
                                _ops.append(SlashOption(OptionType.SUB_COMMAND_GROUP, group.base_names[1], options=[group.to_option()]))
                                commands[group.base_names[0]].options = _ops
                        else:
                            commands[group.base_name] = SlashCommand(None, group.base_names[0], MISSING, [
                                    SlashOption(OptionType.SUB_COMMAND_GROUP, group.base_names[1], options=[group.to_option()])
                                ],
                                guild_ids=group.guild_ids, default_permission=group.default_permission, guild_permissions=group.guild_permission)
                else:
                    if commands.get(sub.base_name) is not None:
                        _ops = commands[sub.base_name].options
                        _ops.append(sub.to_option())
                        commands[sub.base_name].options = _ops
                    else:
                        commands[sub.base_name] = SlashCommand(None, sub.base_name, options=[sub.to_dict()], guild_ids=sub.guild_ids, default_permission=sub.default_permission, guild_permissions=sub.guild_permissions)
        #endregion

        async def guild_stuff(command, guild_ids):
            """Adds the command to the guilds"""
            for x in guild_ids:
                if str(x) not in own_guild_ids:
                    raise InvalidArgument("client is not in a server with the id '" + str(x) + "'")
            
                if added_commands["guilds"].get(x) is None:
                    added_commands["guilds"][x] = {}

                if command.guild_permissions is not MISSING:
                    command.permissions = command.guild_permissions.get(x)
                
                await self.add_guild_command(command, x)
                added_commands["guilds"][x][command.name] = command
        async def global_stuff(command):
            await self.add_global_command(command)
            added_commands["globals"][command.name] = command

        for x in commands:
            command = commands[x]
            # guild only command
            if command.guild_ids is not MISSING:
                logging.debug("adding '" + str(command.name) + "' as guild_command")
                await guild_stuff(command, command.guild_ids)
            # global command with guild permissions
            elif command.guild_ids is MISSING and command.guild_permissions is not MISSING:
                logging.debug("adding '" + str(command.name) + "' as guild_command and global")
                await guild_stuff(command, list(command.guild_permissions.keys()))
            # global command
            else:
                logging.debug("adding '" + str(command.name) + "' as global command")
                await global_stuff(command)

        if self.delete_unused:
            api_coms = await self._get_global_commands()
            for apic in api_coms:
                logging.debug("deleting global command '" + str(apic["name"]) + "'")
                if added_commands["globals"].get(apic["name"]) is None:
                    await delete_global_command(self._discord, apic["id"])
            async for x in self._discord.fetch_guilds():
                _id = str(x.id)
                api_coms = await self._get_guild_commands(_id)
                for apic in api_coms:
                    if None in [added_commands["guilds"].get(_id), added_commands["guilds"][_id].get(apic["name"])]:
                        logging.debug("deleting guild command '" + str(apic["name"]) + "' in guild " + str(_id))
                        await delete_guild_command(self._discord, apic["id"], _id)

        logging.info("synchronized slash commands")
    
    async def _get_api_command(self, name) -> Union[dict, None]:
        for x in await self._get_commands():
            if x["name"] == name:
                return x
    async def _get_guild_api_command(self, name, guild_id) -> Union[dict, None]:
        for x in await self._get_guild_commands(guild_id):
            if x["name"] == name:
                return x
    async def _get_global_api_command(self, name) -> Union[dict, None]:
        for x in await self._get_global_commands():
            if x["name"] == name:
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
    
    async def add_global_command(self, base):
        """Adds a slash command to the global bot commands
        
        Parameters
        ----------
            base: :class:`~SlashCommand`
                The slash command to add
        
        """
        api_command = await self._get_global_api_command(base.name)
        if api_command is None:
            await create_global_command(base.to_dict(), self._discord)
        else:
            if api_command != base:
                if api_command.get("guild_id") is None:
                    await edit_global_command(api_command["id"], self._discord, base.to_dict())
                else:
                    await delete_guild_command(self._discord, api_command["id"], api_command["guild_id"])
                    await self.add_global_command(base)
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
        api_command = await self._get_guild_api_command(base.name, guild_id)
        if api_command is not None:
            api_permissions = await get_command_permissions(self._discord, api_command["id"], guild_id)
        # If no command in that guild
        if api_command is None:
            # Check global commands
            api_command = await self._get_global_api_command(base.name)
            # If global command exists, it will be deleted
            if api_command is not None:
                await delete_global_command(self._discord, api_command["id"])
            await create_guild_command(base.to_dict(), self._discord, target_guild, base.permissions.to_dict())
        elif api_command != base or api_permissions != base.permissions:
            if api_command != base:
                await edit_guild_command(api_command["id"], self._discord, target_guild, base.to_dict(), base.permissions.to_dict())
            elif api_permissions != base.permissions:
                await update_command_permissions(self._discord.user.id, self._discord.http.token, guild_id, api_command["id"], base.permissions.to_dict())
        else:
            await update_command_permissions(self._discord.user.id, self._discord.http.token, guild_id, api_command["id"], base.permissions.to_dict())
        # else:

    async def make_sub_command(self, base: SlashCommand, guild_id=MISSING):
        """Creates a new sub command and edits it if the base already exsits

        Parameters
        ----------
            base: :class:`~SlashCommand`
                The slash command with the sub commands in it
            guild_id: :class:`str` | :class:`int`
                The guild id where the command should be useable
        
        """
        if guild_id is not MISSING:
            await self.add_guild_command(base, guild_id)
        else:
            await self.add_global_command(base)
            

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


    def command(self, name, description=MISSING, options=MISSING, guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """A decorator for a slash command
        
        command in discord:
            ``/name [options]``

        Parameters
        ----------
            name: :class:`str`
                1-32 characters long name
                
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
            self.commands[format_name(name)] = SlashCommand(callback, name, description, options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
        return wrapper
    def subcommand(self, base_name, name, description=MISSING, options=MISSING, guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """A decotator for a subcommand
        
        command in discord
            ``/base_name name [options]``

        Parameters
        ----------
            base_names: List[:class:`str`]
                The names of the parent base
            name: :class:`str`
                1-32 characters long name
                .. note::

                    The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
            description: :class:`str`, optional
                1-100 character description of the command; default the command name
            options: List[:class:`~SlashOptions`], optional
                The parameters for the command; default MISSING
            guild_ids: List[:class:`str` | :class:`int`], optional
                A list of guild ids where the command is available; default MISSING
            default_permissions: :class:`bool`, optional
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
        .. code-block::

            @slash.subcommand(base_name="hello", name="world", options=[
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
            if self.subcommands.get(format_name(base_name)) is None:
                self.subcommands[format_name(base_name)] = {}

            self.subcommands[format_name(base_name)][format_name(name)] = SubSlashCommand(callback, base_name, name, description, options=options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
        return wrapper
    def subcommand_group(self, base_names, name, description=MISSING, options=MISSING, guild_ids=MISSING, default_permission=True, guild_permissions=MISSING):
        """A decorator for a subcommand group
        
        command in discord
            ``/base_names... name [options]``

        Parameters
        ----------
            base_names: List[:class:`str`]
                The names of the parent bases, currently limited to 2
            name: :class:`str`
                1-32 characters long name
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
            sub = format_name(base_names[1])
            if self.subcommands.get(base) is None:
                self.subcommands[base] = {}
            if self.subcommands[base].get(sub) is None:
                self.subcommands[base][sub] = {}

            self.subcommands[format_name(base_names[0])][format_name(base_names[1])][format_name(name)] = SubSlashCommandGroup(callback, base_names, name, description, options=options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)

        return wrapper
    def user_command(self, name, guild_ids, default_permission=True, guild_permissions = MISSING):
        """Decorator for user context commands in discord.
            ``Right-click username`` -> ``apps`` -> ``commands is displayed here``


        Parameters
        ----------
            name: :class:`str`
                The name of the command
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
    def message_command(self, name, guild_ids, default_permission=True, guild_permissions = MISSING):
        """Decorator for message context commands in discord.
            ``Right-click message`` -> ``apps`` -> ``commands is displayed here``


        Parameters
        ----------
            name: :class:`str`
                The name of the command
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
        async def on_button(pressedButton, message):
            ...

    for listening to select menu selections, use
    

    .. code-block::

        ...
        @client.event("on_menu_select")
        async def on_select(seletedMenu, message):
            ...
        
    For components that will listen to a custom id, use

    .. code-block::

        ...
        @components.listening_component(custom_id="custom_id_here")
        async def my_func(component, msg):
            ...
    """
    def __init__(self, client: com.Bot, auto_defer=(True, False)):
        """Creates a new compnent listener
        
        Example
        ```py
        Components(client)
        ```
        """
        self._buffer = bytearray()
        self._zlib = zlib.decompressobj()

        self.auto_defer: Tuple[bool, bool] = auto_defer if type(auto_defer) in [list, tuple] else (auto_defer, False)
        self._listening_components: Dict[str, List[function]] = {}
        """A list of components that are listening for interaction"""
        self._discord: com.Bot = client
        if discord.__version__.startswith("2"):
            self._discord.add_listener(self._on_response, "on_socket_raw_receive")
        elif discord.__version.startswith("1"):
            self._discord.add_listener(self._on_response, 'on_socket_response')
    
    async def _on_response(self, msg):
        if discord.__version__.startswith("2"):
            if type(msg) is bytes:
                self._buffer.extend(msg)

                if len(msg) < 4 or msg[-4:] != b'\x00\x00\xff\xff':
                    return
                msg = self._zlib.decompress(self._buffer)
                msg = msg.decode('utf-8')
                self._buffer = bytearray()
                msg = json.loads(msg)
        
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]
        
        if data["type"] != 3:
            return
        
        guild = cache_data(data["guild_id"], AdditionalType.GUILD, data, self._discord._connection)
        user = discord.Member(data=data["member"], guild=guild, state=self._discord._connection)
        msg = await getResponseMessage(self._discord._connection, data=data, user=user, response=True)
        
        interaction = Interaction(self._discord._connection, data, user, msg)
        if self.auto_defer[0] is True:
            await interaction.defer(self.auto_defer[1])
        self._discord.dispatch("interaction_received", interaction)

        # Handle auto_defer
        msg.interaction_component._handle_auto_defer(self.auto_defer)
        component = msg.interaction_component

        
        # Get listening components with the same custom id
        listening_components = self._listening_components.get(data["data"]["custom_id"])
        if listening_components is not None:
            for listening_component in listening_components:
                await listening_component(component, msg)


        if data["data"]["component_type"] == 2:
            self._discord.dispatch("button_press", component, msg)
        elif data["data"]["component_type"] == 3:
            self._discord.dispatch("menu_select", component, msg)

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
    def listening_component(self, custom_id):
        """A decorator for a listening component, that will be always executed if the invoked interaction has the custom_id passed

        .. Warning::

            The button_press event will not be dispatched when using ``listening_component``, so make sure you don't use that custom_id here for any of your normal components
        
        Parameters
        ----------
            custom_id: :class:`str`
                The custom_id of the components to listen to

        Decorator
        ---------
            callback: :class:`method(component, message)`
                The asynchron function that will be called if a component with the custom_id was invoked

                There will be two parameters passed

                    component: :class:`~PressedButton` or :class:`~SelectedMenu`
                        The invoked component
                    message: :class:`~ResponseMessage`
                        The message in which the component was invoked

                    .. note::

                        ``component`` and ``message`` are just example names, you can use whatever you want for them

        Example
        -------
        @ui.components.listening_component("custom_id")
        async def callback(component, message):
            ...
        """
        def wrapper(callback):
            if not inspect.iscoroutinefunction(callback):
                raise NoAsyncCallback()
            if len(inspect.signature(callback).parameters) < 2:
                raise MissingListenedComponentParameters()
            
            if self._listening_components.get(custom_id) is None:
                self._listening_components[custom_id] = []
            self._listening_components[custom_id].append(callback)
        return wrapper
    

class UI():
    """The main extension for the package to use slash commands and message components
        
        Parameters
        ----------
            client: :class:`discord.ext.commands.Bot`
                The discord bot client

            slash_options: :class:`dict`, optional
                Settings for the slash command part; Default `{parse_method: ParseMethod.AUTO, delete_unused: False, wait_sync: 1}`
                
                ``parse_method``: :class:`int`, optional
                    How the received interaction argument data should be treated; Default ``ParseMethod.AUTO``

                ``delete_unused``: :class:`bool`, optional
                    Whether the commands that are not registered by this slash ui should be deleted in the api; Default ``False``
        
                ``wait_sync``: :class:`float`, optional
                    How many seconds will be waited until the commands are going to be synchronized; Default ``1``

        auto_defer: Tuple[:class:`bool`, :class:`bool`]
            Settings for the auto-defer; Default ``(True, False)``

            ``[0]``: Whether interactions should be deferred automatically

            ``[1]``: Whether the deferration should be hidden (True) or public (False)



    """
    def __init__(self, client, slash_options = {"parse_method": ParseMethod.AUTO, "delete_unused": False, "wait_sync": 1, "auto_defer": (True, False)}, auto_defer: Tuple[bool, bool] = (True, False)) -> None:
        """Creates a new ui object
        
        Example
        ```py
        UI(client, slash_options={"delete_unused": True, "wait_sync": 2})
        ```
        """
        self.components = Components(client, auto_defer=auto_defer)
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