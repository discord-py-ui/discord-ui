from .slash.tools import ParseMethod, handle_options, handle_thing, resolve
from .slash.http import (
    create_global_command,
    create_guild_command,
    delete_global_command,
    delete_guild_command,
    delete_guild_commands,
    edit_global_command,
    edit_guild_command,
    get_command,
    get_global_commands,
    get_guild_commands,
    delete_global_commands,
    get_id,
)
from .slash.types import (
    MessageCommand,
    OptionType,
    SlashCommand,
    SlashOption,
    SlashPermission,
    SubSlashCommand,
    SubSlashCommandGroup,
    UserCommand,
)
from .tools import MISSING, get, get_index
from .http import jsonifyMessage, BetterRoute, send_files
from .receive import (
    EphemeralComponent,
    Message,
    SlashedContext,
    WebhookMessage,
    SlashedCommand,
    SlashedSubCommand,
    getResponseMessage,
)

import discord
from discord.errors import Forbidden, InvalidArgument
from discord.ext import commands as com

import asyncio
from typing import Dict, List, Tuple, Union


class Slash:
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

    def __init__(
        self, client, parse_method=ParseMethod.AUTO, delete_unused=False, wait_sync=1
    ) -> None:
        """Creates a new slash command thing

        Example
        ```py
        Slash(client)
        ```
        """
        self.parse_method: int = parse_method
        self.delete_unused: bool = delete_unused
        self.wait_sync: float = wait_sync

        self._discord: com.Bot = client
        self.commands: Dict[(str, SlashCommand)] = {}
        self.subcommands: Dict[(str, Dict[(str, SubSlashCommand)])] = {}
        self.subcommand_groups: Dict[(str, Dict[(str, SubSlashCommandGroup)])] = {}
        self.context_commands = {"message": {}, "user": {}}
        self._discord.add_listener(self._on_socket_response, "on_socket_response")

        self.ready = False

        async def client_ready():
            await asyncio.sleep(self.wait_sync or 1)
            self._discord.loop.create_task(self.add_commands())
            self.ready = True

        self._discord.add_listener(client_ready, "on_ready")

    async def _on_socket_response(self, msg):
        """Will be executed if the bot receives a socket response"""
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]

        if int(data["type"]) not in [1, 2]:
            return

        guild = await self._discord.fetch_guild(data["guild_id"])
        user = discord.Member(
            data=data["member"], guild=guild, state=self._discord._connection
        )
        channel = await self._discord.fetch_channel(data["channel_id"])

        if data["data"]["type"] == 1:
            x = self.commands.get(data["data"]["name"])
            if x:
                options = {}
                if data["data"].get("options") is not None:
                    options = await handle_options(
                        data, data["data"]["options"], self.parse_method, self._discord
                    )
                await x.callback(
                    SlashedCommand(
                        self._discord,
                        command=x,
                        data=data,
                        user=user,
                        channel=channel,
                        guild_ids=x.guild_ids,
                    ),
                    **options,
                )
                return
        elif data["data"]["type"] == 2:
            x = self.context_commands["user"].get(data["data"]["name"])
            if x:
                member = await handle_thing(
                    data["data"]["target_id"],
                    OptionType.MEMBER,
                    data,
                    self.parse_method,
                    self._discord,
                )
                await x.callback(
                    SlashedContext(
                        self._discord,
                        command=x,
                        data=data,
                        user=user,
                        channel=channel,
                        guild_ids=x.guild_ids,
                    ),
                    member,
                )
        elif data["data"]["type"] == 3:
            x = self.context_commands["message"].get(data["data"]["name"])
            if x:
                message = await handle_thing(
                    data["data"]["target_id"],
                    44,
                    data,
                    self.parse_method,
                    self._discord,
                )
                await x.callback(
                    SlashedContext(
                        self._discord,
                        command=x,
                        data=data,
                        user=user,
                        channel=channel,
                        guild_ids=x.guild_ids,
                    ),
                    message,
                )

        fixed_options = []
        x_base = self.subcommands.get(
            data["data"]["name"]
        ) or self.subcommand_groups.get(data["data"]["name"])
        if x_base:
            x = x_base.get(data["data"]["options"][0]["name"])

            op = data["data"]["options"][0]
            while op["type"] != 1:
                op = op["options"][0]
            fixed_options = op.get("options", [])

            if x is None:
                x = x_base.get(op["name"])

            options = await handle_options(
                data, fixed_options, self.self.parse_method, self._discord
            )
            if x:
                await x.callback(
                    SlashedSubCommand(
                        self._discord, x, data, user, channel, x.guild_ids
                    ),
                    **options,
                )
                return

    async def add_commands(self):
        commands = {"globals": {}, "guilds": {}}
        own_guild_ids = [str(x.id) for x in self._discord.guilds]

        # region contgext commands
        for command in list(self.context_commands["message"].values()) + list(
            self.context_commands["user"].values()
        ):
            if command.guild_ids is not MISSING:
                for x in command.guild_ids or command.guild_permissions.keys():
                    if str(x) not in own_guild_ids:
                        raise InvalidArgument(
                            "Client is not in a server with the id '" + str(x) + "'"
                        )

                    if commands["guilds"].get(x) is None:
                        commands["guilds"][x] = {}

                    if command.guild_permissions is not MISSING:
                        command.permissions = command.guild_permissions.get(x)
                    await self.add_guild_command(command, x)
                    commands["guilds"][x][command.name] = command
            else:
                await self.add_global_command(command)
                commands["globals"][command.name] = command
        # endregion

        for command in list(self.commands.values()):
            if command.guild_ids is not MISSING:
                for x in command.guild_ids or command.guild_permissions.keys():
                    if str(x) not in own_guild_ids:
                        raise InvalidArgument(
                            "Client is not in a server with the id '" + str(x) + "'"
                        )

                    if commands["guilds"].get(x) is None:
                        commands["guilds"][x] = {}

                    if command.guild_permissions is not MISSING:
                        command.permissions = command.guild_permissions.get(x)
                    await self.add_guild_command(command, x)
                    commands["guilds"][x][command.name] = command
            else:
                await self.add_global_command(command)
                commands["globals"][command.name] = command

        for base_name in self.subcommands:
            subcommands = list(self.subcommands[base_name].values())
            base = SlashCommand(
                None,
                subcommands[0].base_name,
                options=[x.to_dict() for x in subcommands],
                guild_ids=subcommands[0].guild_ids,
                default_permission=subcommands[0].default_permission,
                guild_permissions=subcommands[0].guild_permissions,
            )
            if base.guild_ids is not MISSING or base.guild_permissions is not MISSING:
                for x in base.guild_ids or base.guild_permissions.keys():
                    if str(x) not in own_guild_ids:
                        raise InvalidArgument(
                            "Client is not in a server with the id '" + str(x) + "'"
                        )

                    if commands["guilds"].get(x) is None:
                        commands["guilds"][x] = {}
                    await self.make_sub_command(base, guild_id=x)
                    commands["guilds"][x][base.name] = base
            else:
                await self.make_sub_command(base)
                commands["globals"][base.name] = base

        for base_name in self.subcommand_groups:
            subcommand_groups = list(self.subcommand_groups[base_name].values())
            base = SlashCommand(
                None,
                subcommand_groups[0].base_names[0],
                guild_ids=subcommand_groups[0].guild_ids,
                options=[],
                default_permission=subcommand_groups[0].default_permission,
                guild_permissions=subcommand_groups[0].guild_permissions,
            )

            for x in subcommand_groups:
                del x.base_names[0]

                subs: List[dict] = []
                for _base in x.base_names:
                    subs.append(
                        SlashOption(OptionType.SUB_COMMAND_GROUP, _base).to_dict()
                    )

                subs.append(x.to_dict())

                for i in range(0, len(subs) - 1):
                    subs[i]["options"] = [subs[i + 1]]

                if subs[0]["name"] not in [x["name"] for x in base.options]:
                    base.options += [subs[0]]
                else:
                    b = base.options
                    b[get_index(b, subs[0]["name"], lambda x: x.get("name"))][
                        "options"
                    ].append(subs[1])
                    base.options = b

            if base.guild_ids is not MISSING or base.guild_permissions is not MISSING:
                for x in base.guild_ids or base.guild_permissions.keys():
                    if str(x) not in own_guild_ids:
                        raise InvalidArgument(
                            "Client is not in a server with the id '" + str(x) + "'"
                        )

                    if commands["guilds"].get(x) is None:
                        commands["guilds"][x] = {}

                    await self.make_sub_command(base, guild_id=x)
                    commands["guilds"][x][base.name] = base
            else:
                await self.make_sub_command(base)
                commands["globals"][base.name] = base

        if self.delete_unused:
            api_coms = await self._get_global_commands()
            for apic in api_coms:
                if commands["globals"].get(apic["name"]) is None:
                    await delete_global_command(self._discord, apic["id"])
            async for x in self._discord.fetch_guilds():
                _id = str(x.id)
                api_coms = await self._get_guild_commands(_id)
                for apic in api_coms:
                    if (
                        commands["guilds"].get(_id) is None
                        or commands["guilds"][_id].get(apic["name"]) is None
                    ):
                        await delete_guild_command(self._discord, apic["id"], _id)

        # print("synchronized slash commands")

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
                print("Got forbidden in", x.name, x.id)
                continue
        return commands

    async def _get_guild_commands(self, guild_id: str) -> List[dict]:
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
                    await edit_global_command(
                        api_command["id"], self._discord, base.to_dict()
                    )
                else:
                    await delete_guild_command(
                        self._discord, api_command["id"], api_command["guild_id"]
                    )
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
        # If no command in that guild
        if api_command is None:
            # Check global commands
            api_command = await self._get_global_api_command(base.name)
            # If global command exists, it will be deleted
            if api_command is not None:
                await delete_global_command(self._discord, api_command["id"])
            await create_guild_command(
                base.to_dict(), self._discord, target_guild, base.permissions.to_dict()
            )
        else:
            # elif api_command != base:
            await edit_guild_command(
                api_command["id"],
                self._discord,
                target_guild,
                base.to_dict(),
                base.permissions.to_dict(),
            )

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
        print("nuking...")
        await self.delete_global_commands()
        print("nuked global commands")
        async for guild in self._discord.fetch_guilds():
            print("nuking commands in", guild.id)
            await self.delete_guild_commands(guild.id)
            print("nuked commands in", guild.id, guild.name)
        print("nuked")

    def command(
        self,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=True,
        guild_permissions=MISSING,
    ):
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
            choices: :class:`[type]`, optional
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
            self.commands[name] = SlashCommand(
                callback,
                name,
                description,
                options,
                guild_ids=guild_ids,
                default_permission=default_permission,
                guild_permissions=guild_permissions,
            )

        return wrapper

    def subcommand(
        self,
        base_name,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=True,
        guild_permissions=MISSING,
    ):
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
            if self.subcommands.get(base_name) is None:
                self.subcommands[base_name] = {}

            self.subcommands[base_name][name] = SubSlashCommand(
                callback,
                base_name,
                name,
                description,
                options=options,
                guild_ids=guild_ids,
                default_permission=default_permission,
                guild_permissions=guild_permissions,
            )

        return wrapper

    def subcommand_group(
        self,
        base_names,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=True,
        guild_permissions=MISSING,
    ):
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
            choices: :class:`[type]`, optional
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
            if self.subcommand_groups.get(base_names[0]) is None:
                self.subcommand_groups[base_names[0]] = {}
            self.subcommand_groups[base_names[0]][name] = SubSlashCommandGroup(
                callback,
                base_names,
                name,
                description,
                options=options,
                guild_ids=guild_ids,
                default_permission=default_permission,
                guild_permissions=guild_permissions,
            )

        return wrapper

    def user_command(
        self, name, guild_ids, default_permission=True, guild_permissions=MISSING
    ):
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
            self.context_commands["user"][name] = UserCommand(
                callback, name, guild_ids, default_permission, guild_permissions
            )

        return wraper

    def message_command(
        self, name, guild_ids, default_permission=True, guild_permissions=MISSING
    ):
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
            self.context_commands["message"][name] = MessageCommand(
                callback, name, guild_ids, default_permission, guild_permissions
            )

        return wraper


