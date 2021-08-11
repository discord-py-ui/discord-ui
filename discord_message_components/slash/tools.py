import discord
from discord.enums import ChannelType
from discord.errors import InvalidArgument, InvalidData
from .types import OptionType
from ..tools import get


class ParseMethod:
    """Methods of how the interaction argument data should be treated

    - ``RESOLVE``   [1]
    : Uses the resolved data which will be delivered together with the received interaction
    - ``FETCH``     [2]
    : Fetches all the ids of the received data with an api call
    - ``CACHE``     [3]
    : Uses the internal bot cache to receive the data ``.get_channel``, ``.get_guild``...

    .. warning::

        Some cache functions need to have intents enabled (more information https://discordpy.readthedocs.io/en/latest/intents.html?highlight=intents)

    - ``AUTO``      [4]
    : This will try to resolve the data, and if an exception occurs, it will try to fetch the data,
    and if that doesn't work it will try to get the data from the internal cache
    """
    RESOLVE     =       1
    FETCH       =       2
    CACHE       =       3
    AUTO        =       4

def resolve(data, _discord):
    resolved = {}
    for x in data["data"]["resolved"]:
        if x == "members":
            resolved["members"] = {}
            for m_id in data["data"]["resolved"]["members"]:
                member_data = data["data"]["resolved"]["members"][m_id]
                member_data["user"] = data["data"]["resolved"]["users"][m_id]
                resolved["members"][m_id] = discord.Member(data=member_data, guild=_discord.get_guild(data["guild_id"]), state=_discord._connection)
        elif x == "messages":
            resolved["messages"] = {}
            for message_id in data["data"]["resolved"]["messages"]:
                message_data = data["data"]["resolved"]["messages"][message_id]
                resolved["messages"][message_id] = discord.Message(data=message_data, channel=_discord.get_channel(data["channel_id"]), state=_discord._connection)
        elif x == "channels":
            resolved["channels"] = {}
            for channel_id in data["data"]["resolved"]["channels"]:
                channel_data = data["data"]["resolved"]["channels"][channel_id]

                guild = _discord.get_guild(data["guild_id"])
                channel = None
                if ChannelType(channel_data["type"]) is  ChannelType.text:
                    channel = discord.TextChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.voice:
                    channel = discord.VoiceChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.category:
                    channel = discord.CategoryChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.group:
                    channel = discord.GroupChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.news:
                    channel = discord.NewsChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.private:
                    channel = discord.DMChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.store:
                    channel = discord.StoreChannel(data=channel_data, guild=guild, state=_discord._connection)
                elif ChannelType(channel_data["type"]) is  ChannelType.stage_voice:
                    channel = discord.StageChannel(data=channel_data, guild=guild, state=_discord._connection)
                resolved["channels"][channel_id] = channel
        elif x == "roles":
            resolved["roles"] = {}
            for role_id in data["data"]["resolved"]["roles"]:
                role_data = data["data"]["resolved"]["roles"][role_id]
                resolved["roles"][role_id] = discord.Role(data=role_data, guild=_discord.get_guild(data["guild_id"]), state=_discord._connection)
        elif x == "users":
            pass
        else:
            print("Warning: Could not resolve data of type '" + str(x) +  "'")

    return resolved

async def fetch_data(value, typ, data, _discord):
    print("fetch data")
    if typ == OptionType.MEMBER:
        return await (await _discord.fetch_guild(int(data["guild_id"]))).fetch_member(int(value))
    elif typ == OptionType.CHANNEL:
        print("channel", await _discord.fetch_channel(int(value)))
        return await _discord.fetch_channel(int(value))
    elif typ == OptionType.ROLE:
        return get(await (await _discord.fetch_guild(int(data["guild_id"]))).fetch_roles(), value, lambda x: getattr(x, "id", None) == int(value))
    elif typ == 44:
        return await (await _discord.fetch_channel(data["channel_id"])).fetch_message(int(value))
    else:
        return value

def resolve_data(value, typ, data, _discord):
    resolved = resolve(data, _discord)
    if typ in [OptionType.STRING, OptionType.INTEGER, OptionType.BOOLEAN, OptionType.FLOAT]:
        return value
    elif typ == OptionType.MEMBER:
        return resolved["members"].get(value)
    elif typ == OptionType.CHANNEL:
        return resolved["channels"].get(value)
    elif typ == OptionType.ROLE:
        return resolved["roles"].get(value)
    elif typ == 44:
        return resolved["messages"].get(value)

def cache_data(value, typ, data, _discord):
    if typ in [OptionType.STRING, OptionType.INTEGER, OptionType.BOOLEAN, OptionType.FLOAT]:
        return value
    elif typ == OptionType.MEMBER:
        return _discord.get_guild(int(data["guild_id"])).get_member(int(value))
    elif typ == OptionType.CHANNEL:
        return _discord.get_channel(int(value))
    elif typ == OptionType.ROLE:
        return _discord.get_guild(int(data["guild_id"])).get_role(value)
    elif typ == 44:
        return _discord.get_guild(int(data["guild_id"])).get_partial_message(value)

async def handle_options(data, options, method, _discord: discord.Client):
    _options = {}
    for op in options:
        _options[op["name"]] = await handle_thing(op["value"], op["type"], data, _discord, method)
    return _options

async def handle_thing(value, typ, data, method, _discord):
    if method is ParseMethod.RESOLVE or method is ParseMethod.AUTO:
        try:
            return resolve_data(value, typ, data, _discord)
        except Exception as ex:
            print("Got exepction while resolving data",
                f"\n{type(ex).__name__}: {ex}\n",
                f"{__file__}:{ex.__traceback__.tb_lineno}"
            )
            if method is ParseMethod.AUTO:
                return await handle_thing(value, typ, data, ParseMethod.FETCH, _discord)
    elif method is ParseMethod.FETCH:
        try:
            return await fetch_data(value, typ, data, _discord)
        except Exception as ex:
            print("Got exepction while getting data from cache",
                f"\n{type(ex).__name__}: {ex}\n",
                f"{__file__}:{ex.__traceback__.tb_lineno}"
            )
            if method is ParseMethod.AUTO:
                return await handle_thing(value, typ, data, ParseMethod.CACHE, _discord)
    elif method is ParseMethod.CACHE:
        return cache_data(value, typ, data, _discord)
        