import asyncio
from .slash.tools import (
    create_command,
    create_guild_command,
    get_commands,
    get_guild_commands,
)
from .slash.slash_commands import BaseSlashCommand
from .components import Button, LinkButton, SelectMenu
from typing import List
from .tools import MISSING, jsonifyMessage, V8Route, send_files
from .receive import Message, getResponseMessage

import discord
from discord.ext import tasks
from discord.ext import commands


class Slash:
    def __init__(self, client) -> None:
        print("This feature is not availabile yet")
        self._discord = client
        self.commands = []
        self.subcommands = []

    async def get_commands(self):
        return await get_commands(self._discord)

    async def get_guild_commands(self, guild_id):
        return await get_guild_commands(self._discord, guild_id)

    async def add_command(
        self, callback, name, description, choices=MISSING, guild_ids=MISSING
    ):
        base = BaseSlashCommand(callback, name, description, choices)
        self.commands.append(base)
        if guild_ids is MISSING:
            await create_command(base, self._discord)
        else:
            for x in guild_ids:
                await create_guild_command(base, self._discord, x)

    def slash(self, name, description, choices=MISSING, guild_ids=MISSING):
        def wrapper(callback):
            print("registering command")
            base = BaseSlashCommand(callback, name, description, choices)
            self.commands.append(base)
            if guild_ids is MISSING:
                create_command(base, self._discord)
            else:
                for x in guild_ids:
                    create_guild_command(base, self._discord, x)

        return wrapper


class Components:
    """A component listener instance for using components in discord

    Example
    ------------------
    Example for using the listener


    .. code-block::

        ...
        # Your bot declaration should be here
        client.components = components(client)


    for listening to button presses, use

    .. code-block::

        ...
        @client.event("on_button_press")
        async def on_button(pressedButton, message):
            pass

    for listening to select menu selections, use


    .. code-block::

        ...
        @client.event("on_menu_select")
        async def on_select(seletedMenu, message):
            pass


    """

    def __init__(self, client: commands.Bot):
        """Creates a new compnent listener

        Example
        ```py
        Components(client)
        ```
        """
        self._listening_components = []
        """A list of components that are listening for interaction"""
        self._discord = client
        self._discord.add_listener(self.on_socket_response)

    async def on_socket_response(self, msg):
        """Will be executed if the bot receives a socket response"""
        if msg["t"] != "INTERACTION_CREATE":
            return
        data = msg["d"]

        if data["type"] != 3:
            return

        guild = await self._discord.fetch_guild(data["guild_id"])
        user = discord.Member(
            data=data["member"], guild=guild, state=self._discord._connection
        )

        msg = getResponseMessage(self._discord, data=data, user=user, response=True)

        # Get listening components with the same custom id
        _listening_components = [
            x for x in self._listening_components if data["data"]["custom_id"] == x[1]
        ]
        if len(_listening_components) == 1:
            await _listening_components[0][0](msg.interaction_component, msg)

        if data["data"]["component_type"] == 2:
            self._discord.dispatch("button_press", msg.interaction_component, msg)
        elif data["data"]["component_type"] == 3:
            self._discord.dispatch("menu_select", msg.interaction_component, msg)

    async def send(
        self,
        channel,
        content=MISSING,
        *,
        tts=False,
        embed=MISSING,
        embeds=MISSING,
        file=MISSING,
        files=MISSING,
        delete_after=MISSING,
        nonce=MISSING,
        allowed_mentions=MISSING,
        reference=MISSING,
        mention_author=MISSING,
        components=MISSING,
    ) -> Message:
        """Sends a message to a textchannel

        Parameters
        ----------
        channel: :class:`discord.TextChannel`
            The target textchannel
        content: :class:`str`, optional
            The message text content; default None
        tts: :class:`bool`, optional
            True if this is a text-to-speech message; default False
        embed: :class:`discord.Embed`, optional
            Embedded rich content; default None
        embeds: List[:class:`discord.Embed`], optional
            embedded rich content (up to 6000 characters); default None
        file: :class:`discord.File`, optional
            A file sent as an attachment to the message; default None
        files: List[:class:`discord.File`], optional
            A list of file attachments; default None
        delete_after: :class:`float`, optional
            After how many seconds the message should be deleted; default None
        nonce: :class:`int`, optional
            The nonce to use for sending this message. If the message was successfully sent, then the message will have a nonce with this value; default None
        allowed_mentions: :class:`discord.AllowedMentions`, optional
            A list of mentions proceeded in the message; default None
        reference: :class:`discord.MessageReference` | :class:`discord.Message`, optional
            A message to refer to (reply); default None
        mention_author: :class:`bool`, optional
            True if the author should be mentioned; default None
        components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`], optional
            A list of message components included in this message; default None

        Returns
        -------
        :return: Returns the sent message
        :type: :class:`~Message`

        Raises
        ------
        :raises: :class:`discord.InvalidArgument`: A passed argument was invalid
        """

        if type(channel) != discord.TextChannel:
            raise discord.InvalidArgument("Channel must be of type discord.TextChannel")

        payload = jsonifyMessage(
            content=content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=reference,
            mention_author=mention_author,
            components=components,
        )

        route = V8Route("POST", f"/channels/{channel.id}/messages")

        r = None
        if file is MISSING and files is MISSING:
            r = await self._discord.http.request(route, json=payload)
        else:
            r = await send_files(
                route, files=files or [file], payload=payload, http=self._discord.http
            )

        msg = getResponseMessage(self._discord, r, response=False)

        if delete_after is not None:
            await msg.delete(delay=delete_after)

        return msg

    def listening_component(self, custom_id):
        """
        A decorator for a listening component, that will be always executed if the invoked interaction has the custom_id passed

        .. Warning::

            The button_press event will not be dispatched when using ``listening_component``, so make sure you don't use that custom_id here for any of your normal components
        """

        def wrapper(callback):
            if len([x for x in self._listening_components if x[1] == custom_id]) > 0:
                raise Exception(
                    "custom_id "
                    + str(custom_id)
                    + " is already in use! Use another custom_id"
                )
            self._listening_components.append((callback, custom_id))

        return wrapper
