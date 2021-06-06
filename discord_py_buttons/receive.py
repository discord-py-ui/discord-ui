import discord
from discord.ext import commands
from .apiRequests import POST, url, jsonifyMessage
from .buttons import Button, LinkButton
from typing import List

class PressedButton(object):
    def __init__(self, data, user, b) -> None:
        self.interaction = {
            "token": data["token"],
            "id": data["id"]
        }
        self.member: discord.Member = user

        if hasattr(b, "url"):
            self.url = b.url
            self.label = b.label
            self.disabled = b.disabled
        else:
            self.custom_id = b.custom_id
            self.color = b.color
            self.label = b.label
            self.disabled = b.disabled

async def getResponseMessage(client: commands.Bot, data, user = None, response = True):
    channel = await client.fetch_channel(data["channel_id"])
    if response and user:
        return ResponseMessage(state=client._connection, channel=channel, data=data, user=user, client=client)

    return Message(state=client._connection, channel=channel, data=data)

class Message(discord.Message):
    def __init__(self, *, state, channel, data):
        super().__init__(state=state, channel=channel, data=data)

        self.buttons: List[Button] = []
        #print(data)
        if len(data["components"]) > 1:
            for componentWrapper in data["components"]:
                for btn in componentWrapper["components"]:
                    self.buttons.append(Button._fromData(btn) if not "url" in btn else LinkButton._fromData(btn))
        elif len(data["components"][0]["components"]) > 1:
            for btn in data["components"][0]["components"]:
                self.buttons.append(Button._fromData(btn) if not "url" in btn else LinkButton._fromData(btn))
        else:
            self.buttons.append(Button._fromData(data["components"][0]["components"][0]) if not "url" in data["components"][0]["components"][0] else LinkButton._fromData(data["components"][0]["components"][0]))

class ResponseMessage(Message):
    def __init__(self, *, state, channel, data, user, client):
        super().__init__(state=state, channel=channel, data=data["message"])

        self._discord = client
        for x in self.buttons:
            if hasattr(x, 'custom_id') and x.custom_id == data["data"]["custom_id"]:
                self.pressedButton = PressedButton(data, user, x)

    def acknowledge(self):
        r = POST(self._discord.http.token, f'{url}/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
            "type": 5
        })

    def respond(self, content=None, *, tts=False,
            embed=None, file=None, files=None, delete_after=None, nonce=None,
            allowed_mentions=None, reference=None, mention_author=None, buttons=None,
        ninjaMode = False):
        if ninjaMode:
            r = POST(self._discord.http.token, f'https://discord.com/api/v8/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
                "type": 6
            })
        else:
            json = jsonifyMessage(content = content, embed=embed, file=file, files=files, buttons=buttons)
            if "embed" in json:
                json["embeds"] = [json["embed"]]
                del json["embed"]

            r = POST(self._discord.http.token, f'https://discord.com/api/v8/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
                "type": 4,
                "data": json
            })
        if r.status_code == 400:
            raise Exception(r.text)
        