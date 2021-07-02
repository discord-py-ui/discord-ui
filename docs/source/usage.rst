Get started
=====================

At first, you need to import the discord.py package and this package

.. sourcecode::

    import discord
    from discord.ext import commands
    from discord_message_components import Components


Create a new discord client

.. sourcecode::

    client = commands.Bot(" ")

.. warning::

    Note that the discord client has to be of type :class:`discord.ext.commands.Bot`, or else it won't work

Then you need to create a new :class:`~Components` listener, where you can send components and receive them

.. sourcecode::

    client.components = Components(client)

.. note::

    This will add an attribute to your client, ``.components``, that will be used to acces the listener

Sending
=====================

To send a component, we need to acces our :class:`~Components` class with ``client.components`` and use the ``.send()`` function of it 

In this example, we'll wait for a message with the content "!test"

.. sourcecode::

    @client.listen
    async def on_message(message):
        if message.content == "!test":
            ...

Now we will send a component to the text channel where the *"!test"* message came from

Let's say we want to send two buttons and a select menu

We need to import them at first. For that, we need to go back to the beginning, where we imported the module

.. sourcecode::

    import discord
    from discord.ext import commands
    from discord_message_components import Components, Button, SelectMenu, SelectMenuOption

And to send them, we use

.. sourcecode::

    ...
    await client.components.send(message.channel, "Hello World", components=[
        Button("my_custom_id", "press me", "green"),
        Button("my_other_custom_id", "or press me!", emoji="😁", new_line=True),
        SelectMenu("another_custom_id", options=[
            SelectMenuOption("choose me", 1),
            SelectMenuOption("or me", 2),
            SelectMenuOption("or me", 3)
        ])
    ])

Now we sent some components, but how do you receive them?

Receiving
===================

To receive a button press or a selection, we can listen to the ``button_press`` and the ``menu_select`` events


**Button**

.. sourcecode::

    @client.listen('on_button_press')
    async def on_button(btn, message):
        ...

To get the user who pressed the button, you use ``btn.member``.
If you want to acces the message on which the button is, you use ``messsage``

**Select menu**

.. sourcecode::

    @client.listen('on_menu_select')
    async def on_menu(menu, message):
        ...
 

To get the user who selected a value, you use ``menu.member``.
To get the value(s) selected by the user, you need to acces ``menu.values``



And to respond to the component interaction, we use

.. sourcecode::

    await message.respond("we gotcha!")