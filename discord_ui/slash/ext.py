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
    """A decorator for auto deferring a command

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
            ctx = args[0]
            await ctx.defer(hidden=hidden)
            return await func(*args, **kwargs)
        return wraper
    return decorator