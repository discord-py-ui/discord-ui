======================================================
discord-ui documentation!
======================================================

Welcome to the discord message components docs!
This is a "extension" (I guess) or whatever you want to call it for `discord.py <https://github.com/Rapptz/discord.py>`__

We (`Redstone <https://github.com/RedstoneZockt>`__ and me) decided to create a pip package for the 
new ui features that discord added. If you want to keep using our lib with dpy2, we added support for discordpy2 


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
   *  Creating and receiving the new context commands

   and some more things

.. important::
   
   The ``Messageable.send`` and ``Webhook.send`` functions are overriden by default with our custom method. 
   If you're using dpy2, the default ``discord.ext.commands.Bot`` is overriden with a custom Bot that enables degbug events
   in order to let our lib function proberly


Installation
---------------------

To install this package, open your terminal or command line and type

.. code-block::

   # windows
   py -m install discord-ui
   # linux
   python3 -m pip install discord-ui


Examples
---------------------

we have some examples `here <https://github.com/KusoRedsto/discord-ui/tree/main/examples>`__


Docs
---------------------


.. toctree::
   :maxdepth: 1

   usage.rst
   ui.rst
   interactions.rst
   components.rst
   slash.rst
 

Links
---------------------

*  `Pip package <https://pypi.org/project/discord-ui/>`__
*  `404kuso <https://github.com/404kuso>`__
*  `RedstoneZockt <https://github.com/RedstoneZockt>`__
*  `discord.py <https://github.com/Rapptz/discord.py>`__
*  `discord message component docs <https://discord.com/developers/docs/interactions/message-components>`__
*  `discord application commands docs <https://discord.com/developers/docs/interactions/application-commands>`__
*  And in case you don't like our package, check out `this cool libary for slash commands and slash components <https://github.com/discord-py-slash-commands/discord-py-interactions>`__