import typing
from ..tools import MISSING

import inspect
import discord
from discord.errors import InvalidArgument


class SlashOption:
    """An option for a slash command

    Parameters
    ----------
        argument_type: :class:`int` | :class:`str` | :class:`class`
            What type of parameter the option should accept
        name: :class:`str`
            1-32 lowercase character name for the option
        description: :class:`str`, optional
            1-100 character description of the command; default name
        required: :class:`bool`, optional
            If the parameter is required or optional; default False
        choices: List[:class:`dict`], optional
            Choices for string and int types for the user to pick from; default MISSING
                Choices should be formated like this: ``[{"name": "name of the choice", "value": "the real value"}, ...]``

                .. note::

                    The choice value has to be of the same type as the type this option accepts

        options: :class:`~SlashOption`
            This parameter is only for subcommands to work, you shouldn't need to use that, unless you know what you're doing
    """

    def __init__(
        self,
        argument_type,
        name,
        description=MISSING,
        required=False,
        choices=MISSING,
        options=MISSING,
    ) -> None:
        """
        Creates a new option for a slash command

        Example
        ```py
        SlashOption(argument_type=int, name="Your number", required=True, choices=[{"name": "a cool number", "value": 2}])
        ```
        """
        self._json = {}
        self.argument_type = argument_type
        self.name = name
        self.description = description or name
        if required is True:
            self.required = required

        if options is not MISSING:
            self.options = options
        if choices is not MISSING:
            self._json["choices"] = choices

    @property
    def argument_type(self) -> int:
        """Parameter type that the option accepts

        :type: :class:`int`
        """
        return self._json["type"]

    @argument_type.setter
    def argument_type(self, value):
        self._json["type"] = OptionTypes.any_to_type(value)

    @property
    def name(self) -> str:
        """The name of the option appearing in discord

        :type: :class:`str`
        """
        return self._json["name"]

    @name.setter
    def name(self, value):
        if len(value) > 32 or len(value) < 1:
            raise InvalidArgument("name must be between 1 and 32 characters")
        self._json["name"] = value.lower().replace(" ", "_")

    @property
    def description(self) -> str:
        """The description of the option appearing under the name

        :type: :class:`str`
        """
        return self._json["description"]

    @description.setter
    def description(self, value):
        if len(value) > 100 or len(value) < 1:
            raise InvalidArgument("description must be between 1 and 100 characters")
        self._json["description"] = value

    @property
    def required(self) -> bool:
        """Whether this parameter is required to use or not

        :type: :class:`bool`
        """
        return self._json.get("required", False)

    @required.setter
    def required(self, value):
        if type(value) is not bool:
            raise InvalidArgument(
                "required has to be of type bool, not " + str(type(value))
            )
        self._json["required"] = value

    @property
    def choices(self) -> typing.List[dict]:
        """Choices for string and int types for the user to pick from

        .. note::

            Choices are formated like this: ``[{"name": "name of the choice", "value": "the real value"}, ...]``

        :type: List[:class:`dict`]
        """
        return self._json.get("choices")

    @choices.setter
    def choices(self, value):
        self._json["choices"] = value

    @property
    def options(self) -> typing.List["SlashOption"]:
        return [
            SlashOption(
                x["type"],
                x["name"],
                x["description"],
                x.get("required", False),
                x.get("choices"),
                x.get("options"),
            )
            for x in self._json.get("options")
        ]

    @options.setter
    def options(self, options):
        if type(options) is list and all(type(x) is SlashOption for x in options):
            self._json["options"] = [x.to_dict() for x in options]
        elif type(options) is list and all(type(x) is dict for x in options):
            self._json["options"] = options
        else:
            raise InvalidArgument(
                "'options' has to be of type List[dict] or List[dict], not "
                + str(type(options))
            )

    def to_dict(self):
        return self._json


