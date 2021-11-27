from __future__ import annotations
import asyncio

from .http import ModifiedSlashState
from ..tools import All, _raise
from ..enums import CommandType, OptionType
from ..errors import InvalidLength, WrongType
from .errors import (
    CallbackMissingContextCommandParameters, 
    MissingOptionParameter, 
    NoAsyncCallback, 
    OptionalOptionParameter,
    NoCommandFound
)

import discord
from discord.ext.commands import Bot, BadArgument

import re
import typing as t
import inspect

__all__ = (
    'SlashOption',
    'SlashPermission',
)

C = t.TypeVar("C")

class OptionDataPayload(t.TypedDict):
    type: int 
    name: str
    options: t.Optional[OptionDataPayload]
class InteractionDataPayload(t.TypedDict):
    type: int
    options: t.List[OptionDataPayload]
    name: str
    id: str
class InteractionPayload(t.TypedDict):
    version: int
    type: int
    token: str
    member: discord.member.MemberPayload
    id: str
    guild_id: t.Optional[str]
    data: InteractionDataPayload
    channel_id: str
    application_id: str

def format_name(value):
    return str(value).lower().replace(" ", "-")


class SlashOptionCollection():
    def __init__(self, options=[]):
        self.__options = {
            x.name if isinstance(x, SlashOption) else x["name"]: 
                SlashOption._from_data(x, x.choice_generator if isinstance(x, SlashOption) else None) if isinstance(x, dict) else x 
            for x in options
        }
    
    def __repr__(self) -> str:
        return "<SlashOptionCollection[" + ', '.join([x.__repr__() for x in self]) + "]>"
    def __eq__(self, o):
        if isinstance(o, SlashOptionCollection):
            return len(self) == len(o) and self.__options == o.__options
        if isinstance(o, list):
            return len(o) == len(self.__options) and list(self.__options.values()) == o
        return False
    def __len__(self):
        return len(self.__options)
    def __iter__(self) -> t.List[SlashOption]:
        return iter(self.__options.values())
    def __getitem__(self, index):
        if isinstance(index, int):
            return list(self.__options.values())[index]
        elif isinstance(index, str):
            return self.__options[index]
        raise TypeError()
    def __setitem__(self, index, value):
        if isinstance(index, int):
            self.__options[list(self.__options.keys())[index]] = value
        elif isinstance(index, str):
            self.__options[index] = value
        else:
            raise WrongType("index", index, ["int", "str"])
    def __delitem__(self, index):
        if isinstance(index, int):
            del self.__options[list(self.__options.keys())[index]]
        elif isinstance(index, str):
            del self.__options[index]
        else:
            raise WrongType("index", index, ["int", "str"])
    def __add__(self, value):
        if isinstance(value, list):
            if all(isinstance(x, SlashOption) for x in value):
                copy = self.copy()
                for x in value:
                   copy.set(x.name, x)
                return copy
            elif all(isinstance(x, dict) for x in value):
                copy = self.copy()
                for x in value:
                   copy.set(x["name"], SlashOption._from_data(x))
                return copy
            else:
                for i, x in enumerate(value):
                    if not isinstance(value, (dict, SlashOption)):
                        raise WrongType(f"value[{i}]", x, ["list", "SlashOption", "dict"])
        if isinstance(value, SlashOption):
            return self.copy().set(value.name, value)
        elif isinstance(value, dict):
            return self.copy().set(value["name"], SlashOption._from_data(value))
        else:
            raise WrongType("value", value, ["list", "SlashOption", "dict"])
    
    def append(self, value):
        self.__options[value.name] = value
    def copy(self):
        return self.__class__(list(self.__options.values()))
    def get(self, index: t.Union[str, int], default=None):
        try:
            return self.__getitem__(index)
        except (IndexError, KeyError):
            return default
    def set(self, index, value):
        self.__setitem__(index, value)
        return self
    def remove(self, command: BaseCommand):
        type_key = str(command.command_type)
        if command.is_global:
            try:
                del self["globals"][type_key][command.name]
            except KeyError:
                pass
            return
        for x in command.guild_ids:
            guild = str(x)
            try:
                del self[guild][type_key][command.name]
            except KeyError:
                continue
    def to_dict(self):
        return [x.to_dict() for x in self]

