.. currentmodule:: discord_ui

======
cogs
======

Setup
===============

To use cog tools, you have to import the module

.. code-block::

    from discord_ui.cogs import slash_cog, subslash_cog, context_cog, listening_component_cog

.. important::

    You need a :class:`~Slash` instance for slashcommands cogs and a :class:`~Component` instance for listening components. 
    The best would be to initialze a :class:`~UI` instance, because it will initialize a component instance and a slash instance


Example

.. code-block::

    from discord.ext import commands
    from discord_ui import UI
    from discord_ui.cogs import slash_cog, subslash_cog


    bot = commands.Bot(" ")
    ui = UI(bot)
    

    class Example(commands.Cog):
        def __init__(self, bot):
            self.bot = bot
        
        @slash_cog(guild_ids=[785567635802816595])
        async def name(self, ctx):
            """Responds with the name of the bot"""
            await ctx.send("my name is _" + self.bot.user.name + "_")
    
    bot.add_cog(Example(bot))
    bot.run("token")


slash_cog
==========

.. automethod:: cogs.slash_cog

subslash_cog
============

.. automethod:: cogs.subslash_cog

context_cog
=============

.. automethod:: cogs.context_cog

listening_component_cog
========================

.. automethod:: cogs.listening_component_cog