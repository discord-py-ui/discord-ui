import discord
from discord.ext import commands

from . import apiRequests
from .receive import Message

class Buttons:
    def __init__(self, client: commands.Bot):
        self._discord = client

    async def send(self, channel: discord.TextChannel, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None, allowed_mentions=None, reference=None, mention_author=None, buttons=None):
        print(apiRequests.jsonifyMessage(content, tts=tts, embed=embed, file=file, files=files, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, buttons=buttons))
        r = apiRequests.POST(self._discord.http.token, f"https://discord.com/api/v8/channels/{channel.id}/messages", data=apiRequests.jsonifyMessage(content, tts=tts, embed=embed, file=file, files=files, nonce=nonce, allowed_mentions=allowed_mentions, reference=reference, mention_author=mention_author, buttons=buttons))
        print(r.text)
        return Message()