class SlashOption():
    """An option for a slash command
        
    Parameters
    ----------
    type: :class:`int` | :class:`str` | :class:`class` | :class:`~OptionType`
        What type of parameter the option should accept.
    name: :class:`str`
        1-32 lowercase character name for the option.
    description: :class:`str`, optional
        1-100 character description of the command; default `\u200b`
    required: :class:`bool`, optional
        If the parameter is required or optional; default False
    choices: List[:class:`dict`], optional
        Choices for string and int types for the user to pick from; default None
            Choices should be formated like this: ``[{"name": "name of the choice", "value": "the real value"}, ...]``

            .. note::

                The choice value has to be of the same type as the type this option accepts.
    
    autocomplete: :class:`bool`, optional
        Whether the choices should be autogenerated; default None
    choice_generator: :class:`function`, optional
        A function that generates the choices for this option. Needds to return a list of dicts or tuples; default None
            This will automatically set autocomplete to True if autocomplete was not passed.
    options: List[:class:`~SlashOption`]
        This parameter is only for subcommands to work, you shouldn't need to use that, unless you know what you're doing.
    channel_types: List[:class:`discord.ChannelType`]
        If the option is a channel type, the channels shown will be restricted to these types.
    min_value: :class:`int`
        If the option type is numeric (``float`` or ``int``) the minimum value permitted
    max_value: :class:`int`
        If the option type is numeric (``float`` or ``int``) the maximum value permitted
    """
    def __init__(self, type, name, description=None, required=False, choices=None, 
        autocomplete=None, choice_generator=None, options=None, channel_types=None,
        min_value=None, max_value=None
    ) -> None:
        """
        Creates a new option for a slash command

        Example
        ```py
        SlashOption(type=int, name="Your number", required=True, choices=[{"name": "a cool number", "value": 2}])
        ```
        """

        self.__choice_generators__ = {}
        self._options = SlashOptionCollection()
        self._json = {}

        self.type = type
        self.name = name
        self.description = description or "\u200b"
        self.required = required
        self.options = options or []
        self.autocomplete = autocomplete or choice_generator is not None
        self.choices = choices if self.autocomplete is False else None
        self.choice_generator: t.Callable[[t.Any], t.List[t.Union[dict, tuple]]] = choice_generator
        """A function which will generate choices for this option"""
        self.channel_types = channel_types
        self.min_value = min_value
        self.max_value = max_value
    def __repr__(self) -> str:
        return f"<discord_ui.SlashOption({str(self.to_dict())})>"
    def __eq__(self, o: object) -> bool:
        if isinstance(o, SlashOption):
            return (
                self.type == o.type 
                    and 
                self.name == o.name 
                    and 
                self.description == o.description 
                    and 
                self.required == o.required 
                    and 
                self.choices == o.choices 
                    and 
                self.options == o.options
                    and
                sorted(self.channel_types) == sorted(o.channel_types)
                    and
                self.min_value == o.min_value
                    and
                self.max_value == o.max_value
            )
        elif isinstance(o, dict):
            return (
                self.type == o["type"] 
                    and 
                self.name == o["name"] 
                    and 
                self.description == o.get("description") 
                    and 
                self.required == o.get("required", False)
                    and 
                (self.choices == o.get("choices", []) or self.choices == o.get("choices", None))
                    and 
                (self.options == o.get("options", []) or self.options == o.get("options", None))
                    and
                self.autocomplete == o.get("autocomplete", False)
                    and
                sorted([x.value for x in self.channel_types]) == sorted(o.get("channel_types", []))
                    and
                self.min_value == o.get("min_value")
                    and
                self.max_value == o.get("max_value")
            )
        return False
    
    def autocomplete_function(self, callback):
        """Decorator for the autocomplete choice generator
        
        Usage
        ------

        .. code-block::

            op = SlashOption(...)
            
            @op.autocomplete_function
            async def generator(ctx):
                ... 
        """
        self.autocomplete = True
        self.choice_generator = callback
        return callback

    @property
    def type(self) -> int:
        """Parameter type that the option accepts"""
        return OptionType(self._json["type"])
    @type.setter
    def type(self, value: OptionType):
        type = OptionType.any_to_type(value) if not isinstance(value, OptionType) else value
        self._json["type"] = type
        if hasattr(type, "__channel_types__"):
            self.channel_types = type.__channel_types__
        if hasattr(type, "__min__"):
            self.min_value = type.__min__
        if hasattr(type, "__max__"):
            self.max_value = type.__max__

    @property
    def channel_types(self):
        """A list of channel types that will restrict the shown channels for this option"""
        return [discord.ChannelType(x) for x in self._json.get("channel_types", [])]
    @channel_types.setter
    def channel_types(self, value):
        self._json["channel_types"] = [x.value for x in (value or [])]
    @property
    def min_value(self):
        """If the option is an ``INTEGER`` or ``NUMBER`` type, the minimum value permitted"""
        return self._json.get("min_value")
    @min_value.setter
    def min_value(self, value):
        if value is not None:
            self._json["min_value"] = value
    @property
    def max_value(self):
        """If the option is an ``INTEGER`` or ``NUMBER`` type, the maximum value permitted"""
        return self._json.get("max_value")
    @max_value.setter
    def max_value(self, value):
        if value is not None:
            self._json["max_value"] = value


    @property
    def name(self) -> str:
        """The name of the option appearing in discord"""
        return self._json["name"]
    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise WrongType("name", value, "str")
        if len(value) > 32 or len(value) < 1:
            raise InvalidLength("name", 1, 32)
        self._json["name"] = format_name(value)


    @property
    def description(self) -> str:
        """The description of the option appearing under the name"""
        return self._json["description"]
    @description.setter
    def description(self, value):
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("description", 1, 100)
        self._json["description"] = value

    @property
    def required(self) -> bool:
        """Whether this parameter is required to use or not"""
        return self._json.get("required", False)
    @required.setter
    def required(self, value):
        if not isinstance(value, bool):
            raise WrongType("required", value, "bool") 
        self._json["required"] = value

    @property
    def choices(self) -> t.List[dict]:
        """Choices for string and int types for the user to pick from
        
        .. note::
    
            Choices are formated like this: ``[{"name": "name of the choice", "value": "the real value"}, ...]``
        """
        return self._json.get("choices")
    @choices.setter
    def choices(self, value):
        if isinstance(value, list):
            if all(isinstance(x, dict) for x in value):
                self._json["choices"] = value
            elif all(isinstance(x, tuple) for x in value):
                self._json["choices"] = [{"name": x[0], "value": x[1]} for x in value]
            else:
                raise WrongType("choices", value, ["List[dict]", "List[tuple]"])

    @property
    def options(self) -> SlashOptionCollection:
        """The parameters for the command.
            You can use the option's name (``.options["option name"]``) or the index of the option (``.options[index]``) to get an element.
        """
        return self._options
    @options.setter
    def options(self, options):
        if not isinstance(options, list) and not isinstance(options, SlashOptionCollection):
            raise WrongType("options", options, ["list", "SlashOptionCollection"])
        if all(isinstance(x, (SlashOption, dict)) for x in options):
            self._options = SlashOptionCollection(options)
        else:
            for i, x in enumerate(options):
                if not isinstance(x, SlashOption) and not isinstance(x, dict):
                    raise WrongType("options[" + str(i) + "]", x, ["dict", "SlashOption"])
        # set autocomplete generators
        self.__choice_generators__ = {
            x.name: x.choice_generator or self.__choice_generators__.get(x.name) for x in 
                [SlashOption._from_data(o) if isinstance(o, dict) else o for o in options]
            }
        
    @property
    def autocomplete(self) -> bool:
        """Whether the choices for this option should be autocompleted"""
        return self._json.get("autocomplete", False)
    @autocomplete.setter
    def autocomplete(self, value):
        self._json["autocomplete"] = value

    @property
    def focused(self) -> bool:
        """"Whether this option was focused while autocomplete"""
        return self._json.get("focused", False)
    
    @staticmethod
    def _from_data(data: dict, generator=None):
        return SlashOption(data["type"], data["name"], data["description"], data.get("required", False), data.get("choices"), data.get("autocomplete", False), 
            generator, data.get("options"), data.get("channel_types", []), data.get("min_value"), data.get("max_value")
        )

    def to_dict(self):
        return self._json | {"options": self._options.to_dict()}

