# https://github.com/discord-py-ui/discord-ui/blob/main/discord_ui/override.py
# 404kuso was here hehehe
#
#       This module overrides some methods of the discord's functions.
#       This overrides the Messageable.send, Webhook.send, the Message.__new__ method (whenever a new Message is created, it will use our own Message type)
#       The same goes for the WebhookMessage, it will be overriden by our own Webhook type.
#       And last but not least, if you're using dpy 2, the discord.ext.commands.Bot will be overriden with our
#       own class, which enables `enable_debug_events` in order for our lib to work


from .tools import MISSING, _or
from .receive import Message, WebhookMessage
from .http import jsonifyMessage, BetterRoute, send_files

import discord
from discord.ext import commands

import sys

def override_dpy():
    """This method overrides dpy methods. You shouldn't need to use this method by your own, the lib overrides everything by default"""
    module = sys.modules["discord"]

    #region message override
    async def send(self: discord.TextChannel, content=None, **kwargs) -> Message:


        channel_id = self.id if type(self) is not commands.Context else self.channel.id
        route = BetterRoute("POST", f"/channels/{channel_id}/messages")
        
        r = None
        if kwargs.get("file") is None and kwargs.get("files") is None:
            payload = jsonifyMessage(content=content, **kwargs)
            r = await self._state.http.request(route, json=payload)
        else:
            if kwargs.get("file") is not None:
                files = [kwargs.pop("file")]
            elif kwargs.get("files") is not None:
                files = kwargs.pop("files")
            payload = jsonifyMessage(content=content, **kwargs)
            r = await send_files(route, files=files, payload=payload, http=self._state.http)
        
        msg = Message(state=self._state, channel=self if type(self) is not commands.Context else self.channel, data=r)
        if kwargs.get("delete_after") is not None:
            await msg.delete(delay=kwargs.get("delete_after"))
    
        return msg
    def message_override(cls, *args, **kwargs):
        if cls is discord.message.Message:
            return object.__new__(Message)
        else:
            return object.__new__(cls)


    module.abc.Messageable.send = send
    module.message.Message.__new__ = message_override
    #endregion

    #region webhook override
    def webhook_message_override(cls, *args, **kwargs):
        if cls is discord.webhook.WebhookMessage:
            return object.__new__(WebhookMessage)
        else:
            return object.__new__(cls)
    def send_webhook(self: discord.Webhook, content=MISSING, *, wait=False, username=MISSING, avatar_url=MISSING, tts=False, files=None, embed=MISSING, embeds=MISSING, allowed_mentions=MISSING, components=MISSING):
        payload = jsonifyMessage(content, tts=tts, embed=embed, embeds=embeds, allowed_mentions=allowed_mentions, components=components)

        if username is not None:
            payload["username"] = username
        if avatar_url is not None:
            payload["avatar_url"] = str(avatar_url)
        
        return self._adapter.execute_webhook(payload=payload, wait=wait, files=files)

    module.webhook.Webhook.send = send_webhook
    module.webhook.WebhookMessage.__new__ = webhook_message_override
    #endregion

    class OverridenV2Bot(commands.bot.Bot):
        """A overriden client that enables `enable_debug_events` for receiving the events"""
        def __init__(self, command_prefix, help_command = None, description = None, **options):
            commands.bot.Bot.__init__(self, command_prefix, help_command=help_command, description=description, enable_debug_events=True, **options)

    def client_override(cls, *args, **kwargs):
        if cls is commands.bot.Bot:
            return object.__new__(OverridenV2Bot)
        else:
            return object.__new__(cls)

    if discord.__version__.startswith("2"):
        module.ext.commands.bot.Bot.__new__ = client_override


    sys.modules["discord"] = module
