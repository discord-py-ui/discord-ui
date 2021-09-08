"""
discord_ui.ext
~~~~~~~~~~~~~~~

An extension module to the libary that has some usefull decorators and functions 
for application-commands.

.. code-block::

    from discord_ui import ext


Important: Every decorator should be placed before the actual slashcommand decorator.
    When using the cog decorator it shouldn't be important

"""

import functools
import inspect

from discord.ext.commands import errors


def check_failure_response(content=None, hidden=False, **fields):
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
        @ext.check_failure_response("command is guild only", hidden=True)
        @commands.guild_only()
        # second check
        @ext.check_failure_response("command can only used in nsfw channels", hidden=True)
        @commands.is_nsfw()
        @cogs.slash_cog(guild_ids=[867699578034716683])
        async def callback(self, ctx):
            ...
    """
    def wraper(cog):
        # get last check
        check = cog.checks[-1]
        _invoke = cog.invoke

        async def invoke(ctx, *args, **kwargs):
            try:
                if not check(ctx):
                    await ctx.respond(content, **fields, hidden=hidden)
                    return
            except errors.CheckFailure:
                await ctx.respond(content, **fields, hidden=hidden)
                raise
            await _invoke(ctx, *args, **kwargs)

        cog.invoke = invoke
        return cog
    return wraper

def any_failure_response(content, hidden=False, **fields):
    """Decorator for autoresponding to all cog checks that failed.

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
    def wraper(cog):
        _invoke = cog.invoke

        async def invoke(ctx, *args, **kwargs):
            try:
                if not await cog.can_run(ctx):
                    await ctx.respond(content, hidden=hidden, **fields)
                    return
            except errors.CheckFailure:
                await ctx.respond(content, hidden=hidden, **fields)
                raise
            await _invoke(ctx, *args, **kwargs)

        cog.invoke = invoke
        return cog
    return wraper

def guild_change(guild_id, *, name=None, description=None, default_permission=True):
    """A decorator for slashcommands that will apply changes to a specific guild

    Note that this decorator should mainly be used for guild commands, because if used with
    a global command, both commands will show up, the changed one and the global one.
    
    Parameters
    ----------
    guild_id: :class:`int` | :class:`str`
        The guild_id where the changes should be applied to
    name: :class:`str`, optional
        The new name; default None
    description: :class:`str`, optional
        The new description; default None
    default_permission: :class:`bool`, optional
        Whether this command can be used by default; default True
    
    """
    def wraper(callback):
        if not hasattr(callback, "__guild_changes__"):
            callback.__guild_changes__ = {}
        callback.__guild_changes__[str(guild_id)] = (name, description, default_permission)
        return callback
    return wraper

def alias(aliases):
    """Decorator for slashcommand aliases that will add the same command but with different names.
    
    Usage:
    
    .. code-block::
    
        @ui.slash.command(name="cats", ...)
        @ui.slash.alias(["catz", "cute_things"])
    
    """
    def wraper(command):
        command.__aliases__ = aliases
        return command
    return wraper

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
    def wraper(callback):
        callback.__sync__ = False
        return callback
    return wraper

def auto_defer(hidden=False):
    """A decorator for auto deferring a command.

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
        async def wraper(*args, **kwargs):
            params = inspect.signature(func).parameters.keys()[0] == "self"
            # if there is self param use the next one
            ctx = args[1 if list(inspect.signature(func).parameters.keys()[0]) == "self" else 0]
            # use defer for "auto_defering"
            await ctx.defer(hidden=hidden)
            return await func(*args, **kwargs)
        return wraper
    return decorator