class SlashPermission():
    """Permissions for a slash commannd
        
        Parameters
        ----------
        allowed: :class:`dict` | List[:class:`discord.Member` | :class:`discord.User` | :class:`discord.Role`], optional
            A list of ids, users or members that can use the command; default None
                Format: ``{"role_or_user_id": permission_type}]``


        forbidden: :class:`dict` | List[:class:`discord.Member` | :class:`discord.User` | :class:`discord.Role`], optional
            A list of ids, users or members that are forbidden to use the command; default None
    

        .. note::

            If you want to use a role id, the permission type has to be 1, and if you want to specify a user id, it has to be 2

            You can use ``SlashPermission.Role`` and ``SlashPermission.User`` instead

        """
    def __init__(self, allowed: t.Union[dict, list]=None, forbidden: t.Union[dict, list]=None) -> None:
        """Creates a new permission object for a slash command
        
        Examples
        ---------

        ```py
        SlashPermission(
            allowed={
                SlashPermission.User: [874357255829606402],
                SlashPermission.Role: [874357255829606402, 87435725582922303]
            }, forbidden={
                539459006847255232: SlashPermission.User,
                874357255829606402: SlashPermission.Role
            }
        )
        ```

        ```py
        SlashPermission(
            allowed=[
                await bot.fetch_user(539459006847254542),
                await bot.fetch_user(874357113864998922)
            ], forbidden={
                539459006847255232: SlashPermission.User,
                874357255829606402: SlashPermission.Role
            }
        )
        ```

        """
        
        self._json = []
        if allowed is not None:
            if isinstance(allowed, dict):
                for _id, _type in allowed.items():
                    if isinstance(_id, int) and isinstance(_type, (list, tuple)):
                        for x in _type:
                            self._json.append(
                                {
                                    "id": int(x),
                                    "type": _id,
                                    "permission": True
                                }
                            )
                    else:
                        self._json.append(
                            {
                                "id": int(_id),
                                "type": _type,
                                "permission": True
                            }
                        )
            elif isinstance(allowed, list):
                for t in allowed:
                    self._json.append({
                        "id": t.id,
                        "type": SlashPermission.USER if isinstance(t, (discord.User, discord.Member)) else SlashPermission.ROLE,
                        "permission": True
                    })
        if forbidden is not None:
            if isinstance(forbidden, dict):
                for _id, _type in forbidden.items():
                    if isinstance(_id, int) and isinstance(_type, (list, tuple)):
                        for x in _type:
                            self._json.append(
                                {
                                    "id": int(x),
                                    "type": _id,
                                    "permission": False
                                }
                            )
                    else:
                        self._json.append(
                            {
                                "id": int(_id),
                                "type": _type,
                                "permission": False
                            }
                        )
            elif isinstance(forbidden, list):
                for t in forbidden:
                    self._json.append({
                        "id": t.id,
                        "type": SlashPermission.USER if type(t) in [discord.User, discord.Member] else SlashPermission.ROLE,
                        "permission": False
                    })
            else:
                raise WrongType("forbidden", forbidden, ["Dict[int | str, int]", "List[discord.Member | discord.User | discord.Role]"])

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
    def __repr__(self) -> str:
        return f"<discord_ui.SlashPermission({self.to_dict()})>"
    
    @staticmethod
    def _from_data(data):
        perm = SlashPermission()
        perm._json = data
        return perm

    Role        =       ROLE        =   1
    """Permission type for a role"""
    User        =       USER        =   2
    """Permission type for a user"""

    @property
    def allowed(self) -> dict:
        return [x for x in self._json if x["permission"] == True]
    @property
    def forbidden(self) -> dict:
        return [x for x in self._json if x["permission"] == False]

