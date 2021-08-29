from .types import AdditionalType, OptionType
from ..tools import get, setup_logger
from ..errors import CouldNotParse

import discord
from discord.enums import ChannelType

import typing

logging = setup_logger(__name__)

class ParseMethod:
    """Methods of how the interaction argument data should be treated

    - ``RAW``       [0]
        Returns the raw value which was received
    - ``RESOLVE``   [1]
        Uses the resolved data which will be delivered together with the received interaction
    - ``FETCH``     [2]
        Fetches all the ids of the received data with an api call
    - ``CACHE``     [3]
        Uses the internal bot cache to get the data 
    
    .. warning::

        The cache method uses the `.get_guild`, `.get_channel`... methods, which needs to have some intents enabled 
        (`more information <https://discordpy.readthedocs.io/en/latest/intents.html?highlight=intents>`__)

    - ``AUTO``      [4]
        This will try all methods beginning (RESOLVE, FETCH, CACHE, RAW) and changes to the next method whenever an exception occurs
    """
    RAW         =       Raw         =       0
    RESOLVE     =       Resolve     =       1
    FETCH       =       Fetch       =       2
    CACHE       =       Cache       =       3
    AUTO        =       Auto        =       4

def format_name(value):
    return str(value).lower().replace(" ", "-")

def resolve(data, _state):
    resolved = {}
    for x in data["data"]["resolved"]:
        if x == "members":
            resolved["members"] = {}
            for m_id in data["data"]["resolved"]["members"]:
                member_data = data["data"]["resolved"]["members"][m_id]
                member_data["user"] = data["data"]["resolved"]["users"][m_id]
                resolved["members"][m_id] = discord.Member(data=member_data, guild=_state._get_guild(data["guild_id"]), state=_state)
        elif x == "messages":
            resolved["messages"] = {}
            for message_id in data["data"]["resolved"]["messages"]:
                message_data = data["data"]["resolved"]["messages"][message_id]
                resolved["messages"][message_id] = discord.Message(data=message_data, channel=_state._get_channel(data["channel_id"]), state=_state)
        elif x == "channels":
            resolved["channels"] = {}
            for channel_id in data["data"]["resolved"]["channels"]:
                channel_data = data["data"]["resolved"]["channels"][channel_id]

                guild = _state._get_guild(data["guild_id"])
                channel = None
                if ChannelType(channel_data["type"]) is ChannelType.text:
                    channel = discord.TextChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.voice:
                    channel = discord.VoiceChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.category:
                    channel = discord.CategoryChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.group:
                    channel = discord.GroupChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.news:
                    channel = discord.NewsChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.private:
                    channel = discord.DMChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.store:
                    channel = discord.StoreChannel(data=channel_data, guild=guild, state=_state)
                elif ChannelType(channel_data["type"]) is ChannelType.stage_voice:
                    channel = discord.StageChannel(data=channel_data, guild=guild, state=_state)
                resolved["channels"][channel_id] = channel
        elif x == "roles":
            resolved["roles"] = {}
            for role_id in data["data"]["resolved"]["roles"]:
                role_data = data["data"]["resolved"]["roles"][role_id]
                resolved["roles"][role_id] = discord.Role(data=role_data, guild=_state._get_guild(data["guild_id"]), state=_state)
        elif x == "users":
            pass
        else:
            logging.warning("Could not resolve data of type '" + str(x) +  "'")

    return resolved

async def fetch_data(value, typ, data, _discord):
    logging.debug("fetching something with type " + str(typ) + " value " + str(value))
    if typ == OptionType.MEMBER:
        return await (await _discord.fetch_guild(int(data["guild_id"]))).fetch_member(int(value))
    elif typ == OptionType.CHANNEL:
        return await _discord.fetch_channel(int(value))
    elif typ == OptionType.ROLE:
        return get(await (await _discord.fetch_guild(int(data["guild_id"]))).fetch_roles(), value, lambda x: getattr(x, "id", None) == int(value))
    elif typ == AdditionalType.MESSAGE:
        return await (await _discord.fetch_channel(data["channel_id"])).fetch_message(int(value))
    else:
        return value

