.. currentmodule:: discord_ui

====================
Message-components
====================


Components
===========

.. autoclass:: Components
    :members:

.. code-block::

    import discord
    from discord.ext import commands
    from discord_ui import Components

    client = commands.Bot(" ")
    components = Components(client) 

Events
================

We got 2 events to listen for your client

``button_press``
~~~~~~~~~~~~~~~~~~~~~~
    
This event will be dispatched whenever a button was pressed

A sole parameter will be passed:

*  :class:`~PressedButton`: The pressed button

.. code-block::

    @client.listen('on_button_press')
    def on_button(btn: PressedButton):
        ...

.. code-block::

    await client.wait_for('button_press', check=lambda btn: ...)


``menu_select``
~~~~~~~~~~~~~~~~~~~~~~

This event will be dispatched whenever a value was selected in a :class:`~SelectedMenu`

A sole paremeter will be passed

*  :class:`~SelectedMenu`: The menu where a value was selected

.. code-block::

    @client.listen('on_menu_select')
    def on_button(menu: SelectedMenu):
        ...

.. code-block::

    await client.wait_for('menu_select', check=lambda menu: ...)


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
    :inherited-members:
    :exclude-members: to_dict


ButtonStyles
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ButtonStyles

    .. note::

        *  (Primary, blurple) = 1

        *  (Secondary, grey) = 2
        
        *  (Succes, green) = 3
        
        *  (Danger, red) = 4
    

SelectMenu
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SelectMenu
    :members:
    :inherited-members:
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
    :exclude-members: to_dict

Tools
=========

.. autofunction:: components_to_dict