class BaseCommand():
    __slots__ = ('__aliases__', '__sync__', '__auto_defer__', '__original_name__', '__choice_generators__', 
        '__subcommands__', '_state', '_id', '_options', '_json', 'callback', 'guild_ids',
        'guild_permissions', 'permissions', 'run'
    )
    def __init__(self, command_type, callback, name=None, description=None, options=None, guild_ids=None, default_permission=None, guild_permissions=None, state=None) -> None:
        self.__aliases__ = getattr(callback, "__aliases__", None)
        self.__sync__ = getattr(callback, "__sync__", True)
        self.__auto_defer__ = getattr(callback, "__auto_defer__", None)
        self.__choice_generators__ = {}
        self.__subcommands__ = {}
        self._state: ModifiedSlashState = state
        self._id: int = None # set later

        self._options = SlashOptionCollection() # set later
        self._json = {"type": getattr(command_type, "value", command_type)}

        self.options = options or []
        if callback is not None:
            if not inspect.iscoroutinefunction(callback):
                raise NoAsyncCallback(name)

            _params = inspect.signature(callback).parameters
            keys = list(_params.keys())
            callback_params = {
                x: _params[x] for i, x in enumerate(_params)
                    if i > (0 if keys[0] != "self" else 1)
            }
            has_kwargs = 4 in [x.kind for x in list(callback_params.values())]
            if self.options is not None:
                for op in self.options:
                    if callback_params.get(op.name) is None and has_kwargs:
                        continue
                    if callback_params.get(op.name) is None:
                        raise MissingOptionParameter(op.name)
                    param = callback_params[op.name]
                    if not op.required and param.default is param.empty:
                        raise OptionalOptionParameter(param.name)
            # if no options provided via options=[], check callback params instead
            if options == None and self.command_type is CommandType.Slash:
                _ops = []
                
                style = 0
                results = []
                doc = '\n'.join(inspect.getdoc(callback).split('\n')[1:]).removeprefix("\n") if inspect.getdoc(callback) != None else ""
                # check docstring pattern
                # style 1
                #
                #       Slashcommand description
                #       param1: `type`:
                #           description here
                #       param2: `type`:
                #           description here
                if len(re.findall(r'\w+: `?\w+`?:?\n.*', doc)) > 0:
                    results = re.findall(r'\w+: `?\w+`?:?\n.*', doc)
                    style = 1
                # style 2
                #
                #       Slashcommand description
                #       param1: description here
                #       param2: description here
                elif len(re.findall(r'\w+:\W.*', doc)) > 0:
                    results = re.findall(r'\w+:\W.*', doc)
                    style = 2
                # style 3
                #
                #       Slashcommand description
                #       param1 description
                #       param2 description
                elif len(doc.split("\n")) > 0:
                    results = doc.split("\n")
                    style = 3

                for _i, _name in enumerate(callback_params):
                    _val = callback_params.get(_name)
                    op_type = None
                    op_desc = None
                    if _val.annotation != _val.empty:
                        op_type = _val.annotation
                    elif _val.default != inspect._empty:
                        op_type = type(_val.default)
                    else: 
                        op_type = _name

                    if style != 0 and _i < len(results):
                        if style == 1:
                            res = results[_i]
                            _name = res.split(":")[0]
                            _type = res.split(":")[1].split("\n")[0].removesuffix(":").removeprefix(" ").replace("`", "").removeprefix(":class:").removeprefix("~")
                            op_desc = re.split(r'\s\s+', res.split("\n")[1])[1]
                            if OptionType.any_to_type(op_type) is None:
                                op_type = _type
                        elif style == 2:
                            res = results[_i]
                            _name = res.split(":")[0]
                            op_desc = ": ".join(res.split(": ")[1:])
                        elif style == 3:
                            res = results[_i]
                            if ":" in res:
                                op_desc = ':'.join(res.split(":")[1:]).removeprefix(" ")
                                _type = res.split(":")[0].replace("`", "")
                                if OptionType.any_to_type(op_type) is None:
                                    op_type = _type
                        
                    if OptionType.any_to_type(op_type) is None:
                        raise discord.errors.InvalidArgument("Could not find a matching option type for parameter '" + str(op_type) + "'")
                    _ops.append(SlashOption(op_type, _name, op_desc, required=_val.default == inspect._empty))
                self.options = _ops

        self.callback = callback
        """The callback for the command"""
        self.run = self.callback
        """Alias for ``.callback``"""
        self.name = name or (self.callback.__name__ if self.callback is not None else None)
        # Set the original name to the name once so if the name should be changed, this value still stays to what it is
        self.__original_name__ = self.name
        self.description = description or (
            inspect.getdoc(callback).split("\n")[0]
                if callback is not None and inspect.getdoc(callback) is not None 
            else None
        ) or "\u200b"
        self.default_permission = default_permission if default_permission is not None else True
        if guild_permissions is not None:
            for _id, perm in list(guild_permissions.items()):
                if not isinstance(_id, (str, int, discord.User, discord.Member, discord.Role)):
                    raise WrongType("guild_permissions key " + str(_id), _id, ["str", "int", "discord.User", "discord.Member", "discord.Role"])
                if not isinstance(perm, SlashPermission):
                    raise WrongType("guild_permission[" + ("'" if isinstance(_id, str) else "") + str(_id) + ("'" if isinstance(_id, str) else "") + "]", perm, "SlashPermission")
        
        self.guild_permissions: t.Dict[(t.Union[str, int], SlashPermission)] = guild_permissions
        self.permissions: SlashPermission = SlashPermission()
        """The current permissions for this command."""
        self.guild_ids: t.List[int] = [int(x) for x in guild_ids or []]
        """A list of guild ids where the command is available"""
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__.split('.')[-1]}({self.to_dict()})>"
    def __eq__(self, o: object) -> bool:
        if isinstance(o, dict):
            return (
                o.get('type') == self.command_type.value 
                and o.get('name') == self.name
                and o.get('description') == self.description
                and o.get('options', []) == (self.options if not self.has_subcommands else self._subcommands_to_options())
                and o.get("default_permission", True) == self.default_permission
            )
        elif isinstance(o, SlashCommand):
            return (
                o._json('type') == self._json["type"]
                and o.name == self.name
                and o.description == self.description
                and o.options == self.options
                and o.subcommands == self.subcommands
                and o.default_permission == self.default_permission
            )
        else:
            return False
    async def __call__(self, ctx, *args, **kwargs):
        return await self.callback(ctx, *args, **kwargs)

    @property
    def is_global(self) -> bool:
        """Whether this command is a global command"""
        return not self.guild_only
    @property
    def guild_only(self) -> bool:
        """Whether this command is limited to some guilds ``True`` or global ``False``"""
        return self.guild_ids != None and len(self.guild_ids) > 0
    @property
    def is_message_context(self) -> bool:
        """Wether is command is a message-context command"""
        return self.command_type is CommandType.Message
    @property
    def is_user_context(self) -> bool:
        """Whether this command is a user-context command"""
        return self.command_type is CommandType.User
    @property
    def is_chat_input(self) -> bool:
        """Whether this command is a chat-input command"""
        return self.command_type is CommandType.Slash
    @property
    def is_slash_command(self) -> bool:
        """
        Whether this command is a slashcommand
            Same as `.is_chat_input`
        """
        return self.is_chat_input
    @property
    def is_subcommand(self) -> bool:
        """Whether this command is a subcommand"""
        return self.is_chat_input and hasattr(self, "base_names")

    @property
    def original_name(self) -> str:
        """The original name for this command. Can be useful if aliases are used."""
        return self.__original_name__
    @property
    def aliases(self) -> t.List[str]:
        """The list of available aliases for this command"""
        return self.__aliases__
    @property
    def has_aliases(self) -> bool:
        """Whether this command has aliases"""
        return hasattr(self, "__aliases__") and self.__aliases__ is not None
    @property
    def is_alias(self) -> bool:
        """Whether this command is an alias to another command"""
        return self.__aliases__ is not None and self.name in self.__aliases__

    # region command
    @property
    def command_type(self) -> CommandType:
        """The type of the command"""
        return CommandType(self._json["type"])

    @property
    def name(self) -> str:
        """The name of the command"""
        return self._json["name"]
    @name.setter
    def name(self, value):
        if value is None:
            raise discord.errors.InvalidArgument("You have to specify a name")
        if not isinstance(value, str):
            raise WrongType("name", value, "str")
        if len(value) > 32 or len(value) < 1:
            raise InvalidLength("name", 1, 32)
        if self.command_type is CommandType.Slash:
            self._json["name"] = format_name(value)
        else:
            self._json["name"] = value
    @property
    def description(self) -> str:
        """The description of the command"""
        return self._json['description']
    @description.setter
    def description(self, value):
        if not isinstance(value, str):
            raise WrongType("description", value, "str")
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("description", 1, 100)
        self._json["description"] = value
    @property
    def options(self) -> SlashOptionCollection:
        """The parameters for the command.
            You can use the option's name (``.options["option name"]``) or the index of the option (``.options[index]``) to get an element.
        """
        return self._options
    @options.setter
    def options(self, options):
        if not isinstance(options, list) and not isinstance(options, SlashOptionCollection):
            raise WrongType("options", options, ["list", "SlashOptionCollection"])
        if all(isinstance(x, (SlashOption, dict)) for x in options):
            self._options = (
                SlashOptionCollection([(x if type(x) is SlashOption else SlashOption._from_data(x)) for x in options]) 
                    if not isinstance(options, SlashOptionCollection) else 
                options
            )
        else:
            for i, x in enumerate(options):
                if not isinstance(x, SlashOption) and not isinstance(x, dict):
                    raise WrongType("options[" + str(i) + "]", x, ["dict", "SlashOption"])
        # set autocomplete generators
        self.__choice_generators__ = {
            x.name: x.choice_generator or self.__choice_generators__.get(x.name) for x in 
                [SlashOption._from_data(o) if isinstance(o, dict) else o for o in options]
        }
    # endregion
    # region permissions
    @property
    def default_permission(self) -> t.Union[str, bool]:
        """
        Default permissions that a user needs to have in order to execute this command.
        If a bool was used, it will indicate whether this command can be used by everyone.
        """
        raw = self._json.get("default_permission", False)
        if isinstance(raw, str):
            return discord.Permissions(int(raw))
        return raw
    @default_permission.setter
    def default_permission(self, value):
        self._json["default_permission"] = str(value.value) if isinstance(value, discord.Permissions) else value
    # endregion

    @property
    def id(self) -> int:
        """The ID of the command.
            The ID is None until the command was synced with `Slash.commands.sync()`
        """
        return self._id
    @property
    def has_subcommands(self) -> bool:
        """Whether this command has subcommands"""
        return len(self.subcommands) > 0
    @property
    def subcommands(self) -> t.Dict[str, t.Union[SlashSubcommand, t.Dict[str, SlashSubcommand]]]:
        """List of references to :class:`Subcommand` instances of this base"""
        return self.__subcommands__
    
    async def update(self, guild_id=None):
        """Updates the api-command with the local changes
        
        guild_id: :class:`int`, optional:
            The guild id to which the command update should be made to
        """
        if self.guild_only:
            [await self._state.slash_http.edit_guild_command(self.id, guild, self.to_dict(), self.permissions.to_dict()) for guild in ([guild_id] if guild_id is not None else self.guild_ids)]
        else:
            await self._state.slash_http.edit_global_command(self.id, self.to_dict())
    async def edit(self, guild_id=None, **fields):
        """Edits this slashcommand and updates the changes in the api

        Parameters
        ----------
        guild_id: :class:`int`
            The guild where the command should be edited
        ``fields``: :class:`**dict`:
            The fields you want to edit (ex: ``name="new name"``)
        """

        for x in fields:
            setattr(self, x, fields[x])
        return await self.update(guild_id)
    async def delete(self, guild_id=None):
        """Deletes this command from the api
        
        Parameters
        ----------
        guild_id: :class:`int`, optional
            A guild id where the command should be deleted from. If passed, the command will only be deleted from this guild; default ``None``
        
        """
        if self.guild_only:
            if guild_id:
                await self._state.slash_http.delete_guild_command(self.id, guild_id)
            else:
                [await self._state.slash_http.delete_guild_command(self.id, guild) for guild in self.guild_ids]
        else:
            await self._state.slash_http.slash_http.delete_global_command(self.id)
    
    async def _fetch_id(self):
        try:
            return int(await self._state.slash_http.get_id(getattr(self, 'base_names', [self.name,])[0], self.guild_ids[0] if self.guild_only else None, self.command_type))
        except NoCommandFound:
            return None
    async def update_id(self):
        self._id = await self._fetch_id()

    def copy(self):
        """Returns a class copy of itself"""
        raise NotImplementedError()

    def _subcommands_to_options(self) -> t.List[SlashOption]:
        return [
                self.subcommands[x] 
                    if not isinstance(self.subcommands[x], dict) else 
                SlashOption(OptionType.SUB_COMMAND_GROUP, x, options=[
                    self.subcommands[x][y].to_option() for y in self.subcommands[x]
                ])
                
                for x in self.subcommands
            ]
    def to_dict(self):
        return self._json | {
            "options": (
                # if no subcommands are present use normal options
                self._options.to_dict() 
                    if not self.has_subcommands
                else [x.to_dict() for x in self._subcommands_to_options()]
            )
        }

