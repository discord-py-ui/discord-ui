.. currentmodule:: discord_ui

=====================
Interactions
=====================

You can receive general interactions of all possible types with the client event ``interaction_received``.
This event passes a :class:`Interaction` object which you can defer, respond to or whatever you want

Example

.. code-block::

    # client stuff before
    from discord_ui import Interaction

    @client.listen("on_interaction_received")
    async def on_interaction(interaction: Interaction):
        await interaction.respond("houston we got an interaction")


Interaction
~~~~~~~~~~~~

.. autoclass:: Interaction()
    :members:
