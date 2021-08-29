from ..tools import MISSING, _or
from ..errors import InvalidLength, WrongType
from .errors import CallbackMissingContextCommandParameters, MissingOptionParameter, NoAsyncCallback, OptionalOptionParameter

import discord
from discord.errors import InvalidArgument

import typing
import inspect

def format_name(value):
    return str(value).lower().replace(" ", "-")

class SlashOption():
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
    def __init__(self, argument_type, name, description=MISSING, required=False, choices=[], options=[]) -> None:
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
        self.description = _or(description, name)
        if required is True:
            self.required = required
        if options is not MISSING:
            self.options = options
        if choices is not MISSING:
            self._json["choices"] = choices
    def __repr__(self) -> str:
        return f"<discord_ui.SlashOption({str(self.to_dict())})>"
    def __eq__(self, o: object) -> bool:
        if isinstance(o, SlashOption):
            return (self.argument_type == o.argument_type and self.name == o.name and self.description == o.description and self.required == o.required and self.choices == o.choices and self.options == o.options)
        elif isinstance(o, dict):
            return (self.argument_type == o["type"] and self.name == o["name"] and self.description == o.get("description") and self.required == o.get("required", False) and self.choices == o.get("choices", []) and self.options == o.get("options", []))
        return False
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    @property
    def argument_type(self) -> int:
        """Parameter type that the option accepts
        
        :type: :class:`int`
        """
        return self._json["type"]
    @argument_type.setter
    def argument_type(self, value):
        self._json["type"] = OptionType.any_to_type(value)

    @property
    def name(self) -> str:
        """The name of the option appearing in discord
        
        :type: :class:`str`
        """
        return self._json["name"]
    @name.setter
    def name(self, value):
        if len(value) > 32 or len(value) < 1:
            raise InvalidLength("name", 1, 32)
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
            raise InvalidLength("description", 1, 100)
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
            raise WrongType("required", value, "bool") 
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
    def options(self) -> typing.List['SlashOption']:
        return [SlashOption._from_data(x) for x in self._json.get("options", [])]
    @options.setter
    def options(self, options):
        if type(options) is not list:
            raise WrongType("options", options, "list")
        if all(type(x) in [SlashOption, dict] for x in options):
            self._json["options"] = [(x.to_dict() if type(x) is SlashOption else x) for x in options]
        else:
            i = 0
            for x in options:
                if type(x) is not SlashOption and type(x) is not dict:
                    raise WrongType("options[" + str(i) + "]", x, ["dict", "SlashOption"])
                i += 1

    @staticmethod
    def _from_data(data: dict):
        return SlashOption(data["type"], data["name"], data["description"], data.get("required", False), data.get("choices", MISSING), data.get("options", MISSING))

    def to_dict(self):
        return self._json

class OptionType:
    """The list of possible slash command option types"""

    SUB_COMMAND             =          Subcommand           =           1
    SUB_COMMAND_GROUP       =          Subcommand_group     =           2
    STRING                  =          String               =           3
    INTEGER                 =          Integer              =           4
    BOOLEAN                 =          Boolean              =           5
    MEMBER     =   USER     =          Member               =   User  = 6
    CHANNEL                 =          Channel              =           7
    ROLE                    =          Role                 =           8
    MENTIONABLE             =          Mentionable          =           9
    FLOAT                   =          Float                =          10

    @classmethod
    def any_to_type(cls, whatever):
        """Converts something to a option type if possible"""
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
                return cls.MEMBER
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
            if whatever in ["user", "discord.user", "member", "discord.member", "usr", "mbr"]:
                return cls.MEMBER
            if whatever in ["channel", "textchannel", "discord.textchannel", "txtchannel"]:
                return cls.CHANNEL
            if whatever in ["role", "discord.role"]:
                return cls.ROLE
            if whatever in ["mentionable", "mention"]:
                return cls.MENTIONABLE
            if whatever in ["float", "floating", "floating number", "f"]:
                return cls.FLOAT
class AdditionalType:
    MESSAGE     =       44
    GUILD       =       45
class CommandType:
    SLASH       =       Slash       =       1
    USER        =       User        =       2
    MESSAGE     =       Message     =       3

    @staticmethod
    def from_string(typ):
        if type(typ) == str:
            if typ.lower() == "slash":
                return CommandType.SLASH
            elif typ.lower() == "user":
                return CommandType.USER
            elif typ.lower() == "message":
                return CommandType.MESSAGE
        else:
            return typ


class SlashPermission():
    """Permissions for a slash commannd
        
        Parameters
        ----------
            allowed: :class:`dict` | List[:class:`discord.Member` | :class:`discord.User` | :class:`discord.Role`], optional
                A list of ids, users or members that can use the command; default MISSING
                    Format: ``{"role_or_user_id": permission_type}]``


            forbidden: :class:`dict` | List[:class:`discord.Member` | :class:`discord.User` | :class:`discord.Role`], optional
                A list of ids, users or members that are forbidden to use the command; default MISSING
        

            .. note::

                If you want to use a role id, the permission type has to be 1, and if you want to specify a user id, it has to be 2

                You can use ``SlashPermission.ROLE`` and ``SlashPermission.USER`` instead

        """
    def __init__(self, allowed: dict=MISSING, forbidden=MISSING) -> None:
        """Creates a new permission object for a slash command
        
        Example
        ```py
        SlashPermission(allowed=[                
                await bot.fetch_user(bot.owner_id)
            ], forbidden={
                539459006847255232: SlashPermission.User,
                874357255829606402: SlashPermission.Role
            }
        )
        ```
        """
        
        self._json = []
        if allowed is not MISSING:
            if type(allowed) is dict:
                for _id, _type in allowed.items():
                    self._json.append(
                        {
                            "id": int(_id),
                            "type": _type,
                            "permission": True
                        }
                    )
            elif type(allowed) is list:
                for t in allowed:
                    self._json.append({
                        "id": t.id,
                        "type": SlashPermission.USER if type(t) in [discord.User, discord.Member] else SlashPermission.ROLE,
                        "permission": True
                    })
        if forbidden is not MISSING:
            if type(forbidden) is dict:
                for _id, _type in forbidden.items():
                    self._json.append(
                        {
                            "id": int(_id),
                            "type": _type,
                            "permission": False
                        }
                    )
            elif type(forbidden) is list:
                for t in forbidden:
                    self._json.append({
                        "id": t.id,
                        "type": SlashPermission.USER if type(t) in [discord.User, discord.Member] else SlashPermission.ROLE,
                        "permission": False
                    })
            else:
                raise WrongType("forbidden", forbidden, ["Dict[int | str, int]", "List[discord.Member | discord.User | discord.Role]"])

    @classmethod
    def Empty(cls) -> 'SlashPermission':
        """Returns an empty permission for the command"""
        return cls()
    def to_dict(self):
        return self._json
    def __eq__(self, o: object) -> bool:
        if isinstance(o, SlashPermission):
            return (
                len(self.allowed) == len(o.allowed) and all(self.allowed[i] == o.allowed[i] for i, _ in enumerate(o.allowed)) and
                len(self.forbidden) == len(o.forbidden) and all(self.forbidden[i] == o.forbidden for i, _ in enumerate(o.forbidden))
            )
        elif isinstance(o, dict):
            o_allowed = [x for x in o["permissions"] if x["permission"] == True]
            o_forbidden = [x for x in o["permissions"] if x["permission"] == False]

            return (
                len(self.allowed) == len(o_allowed) and all(self.allowed[i] == o_allowed[i] for i, _ in enumerate(self.allowed)) and
                len(self.forbidden) == len(o_forbidden) and all(self.forbidden[i] == o_forbidden[i] for i, _ in enumerate(self.forbidden))
            )
        return False
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)
    def __repr__(self) -> str:
        return f"<discord_ui.SlashPermission({self.to_dict()})>"

    ROLE        =       Role      =   1
    USER        =       User      =   2

    @property
    def allowed(self) -> typing.List[typing.Union[str, int]]:
        return [x for x in self._json if x["permission"] == True]
    @property
    def forbidden(self) -> typing.List[typing.Union[str, int]]:
        return [x for x in self._json if x["permission"] == False]


