.. currentmodule:: discord_ui

====================
Components
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

We got 3 events to listen for your client

``component``
~~~~~~~~~~~~~~

This event will be dispatched whenever a component was invoked

A sole parameter will be passed

*  :class:`~ComponentContext`: The used component

.. code-block::

    @client.listen()
    async on_componet(component: ComponentContext):
        ...

.. code-block::

    await client.wait_for('component', check=lambda com: ...)


``button``
~~~~~~~~~~~~~~~~~~~~~~
    
This event will be dispatched whenever a button was pressed

A sole parameter will be passed:

*  :class:`~ButtonInteraction`: The pressed button

.. code-block::

    @client.listen()
    def on_button(btn: ButtonInteraction):
        ...

.. code-block::

    await client.wait_for('button', check=lambda btn: ...)


``select``
~~~~~~~~~~~~~~~~~~~~~~

This event will be dispatched whenever a value was selected in a :class:`~SelectInteraction`

A sole paremeter will be passed

*  :class:`~SelectInteraction`: The menu where a value was selected

.. code-block::

    @client.listen()
    def on_select(menu: SelectInteraction):
        ...

.. code-block::

    await client.wait_for('select', check=lambda menu: ...)


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


ButtonStyle
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ButtonStyle
    

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


Interactions
=================


Message
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: Message()
    :members:

ButtonInteraction
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: ButtonInteraction()
    :members:
    :inherited-members:
    :exclude-members: to_dict


SelectInteraction
~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: SelectInteraction()
    :members:
    :inherited-members:
    :exclude-members: to_dict

Tools
=========

.. autofunction:: components_to_dict