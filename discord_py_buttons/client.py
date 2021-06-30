from typing import List, SupportsAbs, overload
from .tools import jsonifyMessage, V8Route
from .receive import Message, getResponseMessage

import discord
from discord.ext import commands


class Buttons():
    """
    A button instance for using buttons
    
    - - -

    Attributes
    ----------------
    send: `function`
        Sends a message to a `discord.TextChannel`
    
    """
    def __init__(self, client: commands.Bot):
        """
        This will create a new button intearction Listener

        For receiving the button event, scroll down to the bottom and take a look at the example

        - - -

        Parameters
        ------------------
        client: `commands.Bot`
            The discord bot client

        - - -

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
        user = discord.Member(data=data["member"], guild=guild, state=self._discord._connection)
        
        msg = await getResponseMessage(self._discord, data, user, True)

        self._discord.dispatch("button_press", msg.pressedButton, msg)
    

    async def send(self, channel: discord.TextChannel, content=None, *, tts=False,
            embed=None, embeds=None, file: discord.File=None, files: List[discord.File]=None, delete_after=None, nonce=None,
            allowed_mentions=None, reference=None, mention_author=None, buttons=None
        ) -> Message:
        """
        Sends a message to a `discord.TextChannel`

        - - -

        Parameters
        -----------------
        channel: `discord.TextChannel`
            The channel where the message is going to be send
        content: `str`
            The message text content
        tts: `bool`
            Whether text-to-speech should be used
        embed: `discord.Embed`
            The embed in the message
        embeds: `List[discord.Embed]`
            A list of embeds for the message
        file: `discord.File`
            The attached file for the message
        file: `List[discord.File]`
            A list of Files which are going to be attached to the messaeg
        delete_after: `float`
            The numbers of seconds after which the message should be deleted
        nonce: `int`
            The nonce to use for sending this message
        allowed_mentions: `discord.AllowedMentions`
            The mentions proceeded in the message
        reference: `discord.MessageReference or discord.Message`
            The message to refer to
        mention_author: `bool`
            Whether the author should be mentioned
        buttons: `List[Button]`
            A list of buttons included in the message

        - - -

        Returns
        ---------------------
        ```py
        (Message)
        ```
            The sent message including buttons
        """
        if type(channel) != discord.TextChannel:
            raise discord.InvalidArgument("Channel must be of type discord.TextChannel")

        payload = jsonifyMessage(content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, buttons=buttons)
        

        route = V8Route("POST", f"/channels/{channel.id}/messages")
        
        r = await self._discord.http.request(route, json=payload)
        msg = await getResponseMessage(self._discord, r, response=False)
            
        if delete_after is not None:
            await msg.delete(delay=delete_after)
        
        return msg