class SlashCommand():
    """A basic slash command
        
        Parameters
        ----------
            callback: :class:`function`
                The callback function
            name: :class:`str`
                1-32 characters long name
                    If name is not passed, the name of the callback function will be used; default MISSING
                .. important::

                    The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)

            description: :class:`str`, optional
                1-100 character description of the command; default MISSING
                    If description is not passed, the docstring description of the callback function is used. 
                    If no docstring exists, the name of the command will be used
            options: List[:class:`~SlashOptions`], optional
                Parameters for the command; default MISSING
            choices: List[:class:`dict`], optional
                Choices for string and int types for the user to pick from; default MISSING
            guild_ids: :class:`str` | :class:`int`, optional
                A list of guild ids where the command is available; default MISSING
            default_permission: :class:`bool`
                Whether the command should be usable for everyone or not
            guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
                The permissions for the command in guilds
                    Format: ``{"guild_id": SlashPermission}``


    """
    def __init__(self, callback, name=MISSING, description=MISSING, options=[], guild_ids=MISSING, default_permission=MISSING, guild_permissions=MISSING) -> None:
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
                "785567635802816595": SlashPermission(allowed={"539459006847254542": SlashPermission.USER}) 
            })
        ```
        """
        self._json = {
            "type": CommandType.SLASH
        }

        # Check options before callback because callback makes an option check
        if options is not MISSING:
            self.options: typing.List[SlashOption] = options

        if callback is not None:
            if not inspect.iscoroutinefunction(callback):
                raise NoAsyncCallback()

            callback_params = inspect.signature(callback).parameters
            if options is not MISSING:
                for op in options:
                    if callback_params.get(op.name) is None:
                        raise MissingOptionParameter(op.name)
                    param = callback_params[op.name]
                    if not op.required and param.default is param.empty:
                        raise OptionalOptionParameter(param.name)
        
        self.callback: function = callback
        self.name = _or(name, self.callback.__name__ if self.callback not in [None, MISSING] else None)
        self.description = _or(description, (inspect.getdoc(self.callback) if self.callback not in [None, MISSING] else None), name)
        if default_permission is MISSING:
            default_permission = True
        self.default_permission: bool = default_permission
        if guild_permissions is not MISSING:
            for _id, perm in list(guild_permissions.items()):
                if type(_id) not in [str, int, discord.User, discord.Member, discord.Role]:
                    raise WrongType("guild_permissions key " + str(_id), _id, ["str", "int", "discord.User", "discord.Member", "discord.Role"])
                if type(perm) is not SlashPermission:
                    raise WrongType("guild_permission[" + ("'" if type(_id) is str else "") + str(_id) + ("'" if type(_id) is str else "") + "]", perm, "SlashPermission")
        
        self.guild_permissions: typing.Dict[(typing.Union[str, int], SlashPermission)] = guild_permissions or MISSING
        self.permissions: SlashPermission = SlashPermission()
        self.guild_ids: typing.List[int] = [int(x) for x in _or(guild_ids, [])]

    def __str__(self) -> str:
        return str(self.to_dict())
    def __eq__(self, o: object) -> bool:
        if type(o) is dict:
            return (
                o.get('type') == self._json["type"] 
                and o.get('name') == self.name
                and o.get('description') == self.description
                and o.get('options', []) == self.options
                and o.get("default_permission", False) == self.default_permission
            )
        elif isinstance(o, SlashCommand):
            return (
                o._json('type') == self._json["type"] 
                and o.name == self.name
                and o.description == self.description
                and o.options == self.options
                and o.default_permission == self.default_permission
            )
        else:
            return False
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)


    # region command
    @property
    def command_type(self):
        return self._json["type"]

    @property
    def name(self) -> str:
        """The name of the slash command
        
        :type: :class:`str`
        """
        return self._json["name"]
    @name.setter
    def name(self, value):
        if value in [None, MISSING]:
            raise InvalidArgument("You have to specify a name")
        if type(value) is not str:
            raise WrongType("name", value, "str")
        if len(value) > 32 or len(value) < 1:
            raise InvalidLength("name", 1, 32)
        self._json["name"] = format_name(value)
    @property
    def description(self) -> str:
        """The description of the command
        
        :type: :class:`str`
        """
        return self._json['description']
    @description.setter
    def description(self, value):
        if type(value) is not str:
            raise WrongType("description", value, "str")
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("description", 1, 100)
        self._json["description"] = value
    @property
    def options(self) -> typing.List['SlashOption']:
        """The parameters for the command
        
        :type: List[:class:`~SlashOption`]
        """
        return [SlashOption._from_data(x) for x in self._json.get("options", [])]
    @options.setter
    def options(self, options):
        if type(options) is not list:
            raise WrongType("options", options, "list")
        if all(type(x) in [SlashOption, dict] for x in options):
            self._json["options"] = [(x.to_dict() if type(x) is SlashOption else x) for x in options]
        else:
            i = 0
            for x in options:
                if type(x) is not SlashOption and type(x) is not dict:
                    raise WrongType("options[" + str(i) + "]", x, ["dict", "SlashOption"])
                i += 1
    # endregion
    # region permissions
    @property
    def default_permission(self):
        return self._json.get("default_permission", False)
    @default_permission.setter
    def default_permission(self, value):
        self._json["default_permission"] = value
    # endregion

    def to_dict(self):
        return self._json
class SubSlashCommandGroup(SlashCommand):
    def __init__(self, callback, base_names, name, description=MISSING, options=[], guild_ids=MISSING, default_permission=MISSING, guild_permissions=MISSING) -> None:
        if type(base_names) is str:
            base_names = [base_names]
        if len(base_names) > 2:
            raise InvalidArgument("subcommand groups are currently limited to 2 bases")
        if any([len(x) > 32 or len(x) < 1 for x in base_names]):
            raise InvalidLength("base_names", 1, 32)
        SlashCommand.__init__(self, callback, name, description, options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
        self.base_names = [format_name(x) for x in base_names]
        
    def to_option(self) -> SlashOption:
        return SlashOption(OptionType.SUB_COMMAND, self.name, self.description, options=self.options or MISSING)
    def to_dict(self):
        return self.to_option().to_dict()



class ContextCommand(SlashCommand):
    def __init__(self, callback, name, guild_ids, default_permission = True, guild_permissions = MISSING) -> None:
        if callback is not None:
            callback_params = inspect.signature(callback).parameters
            if len(callback_params) < 2:
                raise CallbackMissingContextCommandParameters()
        super().__init__(callback, name, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)

    @property
    def description(self):
        return ""
    @description.setter
    def description(self, value):
        pass
    @property
    def options(self):
        return []
    @options.setter
    def options(self, value):
        pass
        
class UserCommand(ContextCommand):
    def __init__(self, callback, name, guild_ids = MISSING, default_permission = True, guild_permissions = MISSING) -> None:
        super().__init__(callback, name, guild_ids, default_permission, guild_permissions)
        self._json["type"] = CommandType.USER

class MessageCommand(ContextCommand):
    def __init__(self, callback, name, guild_ids = MISSING, default_permission = True, guild_permissions = MISSING) -> None:
        super().__init__(callback, name, guild_ids, default_permission, guild_permissions)
        self._json["type"] = CommandType.MESSAGE