from typing import List
from .tools import jsonifyMessage, V8Route
from .receive import Message, getResponseMessage

import discord
from discord.ext import commands


class Buttons:
    """A button instance for using buttons

    Attributes
    ----------------
    send: `function`
        Sends a message to a `discord.TextChannel`

    """

    def __init__(self, client: commands.Bot):
        """
        This will create a new button intearction Listener

        For receiving the button event, scroll down to the bottom and take a look at the example

        Parameters
        ------------------
        ```py
        (commands.Bot) client
        ```
            The discord bot client

        Example
        ------------------
        Here's an example for using the button listener
        ```py
        # Your bot declaration should be here
        ...
        client.buttons = Buttons(client)

        @client.event("on_button_press")
        async def on_button(pressedButton, message):
            pass
        ```
        """
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

        msg = await getResponseMessage(self._discord, data, user, True)

        self._discord.dispatch("button_press", msg.pressedButton, msg)

    async def send(
        self,
        channel: discord.TextChannel,
        content=None,
        *,
        tts=False,
        embed=None,
        embeds=None,
        file: discord.File = None,
        files: List[discord.File] = None,
        delete_after=None,
        nonce=None,
        allowed_mentions=None,
        reference=None,
        mention_author=None,
        buttons=None,
    ) -> Message:
        """
        Sends a message to a `discord.TextChannel`

        Parameters
        -----------------
        ```py
        (discord.TextChannel) channel
        ```
            The channel where the message is going to be send
        ```py
        (str) content
        ```
            The message text content
        ```py
        (bool) tts
        ```
            Whether text-to-speech should be used
        ```py
        (discord.Embed) embed
        ```
            The embed in the message
        ```py
        (List[discord.Embed]) embeds
        ```
            A list of embeds for the message
        ```py
        (discord.File) file
        ```
            The attached file for the message
        ```py
        (List[discord.File]) file
        ```
            A list of Files which are going to be attached to the messaeg
        ```py
        (float) delete_after
        ```
            The numbers of seconds after which the message should be deleted
        ```py
        (int) nonce
        ```
            The nonce to use for sending this message
        ```py
        (List[discord.AllowedMentions])
        ```
            The mentions proceeded in the message
        ```py
        (discord.MessageReference or discord.Message) reference
        ```
            The message to refer to
        ```py
        (bool) mention_author
        ```
            Whether the author should be mentioned
        ```py
        (List[Button]) buttons
        ```
            A list of buttons included in the message


        Returns
        ---------------------
        ```py
        (Message)
        ```
            The sent message including buttons
        """
        if type(channel) != discord.TextChannel:
            raise discord.InvalidArgument("Channel must be of type discord.TextChannel")

        payload = jsonifyMessage(
            content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            reference=reference,
            mention_author=mention_author,
            buttons=buttons,
        )

        route = V8Route("POST", f"/channels/{channel.id}/messages")

        r = await self._discord.http.request(route, json=payload)
        msg = await getResponseMessage(self._discord, r, response=False)

        if delete_after is not None:
            await msg.delete(delay=delete_after)

        return msg
