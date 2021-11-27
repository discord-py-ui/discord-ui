"""https://github.com/discord-py-ui/discord-ui/blob/main/discord_ui/override.py

    This module overrides some methods of the discord's functions.
    This overrides the Messageable.send, Webhook.send, the Message.__new__ method (whenever a new Message is created, it will use our own Message type)
    The same goes for the WebhookMessage, it will be overriden by our own Webhook type.
    And last but not least, if you're using dpy 2, the discord.ext.commands.Bot will be overriden with our
    own class, which enables `enable_debug_events` in order for our lib to work
"""
from .tools import MISSING
from .receive import Message
from .http import get_message_payload, BetterRoute, send_files

import discord

import sys

def override_dpy():
    """This function overrides default dpy objects. 
    You shouldn't need to use this method by your own, the lib overrides everything that needs to be 
    overriden by default"""
    # override for dpy forks
    module = sys.modules[discord.__name__]

    #region message override
    async def send(self: discord.TextChannel, content=None, **kwargs) -> Message:
        channel = await self._get_channel()
        route = BetterRoute("POST", f"/channels/{channel.id}/messages")
        
        listener = None
        if kwargs.get("listener") is not None:
            listener = kwargs.pop("listener")
        if kwargs.get("components") is None and listener is not None:
            kwargs["components"] = listener.to_components()
        r = None
        if kwargs.get("file") is None and kwargs.get("files") is None:
            payload = get_message_payload(content=content, **kwargs)
            r = await self._state.http.request(route, json=payload)
        else:
            if kwargs.get("file") is not None:
                files = [kwargs.pop("file")]
            elif kwargs.get("files") is not None:
                files = kwargs.pop("files")
            
            payload = get_message_payload(content=content, **kwargs)
            r = await send_files(route, files=files, payload=payload, http=self._state.http)
        
        msg = Message(state=self._state, channel=channel, data=r)
        if kwargs.get("delete_after") is not None:
            await msg.delete(delay=kwargs.pop("delete_after"))
    
        if listener is not None:
            listener._start(msg)

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
    def send_webhook(self: discord.Webhook, content=MISSING, *, wait=False, username=MISSING, avatar_url=MISSING, tts=False, files=None, embed=MISSING, embeds=MISSING, allowed_mentions=MISSING, components=MISSING):
        payload = get_message_payload(content, tts=tts, embed=embed, embeds=embeds, allowed_mentions=allowed_mentions, components=components)

        if username is not None:
            payload["username"] = username
        if avatar_url is not None:
            payload["avatar_url"] = str(avatar_url)
        
        return self._adapter.execute_webhook(payload=payload, wait=wait, files=files)

    module.webhook.Webhook.send = send_webhook
    #endregion

    # override for dpy forks
    sys.modules[discord.__name__] = module