class SlashCommand(BaseCommand):
    """A basic slash command
        
    Parameters
    ----------
    callback: :class:`function`
        The callback function
    name: :class:`str`
        1-32 characters long name
            If name is not passed, the name of the callback function will be used; default None
            
        .. important::

            The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)

    description: :class:`str`, optional
        1-100 character description of the command; default None
            If description is not passed, the docstring description of the callback function is used. 
            If no docstring exists, the name of the command will be used
    options: List[:class:`~SlashOptions`], optional
        Parameters for the command; default None
    choices: List[:class:`tuple`] | List[:class:`dict`], optional
        Choices for string and int types for the user to pick from; default None
    guild_ids: :class:`str` | :class:`int`, optional
        A list of guild ids where the command is available; default None
    default_permission: :class:`bool` | :class:`discord.Permissions`, optional
        Permissions that a user needs to have in order to execute the command, default ``True``. 
            If a bool was passed, it will indicate whether all users can use the command (``True``) or not (``False``)
    guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
        The permissions for the command in guilds
            Format: ``{"guild_id": SlashPermission}``
    """
    def __init__(self, callback, name=None, description=None, options=None, guild_ids=None, default_permission=None, guild_permissions=None, state=None) -> None:
        """
        Creates a new base slash command
        
        Example

        ```py
        async def my_function(command, parameter=None):
            pass

        SlashCommand(callback=my_function, name="hello_world", description="This is a test command",
            options=[
                SlashOption(str, name="parameter", description="this is a parameter", choices=[("choice 1", 1)])
            ], guild_ids=[785567635802816595], default_permission=False,
            guild_permissions={
                785567635802816595: SlashPermission(allowed={"539459006847254542": SlashPermission.USER})
            }
        )
        ```
        """
        BaseCommand.__init__(
            self, CommandType.Slash, callback, 
            name, description, 
            options=options, guild_ids=guild_ids, 
            default_permission=default_permission, guild_permissions=guild_permissions, 
            state=state
        )
    def __getitem__(self, index) -> SlashSubcommand:
        # enable `[key]` for subcommands
        return self.subcommands[index]
    def __setitem__(self, index, value):
        self.subcommands[index] = value
        if isinstance(value, dict):
            for x in value:
                if self.options.get(index) is None:
                    self.options[index] = SlashOption(OptionType.SUB_COMMAND_GROUP, index)
                self.options[index].options[value[x].name] = value[x].to_option()
        else:
            self.options[index] = value.to_option()
    def __delitem__(self, index):
        del self.subcommands[index]
        del self.options[index]

    def copy(self) -> SlashCommand:
        c = self.__class__(self.callback, self.name, self.description, self.options, self.guild_ids, self.default_permission, self.guild_permissions, self._state.slash_http)
        for x in self.__slots__:
            setattr(c, x, getattr(self, x))
        return c
    def add_subcommand(self, sub: SlashSubcommand):
        """Adds a subcommand to this SlashCommand.

        Parameters
        ----------
        sub: :class:`SlashSubcommand`
            The subcommand you want to add
        
        """
        sub._base = self
        if len(sub.base_names) > 1:
            if self.__subcommands__.get(sub.base_names[1]) is None:
                self.__subcommands__[sub.base_names[1]] = {}
            self.__subcommands__[sub.base_names[1]][sub.name] = sub
        else:
            self.__subcommands__[sub.name] = sub

    @staticmethod
    def _from_data(data, permissions=None, state=None, target_guild=None, guild_ids=None):
        return SlashCommand(None, data["name"], data["description"], data.get("options"), guild_ids, 
            data.get("default_permission", True), {target_guild: SlashPermission._from_data(permissions)} if permissions else None, state
        )
    @staticmethod
    async def _from_api(id, slash_http, guild_id=None, guild_ids=None) -> SlashCommand:
        api = await slash_http.fetch_command(id, guild_id)
        permissions = None
        if guild_id:
            permissions = await slash_http.get_command_permissions(id, guild_id)
        return SlashCommand._from_data(api, permissions, slash_http, guild_id, guild_ids)
   
class SlashSubcommand(BaseCommand):
    __slots__ = BaseCommand.__slots__ + ('base_names', '_base')

    def __init__(self, callback, base_names, name, description=None, options=None, guild_ids=None, default_permission=None, guild_permissions=None, state=None) -> None:
        self._base = None # a base instance shared with all subcommands
        if isinstance(base_names, str):
            base_names = [base_names]
        if len(base_names) > 2:
            raise discord.errors.InvalidArgument("subcommand groups are currently limited to 2 bases")
        if any([len(x) > 32 or len(x) < 1 for x in base_names]):
            raise InvalidLength("base_names", 1, 32)
        self.base_names = [format_name(x) for x in base_names]
        BaseCommand.__init__(
            self, CommandType.Slash, callback, 
            name, description, options=options, guild_ids=guild_ids, 
            default_permission=default_permission, guild_permissions=guild_permissions,
            state=state
        )
    async def fetch_base(self, guild_id=None, overwrite_base=True) -> SlashCommand:
        """Fetches the base command from the api
        
        `guild_id`: :class:`int`, optional
            The guild from which the base should be fetched
        `overwrite_base`: :class:`bool`, optional
            Whether `self.base` should be updated to the newly fetched base
        """
        command: SlashCommand = await SlashCommand._from_api(
            self._id, self._state.slash_http, guild_id or self.guild_ids[0] if self.guild_only else None, 
            guild_ids=self.guild_ids
        )
        command.guild_permissions = self.guild_permissions
        if overwrite_base:
            self._base = command
        return command
    @property
    def id(self) -> int:
        return self.base.id
    @property
    def base(self) -> SlashCommand:
        """A shared :class:`~SlashCommand` instance for all subcommands which holds information about the base command"""
        return self._base
    
    @property
    def base_name(self):
        """The name of the base. Same as ``.base.name``"""
        return self.base.name
    @base_name.setter
    def base_name(self, value):
        self.base_names[0] = format_name(value)
        self.base.name = format_name(value)
    @property
    def group_name(self) -> t.Optional[str]:
        """The name of the parent command group.
            If your command is ``/my nice command``, ``nice`` would be returned
        """
        return self.base_names[1] if len(self.base_names) > 1 else None
    @group_name.setter
    def group_name(self, value):
        if self.group_name is not None:
            c = self.base[self.group_name].copy()
            del self.base[self.group_name]
            self.base_names[1] = value
            self.base[value] = c
        else:
            self.base_names.append(value)
            del self.base[self.name]
            if not self.base.subcommands.get(value):
                self.base[value] = {}
            self.base[value][self.name] = self

    async def update(self, guild_id=None):
        for guild in [guild_id] if guild_id is not None else self.guild_ids:
            base = self.base or await self.fetch_base(guild)
            base.guild_ids = self.guild_ids
            base._state = self._state

            if len(self.base_names) > 1:
                if base.__subcommands__.get(self.base_names[1]) is None:
                    base.__subcommands__[self.base_names[1]] = {}
                if base.options.get(self.base_names[1]) is None:
                    base.options[self.base_names[1]] = SlashOption(OptionType.SUB_COMMAND_GROUP, self.name)
                base.options[self.base_names[1]].options[self.name] = self.to_option()
                base.__subcommands__[self.base_names[1]][self.name] = self
            else:
                base.options[self.name] = self.to_option()
                base.__subcommands__[self.name] = self
            return await base.update(guild)
    def to_option(self) -> SlashOption:
        return SlashOption(OptionType.SUB_COMMAND, self.name, self.description, options=self.options or None, required=False)
    def to_dict(self):
        return self.to_option().to_dict()
    def copy(self) -> SlashSubcommand:
        c = self.__class__(self.callback, self.base_names, self.name, self.description, self.options, self.guild_ids, self.default_permission, self.guild_permissions, self._state.slash_http)
        for x in self.__slots__:
            setattr(c, x, getattr(self, x))
        return c

class ContextCommand(BaseCommand):
    def __init__(self, context_type, callback, name=None, guild_ids=None, default_permission=True, guild_permissions=None, state=None) -> None:
        if callback is not None:
            callback_params = inspect.signature(callback).parameters
            if len(callback_params) < 2:
                raise CallbackMissingContextCommandParameters()
        BaseCommand.__init__(self, context_type, callback, name=name, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions, state=state)

    @property
    def description(self) -> str:
        """This field is not supported for context-commands"""
        return ""
    @description.setter
    def description(self, _):
        pass
    @property
    def options(self) -> list:
        """This field is not supported for context-commands"""
        return self._options
    @options.setter
    def options(self, _):
        pass

class UserCommand(ContextCommand):
    def __init__(self, callback, name=None, guild_ids=None, default_permission=True, guild_permissions=None, state=None) -> None:
        ContextCommand.__init__(self, CommandType.User, callback, name, guild_ids, default_permission, guild_permissions, state)
    def copy(self) -> UserCommand:
        c = self.__class__(self.callback, self.name, self.guild_ids, self.default_permission, self.guild_permissions, self._state.slash_http)
        for x in self.__slots__:
            setattr(c, x, getattr(self, x))
        return c

class MessageCommand(ContextCommand):
    def __init__(self, callback, name=None, guild_ids=None, default_permission=True, guild_permissions=None, state=None) -> None:
        ContextCommand.__init__(self, CommandType.Message, callback, name, guild_ids, default_permission, guild_permissions, state)
    def copy(self) -> MessageCommand:
        c = self.__class__(self.callback, self.name, self.guild_ids, self.default_permission, self.guild_permissions, self._state.slash_http)
        for x in self.__slots__:
            setattr(c, x, getattr(self, x))
        return c



class APITools():
    def __init__(self, client) -> None:
        self._discord = client

    async def get_commands(self) -> t.List[dict]:
        return await self.get_global_commands() + await self.get_all_guild_commands()
    async def get_global_commands(self) -> t.List[dict]:
        return await self._discord._connection.slash_http.get_global_commands()
    async def get_global_command(self, name, typ) -> t.Union[dict, None]:
        for x in await self.get_global_commands():
            if x["name"] == name and x["type"] == typ:
                return x
    async def get_all_guild_commands(self):
        commands = []
        async for x in self._discord.fetch_guilds():
            try:
                commands += await self._discord._connection.slash_http.get_guild_commands(x.id)
            except discord.Forbidden:
                continue
        return commands
    async def get_guild_commands(self, guild_id: str) -> t.List[dict]:
        return await self._discord._connection.slash_http.get_guild_commands(guild_id)
    async def get_guild_command(self, name, typ, guild_id) -> t.Union[dict, None]:
        # returns all commands in a guild
        for x in await self.get_guild_commands(guild_id):
            if hasattr(typ, "value"):
                typ = typ.value
            if x["name"] == name and x["type"] == typ:
                return x

command = t.Union[SlashCommand, SlashSubcommand, MessageCommand, UserCommand]
class _CommandList(t.TypedDict):
    Slash: t.Dict[str, command]
    User: t.Dict[str, command]
    Message: t.Dict[str, command]
CommandCacheList = t.Dict[str, _CommandList]

