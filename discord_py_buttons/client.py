import discord
from discord.ext import commands
from .receive import PressedButton

from . import apiRequests
from .receive import Message, getResponseMessage

class Buttons:
    def __init__(self, client: commands.Bot):
        """
        This will create a new Button Listener

        Parameters
        ------------------
        ```py
        (commands.Bot) client
        ```
        The discord Bot client
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
            embed=None, file=None, files=None, delete_after=None, nonce=None,
            allowed_mentions=None, reference=None, mention_author=None, buttons=None
        ) -> Message:
<<<<<<< Updated upstream
        if type(channel) is not discord.TextChannel:
=======
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
        The raw message content
        ```py
        (bool) tts
        ```
        Wheter text-to-speech should be used
        ```py
        (discord.MessageEmbed) embed
        ```
        The embed in the message
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
        (discord.MessageReference) reference
        ```
        The ID or the discord User Object of the message to reference
        ```py
        (bool) mention_author
        ```
        Wheter the author should be mentioned
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
>>>>>>> Stashed changes
            raise discord.InvalidArgument("Channel must be of type discord.TextChannel")
        r = apiRequests.POST(self._discord.http.token, f"{apiRequests.url}/channels/{channel.id}/messages", data=apiRequests.jsonifyMessage(content, tts=tts, embed=embed, file=file, files=files, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, buttons=buttons))
        if(r.status_code != 200):
            raise Exception(r.text)
        msg = await getResponseMessage(self._discord, r.json(), False)
<<<<<<< Updated upstream
        if delete_after is not None:
            await msg.delete(delay=delete_after)

=======
        
        if delete_after is not None:
            await msg.delete(delay=delete_after)
        
>>>>>>> Stashed changes
        return msg