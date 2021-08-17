.. currentmodule:: discord_ui


====================
Message-components
====================


Setup
====================

Components
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Components
    :members:


.. code-block::

    import discord
    from discord.ext import commands
    from discord_ui import Components

    client = commands.Bot(" ")
    client.components = Components(client) 

Events
================

We got 2 events to listen for your client

``button_press``
~~~~~~~~~~~~~~~~~~~~~~
    
This event will be dispatched whenever a button was pressed

Two parameters will be passed:

*  :class:`~PressedButton`
*  :class:`~ResponseMessage`

.. code-block::

    @client.listen('on_button_press')
    def on_button(btn: PressedButton, msg: ResponseMessage):
        ...

.. code-block::

    await client.wait_for('button_press', check=lambda btn, msg: ...)


``menu_select``
~~~~~~~~~~~~~~~~~~~~~~

This event will be dispatched whenever a value was selected in a :class:`~SelectedMenu`

Two parameters will be passed

*  :class:`~SelectedMenu`
*  :class:`~ResponseMessage`

.. code-block::

    @client.listen('on_menu_select')
    def on_button(menu: SelectedMenu, msg: ResponseMessage):
        ...

.. code-block::

    await client.wait_for('menu_select', check=lambda menu, message: ...)


Components
====================

Button
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Button
    :members:
    :exclude-members: to_dict

LinkButton
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: LinkButton
    :members:
    :exclude-members: to_dict


Colors
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Colors

    .. note::

        *  (Primary, blurple) = 1

        *  (Secondary, grey) = 2
        
        *  (Succes, green) = 3
        
        *  (Danger, red) = 4
    

SelectMenu
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SelectMenu
    :members:
    :exclude-members: to_dict


SelectOption
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SelectOption
    :members:
    :exclude-members: to_dict


ActionRow
~~~~~~~~~~

.. autoclass:: ActionRow
    :members:

Interactions
=================


Message
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Message()
    :members:


ResponseMessage
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ResponseMessage()
    :members:


PressedButton
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: PressedButton()
    :members:
    :inherited-members:
    :exclude-members: to_dict


SelectedMenu
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SelectedMenu
    :members:
    :inherited-members:
    :exclude-members: set_default_option, to_dict

Tools
=========

.. autofunction:: components_to_dict