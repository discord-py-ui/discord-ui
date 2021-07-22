======================================================
discord-message-components documentation!
======================================================

Welcome to the discord message components docs!
This is a "extension" (I guess) or whatever you want to call it for `discord.py <https://github.com/Rapptz/discord.py>`__

We (`Redstone <https://github.com/RedstoneZockt>`__ and me) decided to create a pip package for the 
new message components, until discord.py v2.0 is out

We added slash command support to, you can now use slashcommands together with buttons and selectmenus

.. important::

   If you want to use slash commands, in the oauth2 invite link generation, 
   you have to check both ``bot`` and ``application.commands`` fields

   .. image:: images/slash/invite_scope.png
      :width: 1000

We got some cool features for you like:

.. note::

   *  Sending buttons and select menus very easy
   *  Receiving their interaction
   *  Responding to their interacion
   *  Creating slashcommands, subcommands and subcommand groups
   *  Receiving them and respond to them, including message components
   *  Setting up permissions for slash commmands
   *  Deleting unused slash commands
   *  Nuking all accesable commands

   and some more things

.. important::

   We added a function that overrides the normal `discord.ext.commands.Bot` client.
   You can now acces the slash extension and the components extension via `client.slash` and `client.components`,
   and for sending components, you can now use `message.channel.send`, this will use the custom 
   method of our libary, instead of the discord.py method


Installation
---------------------

To install this package, open your terminal or command line and type

.. code-block::

   # windows
   py -m install discord-message-components
   # linux
   python3 -m pip install discord-message-components


Examples
---------------------

we have some examples `here <https://github.com/KusoRedsto/discord-message-components/tree/main//examples>`__


Docs
---------------------


.. toctree::
   :maxdepth: 1

   usage.rst
   extension.rst
   components.rst
   slash.rst
 

Links
---------------------

*  `Pip package <https://pypi.org/project/discord-message-components/>`__
*  `404kuso <https://github.com/404kuso>`__
*  `RedstoneZockt <https://github.com/RedstoneZockt>`__
*  `discord.py <https://github.com/Rapptz/discord.py>`__
*  `discord message component docs <https://discord.com/developers/docs/interactions/message-components>`__
*  `discord slash commands docs <https://discord.com/developers/docs/interactions/slash-commands>`__
*  And in case you don't like our package, check out `this cool libary for slash commands and slash components <https://github.com/discord-py-slash-commands/discord-py-interactions>`__