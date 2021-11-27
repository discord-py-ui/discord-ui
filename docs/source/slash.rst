.. currentmodule:: discord_ui

=====================
Commands
=====================


Slash
=====


.. autoclass:: Slash
    :members:

.. code-block::

    import discord
    from discord.ext import commands
    from discord_ui import Slash

    client = commands.Bot(" ")
    slash = Slash(client) 


Events
================

We got 2 events to listen for your client

``slash_command``
~~~~~~~~~~~~~~~~~~~~~~
    
This event will be dispatched whenever a normal slash command was used

One parameter will be passed

*  :class:`~SlashInteraction` | :class:`~SlashedSubCommand`

.. code-block::

    @client.listen('on_slash_command')
    def slash_command(ctx: SlashInteraction):
        ...

.. code-block::

    await client.wait_for('slash_command', check=lambda ctx: ...)


``context_command``
~~~~~~~~~~~~~~~~~~~~~~

This event will be dispatched whenever a context command was used

Two parameters will be passed

*  :class:`~ContextInteraction`
*  :class:`~Message` | :class:`discord.User`

.. code-block::

    @client.listen('context_command')
    def on_context(ctx: ContextInteraction, param):
        ...

.. code-block::

    await client.wait_for('context_command', check=lambda ctx, param: ...)


SlashOption
============

.. autoclass:: SlashOption
    :members:


SlashPermission
===============

.. autoclass:: SlashPermission
    :members:

SlashInteraction
=================

.. autoclass:: SlashInteraction()
    :members:
    :inherited-members:


Ephemeral
==========

EphemeralMessage
~~~~~~~~~~~~~~~~

.. autoclass:: EphemeralMessage()
    :members:

EphemeralResponseMessage
~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: EphemeralResponseMessage()
    :members:

Tools
=========

.. autofunction:: create_choice