import discord
from discord.ext import commands
from .buttons import Button, LinkButton

class PressedButton(object):
    def __init__(self, data) -> None:
        self.interaction = {
            "token": data["token"],
            "id": data["id"]
        }
        
        if "url" in data["data"]:
            b = LinkButton._fromData(data["data"])
            self.url = b.url
            self.label = b.label
            self.disabled = b.disabled
        else:
            b = Button._fromData(data["data"])
            self.custom_id = b.custom_id
            self.color = b.color
            self.label = b.label
            self.disabled = b.disabled

async def getResponseMessage(client: commands.Bot, data, response = True):
    channel = await client.fetch_channel(data["channel_id"])
    if response:
        return ResponseMessage(state=client._connection, channel=channel, data=data["message"])
    else:
        return Message(state=client._connection, channel=channel, data=data)

class Message(discord.Message):
    def __init__(self, *, state, channel, data):
        super().__init__(state=state, channel=channel, data=data)

        self.buttons: List[Button] = []
        print(data)
        if len(data["components"]) > 1:
            for componentWrapper in data["components"]:
                for btn in componentWrapper["components"]:
                    self.buttons.append(Button._fromData(btn) if not "url" in btn else LinkButton._fromData(btn))
        if len(data["components"][0]["components"]) > 1:
            for btn in data["components"][0]["components"]:
                self.buttons.append(Button._fromData(btn) if not "url" in btn else LinkButton._fromData(btn))
        else:
            self.buttons.append(Button._fromData(data["components"][0]["components"]) if not "url" in data["components"][0]["components"] else LinkButton.from_data(data["components"][0]["components"]))

class ResponseMessage(Message):
    def __init__(self, *, state, channel, data):
        super().__init__(state, channel, data["message"])

        for x in self.buttons:
            if hasattr(x, 'custom_id') and x.custom_id == data["data"]["custom_id"]:
                self.pressedButton = PressedButton(data, x)