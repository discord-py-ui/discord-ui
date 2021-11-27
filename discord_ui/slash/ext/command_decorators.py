"""
discord_ui.ext.command_decorator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Important: Every decorator should be placed before the actual slashcommand decorator, 
except check auto-response decorators, they have to be placed after the target check decorator.

Note: **Theoretically**, these decorators could be used together with normal cog commands and 
not only the slash cog commands, but if you use them for the normal commands, the ``hidden`` param 
doesn't work
"""

import inspect
import functools
from typing import TypeVar, Any, List

from discord.ext import commands


__all__ = (
    'auto_guild',
    'check_failed',
    'any_failure_response',
    'alias',
    'no_sync',
    'auto_defer',
)

f = TypeVar("f")

class _auto_guild_sentinel():
    def __init__(self):
        self.guild_ids: List[int] = []
        """The guild_ids that should be used when decorating a command with this class"""
    def __call__(self, m):
        if inspect.ismethod(m):
            m.__guild_ids__ = self.guild_ids
        else:
            m.guild_ids = self.guild_ids
        return m

auto_guild: _auto_guild_sentinel = _auto_guild_sentinel()
"""Decorator for setting guild_ids to application-commands.
This decorator has to be placed before the actual command decorator

Usage
-----

.. code-block::

    @ui.slash.command(...)
    @ext.auto_guild
    async def my_command(ctx, ...):
        ...
"""

def check_failed(content=None, hidden=False, **fields):
    """A decorator for autoresponding to a cog check that failed.
    
    The decorator has to be placed after the check deceorator

    Parameters
    ----------
    content: :class:`str`
        The raw message content
    tts: :class:`bool`
        Whether the message should be send with text-to-speech
    embed: :class:`discord.Embed`
        Embed rich content
    embeds: List[:class:`discord.Embed`]
        A list of embeds for the message
    file: :class:`discord.File`
        The file which will be attached to the message
    files: List[:class:`discord.File`]
        A list of files which will be attached to the message
    nonce: :class:`int`
        The nonce to use for sending this message
    allowed_mentions: :class:`discord.AllowedMentions`
        Controls the mentions being processed in this message
    mention_author: :class:`bool`
        Whether the author should be mentioned
    components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`]
        A list of message components to be included
    delete_after: :class:`float`
        After how many seconds the message should be deleted, only works for non-hiddend messages
    hidden: :class:`bool`
        Whether the response should be visible only to the user 
    

    Example
    -------

    .. code-block::

        # first check
        @ext.check_failed("command is guild only", hidden=True)
        @commands.guild_only()
        # second check
        @ext.check_failed("command can only used in nsfw channels", hidden=True)
        @commands.is_nsfw()
        @cogs.slash_command(guild_ids=[867699578034716683])
        async def callback(self, ctx):
            ...
    """
    def wrapper(cog):
        # get last check
        check = cog.checks[-1]
        _invoke = cog.invoke

        async def invoke(ctx, *args, **kwargs):
            try:
                if not check(ctx):
                    await ctx.send(content, **fields, hidden=hidden)
                    return
            except commands.CheckFailure:
                await ctx.send(content, **fields, hidden=hidden)
                raise
            await _invoke(ctx, *args, **kwargs)

        cog.invoke = invoke
        return cog
    return wrapper

def any_failure_response(content, hidden=False, **fields):
    """Decorator for autoresponding to all checks of a cog command that failed.

    Note if you use the `check_failure_response` for a check, its response will be sent
    
    Parameters
    ----------
    content: :class:`str`
        The raw message content
    tts: :class:`bool`
        Whether the message should be send with text-to-speech
    embed: :class:`discord.Embed`
        Embed rich content
    embeds: List[:class:`discord.Embed`]
        A list of embeds for the message
    file: :class:`discord.File`
        The file which will be attached to the message
    files: List[:class:`discord.File`]
        A list of files which will be attached to the message
    nonce: :class:`int`
        The nonce to use for sending this message
    allowed_mentions: :class:`discord.AllowedMentions`
        Controls the mentions being processed in this message
    mention_author: :class:`bool`
        Whether the author should be mentioned
    components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`]
        A list of message components to be included
    delete_after: :class:`float`
        After how many seconds the message should be deleted, only works for non-hiddend messages
    hidden: :class:`bool`
        Whether the response should be visible only to the user 
    
    
    """
    def wrapper(cog):
        _invoke = cog.invoke

        async def invoke(ctx, *args, **kwargs):
            try:
                if not await cog.can_run(ctx):
                    await ctx.send(content, hidden=hidden, **fields)
                    return
            except commands.CheckFailure:
                await ctx.send(content, hidden=hidden, **fields)
                raise
            await _invoke(ctx, *args, **kwargs)

        cog.invoke = invoke
        return cog
    return wrapper

def alias(aliases):
    """Decorator for slashcommand aliases that will add the same command but with different names.
    
    Parameters
    ----------
    aliases: List[:class:`str`] | :class:`str`
        The alias(es) for the command with wich the command can be invoked with

    Usage:
    
    .. code-block::
    
        @ui.slash.command(name="cats", ...)
        @ui.slash.alias(["catz", "cute_things"])
    
    """
    def wrapper(command):
        if not hasattr(command, "__aliases__"):
            command.__aliases__ = []
        # Allow multiple alias decorators
        command.__aliases__.extend(aliases if not isinstance(aliases, str) else [aliases])
        return command
    return wrapper

def no_sync():
    """Decorator that will prevent an application-command to be synced with the api.
   
    Example
    -------

    .. code-block::

        from discord_ui import ext

        @ui.slash.command()
        @ext.no_sync()
        async def no_sync(ctx):
            \"\"\"This command will never be synced with the api\"\"\"
            ...

    """
    def wrapper(callback):
        callback.__sync__ = False
        return callback
    return wrapper

def auto_defer(hidden=False):
    """A decorator for auto deferring a interaction. This decorator has to be placed before the main decorator
    
    Parameters
    ----------
    hidden: :class:`bool`, optional
        Whether the interaction should be deferred hidden; default ``False``

    Example
    --------

    .. code-block::

        from discord_ui import ext

        @ui.slash.command()
        @ext.auto_defer()
        async def my_command(ctx):
            \"\"\"This command will be deferred automatically\"\"\"
            ...
    
    """
    # https://stackoverflow.com/questions/69076152/how-to-inject-a-line-of-code-into-an-existing-function#answers-header
    def decorator(func):
        func.__auto_defer__ = True
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # if there is self param use the next one
            ctx = args[1 if list(inspect.signature(func).parameters.keys())[0] == "self" else 0]
            # use defer for "auto_defering"
            await ctx.defer(hidden=hidden)
            return await func(*args, **kwargs)
        return wrapper
    return decorator