class CommandCache():
    def __init__(self, client, commands: t.List[command] = []) -> None:
        self.api = APITools(client)
        self._client: Bot = client
        self._cache: CommandCacheList = {}
        self._raw_cache = {}    # dict with commands saved together with their id
        self._state: ModifiedSlashState = self._client._connection
        # setup cache
        self.clear()
        # loads the commands into the cache
        self.load(commands)
    def __repr__(self):
        return f"<{self.__class__.__name__}{self._cache}>"
    def __getitem__(self, index) -> t.Dict[str, t.Union[ command, t.Dict[str, t.Union[ command, t.Dict[str, t.Union[ command, dict ]] ]] ]]:
        """
        Special keys
        -------------

        Shortcut for subkeying
        ```py
        x:y:z -> [x][y][z]
        ```

        - - -

        Shortcut for filtering
        ```py
        !x!y -> {key: ... for key in dict if key not in ['x', 'y']}
        ```
        
        Note that this will return a copy of the original dict, if we want to acces objects from the original dict, we can use a simple workaround:
        ```py
        for key in self["!illegal_key"]:
            self[key] # this will grant you acces to the object from the original dict
        ```
        """
        # subkeying or whatever this is called
        if ":" in index:
            keys = index.split(":")
            cur = self._cache[keys.pop(0)]
            while True:
                if len(keys) == 0:
                    return cur
                if cur is None or not isinstance(cur, dict):
                    raise KeyError(f"No key with name '{keys[-1]}'")
                cur = cur.get(keys.pop(0))
        # filtering
        elif "!" in index:
            black_keys = index.split("!")
            return {key: self._cache[key] for key in self._cache if key not in black_keys}
        else:
            return self._cache[index]
    def __setitem__(self, index, value):
        """
        Special keys
        -------------

        Shortcut for setting subkeys
        ```py
        x:y:z = ... -> [x][y][z] = ...
        ```

        - - -


        Shortcut for filtered setting
        ```py
        !x!y = ... -> for key in self:
                          if key not in ["x", "y"]:
                              self[key] = ...
        ```
        
        Sets everything to the value except the "illegal keys"
        """
        # subkeying?
        if ":" in index:
            keys = index.split(":")
            cur = self._cache[keys.pop(0)]
            while True:
                if len(keys) == 0:
                    cur = value
                    break
                if cur is None or not isinstance(cur, dict):
                    raise KeyError(f"No key with name '{keys[-1]}'")
                cur = cur.get(keys.pop(0))
        # set everything to value except
        if "!" in index:
            black_keys = index.split("!")
            for x in self:
                if x not in black_keys:
                    self[x] = value
        else:
            self._cache[index] = value
    def __delitem__(self, index):
        if ":" in index:
            keys = index.split(":")
            cur = self._cache[keys.pop(0)]
            while True:
                if len(keys) == 0:
                    del cur
                    break
                if cur is None or not isinstance(cur, dict):
                    raise KeyError(f"No key with name '{keys[-1]}'")
                cur = cur.get(keys.pop(0))
        else:
            del self._cache[index]
    def __iter__(self):
        return iter(self._cache)
    def __contains__(self, command: command):
        type_key = str(command.command_type)
        if command.is_global:
            if command.is_subcommand:
                if self["globals"].get(type_key) is None:
                    return False
                if self["globals"][type_key].get(command.base_name) is None:
                    return False
                if len(command.base_names) > 1:
                    if self["globals"][type_key][command.base_name].subcommands.get(command.group_name) is None:
                        return False
                    if self["globals"][type_key][command.base_name][command.group_name].get(command.name) is None:
                        return False
                    return True
                return self["globals"][type_key][command.base_name].subcommands.get(command.name) is not None
            if self["globals"].get(type_key) is None:
                return False
            return self["globals"][type_key].get(command.name) is not None
        
        # check for every guild_id
        for g in command.guild_ids:
            guild = str(g)
            if self.get(guild) is None:
                return False
            if self[guild].get(type_key) is None:
                return False
            if command.is_subcommand:
                if self[guild][type_key].get(command.base_names[0]) is None:
                    return False
                # if more than one base
                if len(command.base_names) > 1:
                    if self[guild][type_key][command.base_names[0]].subcommands.get(command.base_names[1]) is None:
                        return False
                    if self[guild][type_key][command.base_names[0]][command.base_names[1]].get(command.name) is None:
                        return False
                # one base only
                else:
                    if self[guild][type_key][command.base_names[0]].subcommands.get(command.name) is not None:
                        return False
            else:
                if self[guild][type_key].get(command.name) is None:
                    return False 
        return True
    def __eq__(self, object):
        if isinstance(object, self.__class__):
            return len(object._cache) == len(self._cache) and object._cache == self._cache
        return False
    
    async def _on_sync(self):
        ...
    def on_sync(self, method):
        """Decorator for a method that should be called when the commands were synced
        
        Usage
        ------

        .. code-block::

            @Slash.commands.on_sync
            async def on_commands_sync():
                ...
        """
        if not asyncio.iscoroutinefunction(method):
            raise BadArgument("on_sync has to be async")
        self._on_sync = method
        

    # region overloading def load(self, cache)
    @t.overload
    def load(self, cache: t.List[command]) -> CommandCache:
        """Loads some commands into the cache
        
        Parameters
        -----------

        cache: List[:class:`command`]:
            The commands that should be loaded into this cache instance

        Returns
        --------
        :class:`CommandCache`:
            The own instance with the commands loaded into it
        """
    ...
    @t.overload
    def load(self, cache: t.Union[CommandCacheList, dict]) -> CommandCache:
        """Replaces the own raw cache with the passed cache
        
        Parameters
        -----------

        cache: :class:`CommandCacheList` | :class:`dict`:
            The raw cache which should be loaded into this cache instance

        Returns
        --------
        :class:`CommandCache`:
            The own instance with the cache loaded into it
        """
        ...
    # endregion
    def load(self, cache):
        # application commands
        if isinstance(cache, list):
            for x in cache:
                self._add(x)
            return self
        # raw cache
        self._cache = cache
        return self
    def clear(self):
        """Clears the cache and makes it empty"""
        self._cache = {
            "globals": {
                str(CommandType.Slash): {},
                str(CommandType.User): {},
                str(CommandType.Message): {}
            }
        }
        return self
    def copy(self):
        return self.__class__(self._client).load(self._cache)
    def _add(self, command: command):
        type_key = str(command.command_type)
        if command.is_global:
            if command.is_subcommand:
                base = self["globals"][type_key].get(command.base_names[0])
                if base is None:
                    base = SlashCommand(None, command.base_names[0], 
                        guild_permissions=command.guild_permissions, default_permission=command.default_permission
                    )
                base.add_subcommand(command)
                self["globals"][type_key][base.name] = base  
            else:
                self["globals"][type_key][command.name] = command
        else:
            for guild_id in command.guild_ids:
                guild = str(guild_id)
                if self.get(guild) is None:
                    self[guild] = {}
                if self[guild].get(type_key) is None:
                    self[guild][type_key] = {}
                if command.is_subcommand:
                    # is subcommand
                    base = self[guild][type_key].get(command.base_names[0])
                    if base is None:
                        base = SlashCommand(None, command.base_names[0],
                            guild_permissions=command.guild_permissions, default_permission=command.default_permission
                        )
                    base.add_subcommand(command)
                    self[guild][type_key][base.name] = base  
                else:
                    self[guild][type_key][command.name] = command
        return self
    def add(self, base: C) -> C:
        """Adds a new command to the cache and returns it. Same as :meth:`.append()`
        
        Parameters
        ----------
        base: :class:`BaseCommand`
            The command that should be added to the cache
        """
        return self.append(base)
    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default
    def append(self, base: C, is_base=False) -> C:
        if base.has_aliases and is_base is False:
            for a in base.__aliases__:
                cur = base.copy()
                cur.name = a
                self.append(cur, is_base=True)
        self._add(base)
        return base
    def remove(self, base: SlashCommand):
        """Removes a SlashCommand from the cache
        
        base: :class:`SlashCommand`
            The command that should be removeed
        """
        key_type = str(base.command_type)
        name = base.name if not base.is_subcommand else base.base_names[0]
        if base.is_global:
            keys = ["global"]
        else:
            keys = [str(x) for x in base.guild_ids]
        for k in keys:
            if self[k].get(key_type) is None:
                return
            if self[k][key_type].get(name) is None:
                return
            if not base.is_subcommand:
                del self[k][key_type][name]
                return
            if len(base.base_names) > 1:
                del self[k][key_type][name][base.base_names[1]][base.name]
                return
            else:
                del self[k][key_type][name][base.name]
                return
    async def sync(self, delete_unused=False):
        """Updates the api with the commands in the cache
        
        delete_unused: :class:`bool`, optional
            Whether commands that are not included in this cache should be deleted; default False
        """
        http = self._state.slash_http
        self._raw_cache = {}
        
        for ct in self["globals"]:
            for base_name in self["globals"][ct]:
                base = self["globals"][ct][base_name]
                new_command = None # variable to store the new command data
                api_command = await self.api.get_global_command(base.name, base._json["type"])
                if api_command is None:
                    new_command = await http.create_global_command(base.to_dict())
                else:
                    if api_command != base:
                        new_command = await http.edit_global_command(api_command["id"], base.to_dict())
                # directly set the id of the command so no extra request is needed
                base._id = new_command["id"] if new_command else api_command["id"]
                self._raw_cache[base._id] = base

        # self["!globals"] returns a copy of a filtered dict but since we will be only using the 
        # copy's key and acces the original self dict, there won't be any problems
        # 
        # for each guild
        for guild in self["!globals"]:
            # acces original dict with filtered keys
            for ct in self[guild]:
                for base_name in self[guild][ct]:
                    base = self[guild][ct][base_name]
                    new_command = None # variable to store the new command data
                    api_command = await self.api.get_guild_command(base.name, base.command_type, guild)
                    if api_command:
                        # get permissions for the command
                        api_permissions = await http.get_command_permissions(api_command["id"], guild)
                    global_command = await self.api.get_global_command(base.name, base.command_type)
                    # If no command in that guild or a global one was found
                    if api_command is None or global_command is not None:
                        # Check global commands
                        # allow both global and guild commands to exist
                        # region ignore
                        # If global command exists, it will be deleted
                        # if global_command is not None:
                        #     await http.delete_global_command(global_command["id"])
                        # endregion
                        new_command = await http.create_guild_command(base.to_dict(), guild, base.permissions.to_dict())
                    elif api_command != base:
                        new_command = await http.edit_guild_command(api_command["id"], guild, base.to_dict(), base.permissions.to_dict())
                    elif api_permissions != base.permissions:
                        await http.update_command_permissions(guild, api_command["id"], base.permissions.to_dict())
                    base._id = new_command["id"] if new_command else api_command["id"]
                    self._raw_cache[base._id] = base

        if delete_unused is True:
            for global_command in await self.api.get_global_commands():
                key_type = str(CommandType(global_command["type"]))
                # command of a type we didn't register
                if self["globals"].get(key_type) is None:
                    await http.delete_global_command(global_command["id"])
                    continue
                # command with a name we didn't register
                if self["globals"][key_type].get(global_command["name"]) is None:
                    await http.delete_global_command(global_command["id"])
                    continue
            for guild in [str(x.id) async for x in self._client.fetch_guilds()]:
                for guild_command in await self.api.get_guild_commands(guild):
                    # command in a guild we didn't register
                    if self.get(guild) is None:
                        await http.delete_guild_command(guild_command["id"], guild)
                        continue
                    key_type = str(CommandType(guild_command["type"]))
                    # command of a type we didn't register
                    if self[guild].get(key_type) is None:
                        await http.delete_guild_command(guild_command["id"], guild)
                        continue
                    # command with a name we didn't register
                    if self[guild][key_type].get(guild_command["name"]) is None:
                        await http.delete_guild_command(guild_command["id"], guild)
                        continue
        
        self._client.dispatch("commands_synced")
        await self._on_sync()
    async def nuke(self, globals=True, guilds=All):
        """
        Deletes all commands registered in the api of this bot
        
        Parameters
        ----------
        globals: :class:`bool`, optional
            Whether all global commands should be deleted; default True
        guild: List[:class:`int`], optional
            The guild ids where commands should be deleted; default All
        
        Usage
        -----

        delete all commands
        >>> await commands.nuke()

        delete only global commands
        >>> await commands.nuke(guilds=None)
    
        delete only guild commands
        >>> await commands.nuke(globals=False)
    
        delete commands in specific guilds
        >>> await commands.nuke(globals=False, guilds=[814473329325899787])
        """
        if guilds is All:
            guilds = self["!globals"]
        if guilds is None:
            guilds = []
        if globals is True:
            await self._state.slash_http.delete_global_commands()
        for id in guilds:
            await self._state.slash_http.delete_guild_commands(id)
        

    def get_command_for(self, interaction: InteractionPayload):
        command = self._raw_cache.get(interaction["data"]["id"])
        if command is None:
            return

        # is subcommand
        if interaction["data"].get("options") is not None and interaction["data"]["options"][0]["type"] in [OptionType.SUB_COMMAND, OptionType.SUB_COMMAND_GROUP]:
            try:
                base_one = command[interaction["data"]["options"][0]["name"]]
            except KeyError:
                return
            # if command has only one base
            if interaction["data"]["options"][0]["type"] == OptionType.SUB_COMMAND:
                # return the subcommand
                return base_one
            elif interaction["data"]["options"][0]["type"] == OptionType.SUB_COMMAND_GROUP:
                try:
                    return base_one[interaction["data"]["options"][0]["options"][0]["name"]]
                except KeyError:
                    return None
            
        return command
    def get_commands(self, *, all=True, guilds=[], **keys):
        guilds = [str(x) for x in guilds]
        commands = {}
        for x in self._cache:
            if x in keys or str(x) in guilds or all:
                commands[x] = self._cache.get(x)
        return commands
    def filter_commands(self, command_type) -> t.Dict[str, command]:
        commands = {}
        for x in self._cache:
            # multiple types
            if isinstance(command_type, (list, tuple)):
                for ct in command_type:
                    if commands.get(x) is None:
                        commands[x] = {}
                    if commands[x].get(str(ct)) is None:
                        commands[x][str(ct)] = {}
                    if len(self._cache[x].get(str(ct), {})) > 0:
                        commands[x][str(ct)] = self._cache[x].get(str(ct), {})
            # single type
            elif self._cache[x].get(str(command_type)):
                commands[x] = self._cache[x].get(str(command_type))
        return commands

    @property
    def all(self) -> CommandCacheList:
        """All commands"""
        return self._cache
    @property
    def globals(self) -> t.Dict[str, command]:
        """All global commands"""
        return self["globals"]
    @property
    def chat_commands(self) -> t.Dict[str, SlashCommand]:
        """All chat commands (slash commands)"""
        return self.filter_commands(CommandType.Slash)
    @property
    def context_commands(self) -> t.Dict[str, t.Union[MessageCommand, UserCommand]]:
        """All context commands (message commands, user commands)"""
        return self.filter_commands((CommandType.Message, CommandType.User))
    @property
    def subcommands(self) -> t.Dict[str, t.Union[SlashSubcommand, t.Dict[str, SlashSubcommand]]]:
        """All subcommands"""
        filter = [list(x.values()) for x in list(self.filter_commands(CommandType.Slash).values())]
        return [z for a in [y.subcommands for x in filter for y in x] for z in a]