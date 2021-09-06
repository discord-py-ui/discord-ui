from discord_ui.cogs import BaseSlash
import types
import functools


def no_sync():
    """Decorator that will prevent an application-command to be synced with the api.

    Important: The decorator has to be placed before the slashcommand

    Usage:

    .. code-block::

        from discord_ui.slash import ext

        @ui.slash.command(name="no_sync")
        @ext.no_sync()
        async def callback(ctx):
            \"\"\"This command will never be synced with the api\"\"\"
            ...

    """
    def wraper(callback):
        callback.__sync__ = False
        return callback
    return wraper

def auto_defer(defer=True, hidden=False):
    def wraper(callback):
        """Based on http://stackoverflow.com/a/6528148/190597 (Glenn Maynard)"""
        function().__code__.co_argcount
        deferring_callback = types.FunctionType(callback.__code__, callback.__globals__, name=callback.__name__,
                            argdefs=callback.__defaults__,
                            closure=callback.__closure__)
        deferring_callback = functools.update_wrapper(deferring_callback, callback)
        deferring_callback.__kwdefaults__ = callback.__kwdefaults__
        return deferring_callback
    return wraper
        