class OptionTypes:
    """The list of possible slash command option types"""

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    FLOAT = 10

    @classmethod
    def any_to_type(cls, whatever):
        if type(whatever) is int and whatever in range(1, 11):
            return whatever
        if inspect.isclass(whatever):
            if whatever is str:
                return cls.STRING
            if whatever is int:
                return cls.INTEGER
            if whatever is bool:
                return cls.BOOLEAN
            if whatever in [discord.User, discord.Member]:
                return cls.USER
            if whatever is discord.TextChannel:
                return cls.CHANNEL
            if whatever is discord.Role:
                return cls.ROLE
            if whatever is float:
                return cls.FLOAT
        if type(whatever) is str:
            whatever = whatever.lower()
            if whatever in ["str", "string"]:
                return cls.STRING
            if whatever in ["int", "integer"]:
                return cls.INTEGER
            if whatever in ["bool", "boolean"]:
                return cls.BOOLEAN
            if whatever in [
                "user",
                "discord.user",
                "member",
                "discord.member",
                "usr",
                "mbr",
            ]:
                return cls.USER
            if whatever in [
                "channel",
                "textchannel",
                "discord.textchannel",
                "txtchannel",
            ]:
                return cls.CHANNEL
            if whatever in ["role", "discord.role"]:
                return cls.ROLE
            if whatever in ["mentionable", "mention"]:
                return cls.MENTIONABLE
            if whatever in ["float", "floating", "floating number", "f"]:
                return cls.FLOAT


class SlashPermission:
    """Permissions for a slash commannd

    Parameters
    ----------
        allowed_ids: :class:`dict`, optional
            A list of ids that can use the command; default MISSING
                Format: ``{"role_or_user_id": permission_type}]``


        forbidden_ids: :class:`dict`, optional
            A list of ids that are forbidden to use the command; default MISSING


        .. note::

            If you want to use a role id, the permission type has to be 1, and if you want to specify a user id, it has to be 2

            You can use ``SlashPermission.ROLE`` and ``SlashPermission.USER`` instead
    """

    def __init__(self, allowed_ids: dict = MISSING, forbidden_ids=MISSING) -> None:
        """Creates a new permission object for a slash command

        Example
        ```py
        SlashPermission(forbidden_ids={
                "785567792899948577": SlashPermission.ROLE,
                "355333222596476930": SlashPermission.USER,
                "539459006847254542": SlashPermission.USER
            }, allowed_ids={
                "539459006847255232": SlashPermission.User
            }
        )
        ```
        """

        self._json = []
        if allowed_ids is not MISSING:
            for _id, _type in allowed_ids.items():
                self._json.append({"id": _id, "type": _type, "permission": True})
        if forbidden_ids is not MISSING:
            for _id, _type in forbidden_ids.items():
                self._json.append({"id": _id, "type": _type, "permission": False})

    def to_dict(self):
        return self._json

    ROLE = 1
    USER = 2

    @property
    def allowed_ids(self) -> typing.List[typing.Union[str, int]]:
        return [x["id"] for x in self._json if x["permission"] == True]

    @property
    def forbidden_ids(self) -> typing.List[typing.Union[str, int]]:
        return [x["id"] for x in self._json if x["permission"] == False]