def resolve_data(value, typ, data, state):
    resolved = resolve(data, state)
    logging.debug("resolving something with type " + str(typ) + " value " + str(value))
    if typ == OptionType.MEMBER:
        return resolved["members"].get(value)
    elif typ == OptionType.ROLE:
        return resolved["roles"].get(value)
    elif typ == OptionType.CHANNEL:
        return resolved["channels"].get(value)
    elif typ == AdditionalType.MESSAGE:
        return resolved["messages"].get(value)
    else:
        return value

def cache_data(value, typ, data, _state):
    logging.debug("getting something out of the cache with type " + str(typ) + " value " + str(value))
    if typ in [OptionType.STRING, OptionType.INTEGER, OptionType.BOOLEAN, OptionType.FLOAT]:
        return value
    elif typ == OptionType.MEMBER:
        return _state._get_guild(int(data["guild_id"])).get_member(int(value))
    elif typ == OptionType.CHANNEL:
        return _state._get_channel(int(value))
    elif typ == OptionType.ROLE:
        return _state._get_guild(int(data["guild_id"])).get_role(value)
    elif typ == AdditionalType.MESSAGE:
        return _state._get_guild(int(data["guild_id"])).get_partial_message(value)
    elif typ == AdditionalType.GUILD:
        return _state._get_guild(int(value))
    else:
        return value

async def handle_options(data, options, method, _discord: discord.Client):
    _options = {}
    for op in options:
        if op["type"] not in [OptionType.SUB_COMMAND, OptionType.SUB_COMMAND_GROUP]:
            parsed = await handle_thing(op["value"], op["type"], data, method, _discord)
            logging.debug("value in handle_options is " + str(op["value"]) + " with type " + str(op["type"]) + " and name is " + str(op["name"]) + " parsed " + str(parsed))
            
            if parsed is None:
                raise CouldNotParse(op["value"], op["type"], method)
            _options[op["name"]] = parsed
    return _options

async def handle_thing(value, typ, data, method, _discord, auto=False) -> typing.Union[str, int, bool, discord.Member, discord.TextChannel, discord.Role, float, discord.Message, discord.Guild]:
    logging.debug("Trying to handle val " + str(value) + " type " + str(typ) +  " with method " + str(method) + " auto is" + str(auto))
    if method is ParseMethod.RESOLVE or method is ParseMethod.AUTO:
        try:
            return resolve_data(value, typ, data, _discord._connection)
        except Exception as ex:
            logging.warning("Got exepction while resolving data" +
                f"\n{type(ex).__name__}: {ex}\n" +
                f"{__file__}:{ex.__traceback__.tb_lineno}" +
                ("\nTrying next method" if method is ParseMethod.AUTO else "")
            )
            if method is ParseMethod.AUTO:
                return await handle_thing(value, typ, data, ParseMethod.FETCH, _discord, True)
    elif method is ParseMethod.FETCH:
        try:
            return await fetch_data(value, typ, data, _discord)
        except Exception as ex:
            logging.warning("Got exepction while getting data from cache" +
                f"\n{type(ex).__name__}: {ex}\n" +
                f"{__file__}:{ex.__traceback__.tb_lineno}" +
                ("\nTrying next method" if method is ParseMethod.AUTO else "")
            )
            if auto is True:
                return await handle_thing(value, typ, data, ParseMethod.CACHE, _discord, auto)
    elif method is ParseMethod.CACHE:
        try:
            return cache_data(value, typ, data, _discord._connection)
        except Exception as ex:
            logging.warning("Got exepction while resolving data" +
                f"\n{type(ex).__name__}: {ex}\n" +
                f"{__file__}:{ex.__traceback__.tb_lineno}" +
                ("\nTrying next method" if method is ParseMethod.AUTO else "")
            )
            if auto:
                return await handle_thing(value, typ, data, ParseMethod.RAW, _discord, auto)
    elif method is ParseMethod.RAW:
        return value
    else:
        logging.warning("Unkonw parsemethod: " + str(method) + "\nReturning raw value")
        return value