.. currentmodule:: discord_ui

======
Cogs
======

Setup
===============

To use cog tools, you have to import the module

.. code-block::

    from discord_ui.cogs import slash_command, subslash_command, context_cog, listening_component

.. important::

    You need a :class:`~Slash` instance for slashcommands cogs and a :class:`~Component` instance for listening components. 
    The best would be to initialze a :class:`~UI` instance, because it will initialize a component instance and a slash instance


Example

.. code-block::

    from discord.ext import commands
    from discord_ui import UI
    from discord_ui.cogs import slash_command, subslash_command


    bot = commands.Bot(" ")
    ui = UI(bot)
    

    class Example(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @slash_command(guild_ids=[785567635802816595])
        async def name(self, ctx):
            """Responds with the name of the bot"""
            await ctx.send("my name is _" + self.bot.user.name + "_")
    
    bot.add_cog(Example(bot))
    bot.run("token")


slash_command
=============

.. automethod:: cogs.slash_command

subslash_command
================

.. automethod:: cogs.subslash_command

context_command
================

.. automethod:: cogs.context_command

listening_component
========================

.. automethod:: cogs.listening_component