class Components:
    """A class for using and receiving message components in discord

    Parameters
    -----------
        client: :class:`discord.Client`
            The main discord client
        receive_events: :class:`bool`
            Whether events like components should be received

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

    def __init__(self, client: com.Bot, receive_events=True):
        """Creates a new compnent listener

        Example
        ```py
        Components(client)
        ```
        """
        self._listening_components = []
        """A list of components that are listening for interaction"""
        self._discord = client
        if receive_events is True:
            self._discord.add_listener(self._on_socket_response, "on_socket_response")

    async def _on_socket_response(self, msg):
        """Will be executed if the bot receives a socket response"""
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]

        if data["type"] != 3:
            return

        guild = await self._discord.fetch_guild(data["guild_id"])
        user = discord.Member(
            data=data["member"], guild=guild, state=self._discord._connection
        )

        msg = await getResponseMessage(
            self._discord._connection,
            data=data,
            application_id=self._discord.user.id,
            user=user,
            response=True,
        )
        component = (
            EphemeralComponent(
                self._discord.user.id,
                state=self._discord._connection,
                user=user,
                data=data,
            )
            if data["message"]["flags"] == 64
            else msg.interaction_component
        )

        # Get listening components with the same custom id
        _listening_components = [
            x for x in self._listening_components if data["data"]["custom_id"] == x[1]
        ]
        if len(_listening_components) == 1:
            await _listening_components[0][0](component, msg)

        if data["data"]["component_type"] == 2:
            self._discord.dispatch("button_press", component, msg)
        elif data["data"]["component_type"] == 3:
            self._discord.dispatch("menu_select", component, msg)

    async def send(
        self,
        channel,
        content=MISSING,
        *,
        tts=False,
        embed=MISSING,
        embeds=MISSING,
        file=MISSING,
        files=MISSING,
        delete_after=MISSING,
        nonce=MISSING,
        allowed_mentions=MISSING,
        reference=MISSING,
        mention_author=MISSING,
        components=MISSING,
    ) -> Message:
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

        Raises
        ------
        :raises: :class:`discord.InvalidArgument`: A passed argument was invalid
        """

        if type(channel) not in [discord.TextChannel, int, str]:
            raise discord.InvalidArgument("Channel must be of type discord.TextChannel")

        channel_id = channel.id if type(channel) is discord.TextChannel else channel
        payload = jsonifyMessage(
            content=content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=reference,
            mention_author=mention_author,
            components=components,
        )

        route = BetterRoute("POST", f"/channels/{channel_id}/messages")

        r = None
        if file is MISSING and files is MISSING:
            r = await self._discord.http.request(route, json=payload)
        else:
            r = await send_files(
                route, files=files or [file], payload=payload, http=self._discord.http
            )

        msg = Message(state=self._discord._get_state(), channel=channel, data=r)

        if delete_after is not None:
            await msg.delete(delay=delete_after)

        return msg

    def send_webhook(
        self,
        webhook,
        content=MISSING,
        *,
        wait=False,
        username=MISSING,
        avatar_url=MISSING,
        tts=False,
        files=MISSING,
        embed=MISSING,
        embeds=MISSING,
        allowed_mentions=MISSING,
        components=MISSING,
    ) -> Union[WebhookMessage, None]:
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
        payload = jsonifyMessage(
            content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            components=components,
        )
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


        """

        def wrapper(callback):
            if len([x for x in self._listening_components if x[1] == custom_id]) > 0:
                raise Exception(
                    "custom_id "
                    + str(custom_id)
                    + " is already in use! Use another custom_id"
                )
            self._listening_components.append((callback, custom_id))

        return wrapper


class UI:
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


    """

    def __init__(
        self,
        client,
        slash_options={
            "parse_method": ParseMethod.AUTO,
            "delete_unused": False,
            "wait_sync": 1,
        },
    ) -> None:
        """Creates a new ui object

        Example
        ```py
        UI(client, slash_options={"delete_unused": True, "wait_sync": 2})
        ```
        """
        self.components = Components(client)
        """For using message components
        
        :type: :class:`~Components`
        """
        if slash_options is None:
            slash_options = {
                "resolve_data": True,
                "delete_unused": False,
                "wait_sync": 1,
            }
        self.slash = Slash(client, **slash_options)
        """For using slash commands
        
        :type: :class:`~Slash`
        """
