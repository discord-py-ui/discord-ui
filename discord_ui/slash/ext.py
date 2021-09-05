def no_sync():
    """Decorator that will prevent an application-command to be synced with the api
    
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