class SlashCommand:
    """A basic slash command

    Parameters
    ----------
        name: :class:`str`
            1-32 characters long name
            .. note::

                The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
        description: :class:`str`, optional
            1-100 character description of the command; default the command name
        options: List[:class:`~SlashOptions`], optional
            Parameters for the command; default MISSING
        choices: :class:`[type]`, optional
            Choices for string and int types for the user to pick from; default MISSING
        guild_ids: :class:`str` | :class:`int`, optional
            A list of guild ids where the command is available; default MISSING
        default_permission: :class:`bool`
            Whether the command should be usable for everyone or not
        guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
            The permissions for the command in guilds
                Format: ``{"guild_id": SlashPermission}``


    """

    def __init__(
        self,
        callback,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=MISSING,
        guild_permissions=MISSING,
    ) -> None:
        """
        Creates a new base slash command

        Example

        ```py
        async def my_function(command, parameter=None):
            pass

        SlashCommand(callback=my_function, name="hello_world", description="This is a test command",
            options=[
                SlashOption(str, name="parameter", description="this is a parameter", choices=[{ "name": "choice 1", "value": 1 }])
            ], guild_ids=["785567635802816595"], default_permission=False,
            guild_permissions={
                "785567635802816595": SlashPermission(allowed_ids={"539459006847254542": SlashPermission.USER})
            })
        ```
        """
        self._json = {}
        self.name = name
        self.description = description or name
        if callback is not None:
            if not inspect.iscoroutinefunction(callback):
                raise InvalidArgument("callback has to be async")

            callback_params = inspect.signature(callback).parameters
            if options is not MISSING:
                for op in options:
                    if callback_params.get(op.name) is None:
                        raise InvalidArgument(
                            "Missing parameter '" + op.name + "' in callback function"
                        )
                    param = callback_params[op.name]
                    if not op.required and param.default is param.empty:
                        raise InvalidArgument(
                            "Parameter '"
                            + param.name
                            + "' in callback function needs to be optional ("
                            + param.name
                            + "=None)"
                        )

        self.callback = callback

        if options is not MISSING:
            self.options = options
        if default_permission is not MISSING:
            self.default_permission = default_permission
        self.guild_permissions: typing.Dict[(str, SlashPermission)] = (
            guild_permissions or MISSING
        )
        self.permissions = SlashPermission()

        self.guild_ids = guild_ids

    # region command
    @property
    def name(self) -> str:
        """The name of the slash command

        :type: :class:`str`
        """
        return self._json["name"]

    @name.setter
    def name(self, value):
        if len(value) > 32 or len(value) < 1:
            raise InvalidArgument("name must be between 1 and 32 characters")
        self._json["name"] = str(value).lower().replace(" ", "-")

    @property
    def description(self) -> str:
        """The description of the command

        :type: :class:`str`
        """
        return self._json["description"]

    @description.setter
    def description(self, value):
        if len(value) > 100 or len(value) < 1:
            raise InvalidArgument("description must be between 1 and 100 characters")
        self._json["description"] = value

    @property
    def options(self) -> typing.List["SlashOption"]:
        """The parameters for the command

        :type: List[:class:`~SlashOption`]
        """
        return self._json.get("options")

    @options.setter
    def options(self, options):
        if all(type(x) is SlashOption for x in options):
            self._json["options"] = [x.to_dict() for x in options]
        elif all(type(x) is dict for x in options):
            self._json["options"] = options
        else:
            raise InvalidArgument(
                "options must be of type List[dict] or List[SlashOptions] not "
                + str(type(options))
            )

    # endregion
    # region permissions
    @property
    def default_permission(self):
        return self._json["default_permission"]

    @default_permission.setter
    def default_permission(self, value):
        self._json["default_permission"] = value

    # endregion

    def to_dict(self):
        return self._json

    def __eq__(self, o: object) -> bool:
        if type(o) is dict:
            return (
                o.get("name") == self.name
                and o.get("description") == self.description
                and o.get("options") == self.options
            )
        elif type(o) is SlashCommand:
            return (
                o.name == self.name
                and o.description == self.description
                and o.options == self.options
            )
        else:
            return False


class SubSlashCommand(SlashCommand):
    def __init__(
        self,
        callback,
        base_name,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=MISSING,
        guild_permissions=MISSING,
    ) -> None:
        SlashCommand.__init__(
            self,
            callback,
            name,
            description,
            options,
            guild_ids=guild_ids,
            default_permission=default_permission,
            guild_permissions=guild_permissions,
        )
        self.base_name = base_name.replace(" ", "-").lower()

    def to_dict(self):
        return SlashOption(
            OptionTypes.SUB_COMMAND, self.name, self.description, options=self.options
        ).to_dict()


class SubSlashCommandGroup(SlashCommand):
    def __init__(
        self,
        callback,
        base_names,
        name,
        description=MISSING,
        options=MISSING,
        guild_ids=MISSING,
        default_permission=MISSING,
        guild_permissions=MISSING,
    ) -> None:
        if len(base_names) > 2:
            raise InvalidArgument("subcommand groups are currently limited to 2 bases")
        if any([len(x) > 32 or len(x) < 1 for x in base_names]):
            raise InvalidArgument(
                "base_names needs to be between 32 and 1 characters long"
            )
        SlashCommand.__init__(
            self,
            callback,
            name,
            description,
            options,
            guild_ids=guild_ids,
            default_permission=default_permission,
            guild_permissions=guild_permissions,
        )
        self.base_names = [x.replace(" ", "-").lower() for x in base_names]

    def to_dict(self):
        return SlashOption(
            OptionTypes.SUB_COMMAND, self.name, self.description, options=self.options
        ).to_dict()
