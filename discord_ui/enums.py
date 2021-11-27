from __future__ import annotations

import discord

import inspect
from enum import IntEnum
from typing import Union

Channel = Union[
    discord.TextChannel, 
    discord.VoiceChannel, 
    discord.StageChannel,
    discord.StoreChannel,
    discord.CategoryChannel, 
    discord.StageChannel,
]
"""Typing object for all possible channel types, only for type hinting"""

_Mentionable = Union[
    Channel,
    discord.Member,
    discord.Role
]
"""Typing object for possible returned classes in :class:`~OptionType.Mentionable`, only for type hinting"""
class __Mentionable:
    """Empty class for comparing a class to `Mentionable`"""
    pass

Mentionable: _Mentionable = __Mentionable
"""Type for a SlashOption with type of :class:`Mentionable`

Usage:
~~~~~~

.. code-block::

    @ui.slash.command(options=[SlashOption(Mentionable, "an_option")])
    async def test(ctx, an_option):
        ...

or

.. code-block::

    @ui.slash.command()
    async def test(ctx, an_option: Mentionable): # OptionType of 'an_option' is now Mentionable
        ... 
"""

class BaseIntEnum(IntEnum):
    def __str__(self) -> str:
        return self.name


class ButtonStyle(BaseIntEnum):
    Blurple     =     Primary           = 1
    Grey        =     Secondary         = 2
    Green       =     Succes            = 3
    Red         =     Destructive       = 4
    URL         =     Link              = 5

    @classmethod
    def getColor(cls, s):
        if isinstance(s, int):
            return cls(s)
        if isinstance(s, cls):
            return s
        s = s.lower()
        if s in ("blurple", "primary"):
            return cls.Blurple
        if s in ("grey", "gray", "secondary"):
            return cls.Grey
        if s in ("green", "succes"):
            return cls.Green
        if s in ("red", "danger"):
            return cls.Red

class CommandType(BaseIntEnum):
    Slash       =              1
    """Chat-input command"""
    User        =              2
    """User-context command"""
    Message     =              3
    """Message-context command"""

    @staticmethod
    def from_string(typ):
        if isinstance(typ, str):
            if typ.lower() == "slash":
                return CommandType.Slash
            elif typ.lower() == "user":
                return CommandType.User
            elif typ.lower() == "message":
                return CommandType.Message
        elif isinstance(typ, CommandType):
            return typ
        else:
            return CommandType(typ)
    def __str__(self):
        return self.name
class ComponentType(BaseIntEnum):
    Action_row      =           1
    Button          =           2
    Select          =           3
class OptionType(BaseIntEnum):
    Subcommand              =          SUB_COMMAND          =           1
    Subcommand_group        =          SUB_COMMAND_GROUP    =           2
    String                  =          STRING               =           3
    Integer                 =          INTEGER              =           4
    """Any integer between -2^53 and 2^53"""
    Boolean    =   bool     =          BOOLEAN              =  BOOL  =  5
    Member     =   user     =          MEMBER               =  USER  =  6
    Channel                 =          CHANNEL              =           7
    """Includes all channel types + categories"""
    Role                    =          ROLE                 =           8
    Mentionable             =          MENTIONABLE          =           9
    """Includes users and roles"""
    Float      =   Number   =          FLOAT                =  NUMBER = 10
    """Any double between -2^53 and 2^53"""

    @classmethod
    def any_to_type(cls, whatever) -> OptionType:
        """Converts something to a option type if possible"""
        if isinstance(whatever, int) and whatever in range(1, 11):
            return whatever
        if inspect.isclass(whatever):
            if whatever is str:
                return cls.String
            if whatever is int:
                return cls.Integer
            if whatever is bool:
                return cls.Boolean
            if whatever in [discord.User, discord.Member]:
                return cls.Member
            if whatever in [discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.CategoryChannel]:
                return cls.Channel
            if whatever is discord.Role:
                return cls.Role
            if whatever is Mentionable:
                return cls.Mentionable
            if whatever is float:
                return cls.Float
        if isinstance(whatever, str):
            whatever = whatever.lower()
            if whatever in ["str", "string", "text", "char[]"]:
                return cls.String
            if whatever in ["int", "integer", "number"]:
                return cls.Integer
            if whatever in ["bool", "boolean"]:
                return cls.Boolean
            if whatever in ["user", "discord.user", "member", "discord.member", "usr", "mbr"]:
                return cls.Member
            if whatever in ["channel"]:
                return cls.Channel
            if whatever in ["role", "discord.role"]:
                return cls.Role
            if whatever in ["mentionable", "mention"]:
                return cls.Mentionable
            if whatever in ["float", "floating", "floating number", "f"]:
                return cls.Float
        if isinstance(whatever, list):
            ret = cls.Channel
            ret.__channel_types__ = whatever
            return ret
        if isinstance(whatever, range):
            if float in [cls.any_to_type(whatever.start), cls.any_to_type(whatever.stop)]:
                _type = cls.Float
            else:
                _type = cls.Integer
            _type.__min__, _type.__max__ = whatever.start, whatever.stop
            return _type
class Limits:
    """Limits for OptionType Parameters"""
    class Numeric:
        min, max = -2**53, 2**53

class InteractionResponseType(BaseIntEnum):
    Pong                        =       1
    """respond to ping"""
    # Ack                         =       2  # deprecated
    # """``deprecated`` acknowledge that message was received"""
    # Channel_message             =       3  # deprecated
    # """``deprecated`` respond with message"""
    Channel_message             =       4
    """
    respond with message
        `command` | `component`"""
    Deferred_channel_message    =       5
    """
    defer interaction
        `command | component`"""
    Deferred_message_update     =       6
    """
    update message later
        `component`"""
    Message_update              =       7
    """
    update message for component
        `component`"""
    Autocomplete_result         =       8
    """
    respond with auto-complete choices
        `command`"""
