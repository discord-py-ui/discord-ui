import discord
from discord.ext import commands
from .apiRequests import POST, url, jsonifyMessage
from .buttons import Button, LinkButton
from typing import List

class PressedButton(object):
    """
    An object for a pressed Button
    
    #### There should be no need to initialize a new instance of this type
    """
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
    """
    Async function to get the Response Message
    
    Should not be needed to be executed

    Parameters
    -----------------

    ```py
    (commands.Bot) client
    ```
    The Discord Bot Client
    ```py
    (json) data
    ```
    The raw data
    ```py
    (discord.User) user
    ```
    The User which pressed the button
    ```py
    response
    ```
    Wheter the Message returned should be of type `ResponseMessage` or `Message`

    Returns
    -----------------
    ```py
    (ResponseMessage or Message)
    ```
    """
    channel = await client.fetch_channel(data["channel_id"])
    if response and user:
        return ResponseMessage(state=client._connection, channel=channel, data=data, user=user, client=client)

    return Message(state=client._connection, channel=channel, data=data)

class Message(discord.Message):
    """
    A fixed message object with added properties like `buttons`

    #### There should be no need to initialize a new instance of this type
    """
    def __init__(self, *, state, channel, data):
        super().__init__(state=state, channel=channel, data=data)

        self.buttons: List[Button] = []
        #print(data)
        if len(data["components"]) > 1:
            for componentWrapper in data["components"]:
                for btn in componentWrapper["components"]:
                    self.buttons.append(Button._fromData(btn) if "url" not in btn else LinkButton._fromData(btn))
        elif len(data["components"][0]["components"]) > 1:
            for btn in data["components"][0]["components"]:
                self.buttons.append(Button._fromData(btn) if "url" not in btn else LinkButton._fromData(btn))
        else:
            self.buttons.append(Button._fromData(data["components"][0]["components"][0]) if "url" not in data["components"][0]["components"][0] else LinkButton._fromData(data["components"][0]["components"][0]))

class ResponseMessage(Message):
    """
    A fixed message Object which extends the `Message` Object with some added properties:

    #### There should be no need to initialize a new instance of this type

    - `(PressedButton) pressedButton`
    - `(function) acknowledge`
    - `(function) respond`
    """
    def __init__(self, *, state, channel, data, user, client):
        super().__init__(state=state, channel=channel, data=data["message"])

        self._discord = client
        for x in self.buttons:
            if hasattr(x, 'custom_id') and x.custom_id == data["data"]["custom_id"]:
                self.pressedButton = PressedButton(data, user, x)

    def acknowledge(self):
        """
        This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        This function should be used if the Bot needs more than 15 seconds to respond
        """

        r = POST(self._discord.http.token, f'{url}/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
            "type": 5
        })

    def respond(self, content=None, *, tts=False,
            embed=None, file=None, files=None, nonce=None,
            allowed_mentions=None, reference=None, buttons=None,
        ninjaMode = False):
        """
        Function to respond to the interaction


        Parameters
        -----------------------
        ```py
        (str) content
        ```
        The raw message content
        ```py
        (bool) tts
        ```
        Wheter the message should be send with text-to-speech
        ```py
        (discord.Embed) embed
        ```
        The embed for the message
        ```py
        (discord.File) file
        ```
        The file which will be attached to the message
        ```py
        (List[discord.File]) files
        ```
        A list of files which will be attached to the message
        ```py
        (int) nonce
        ```
        The nonce to use for sending this message
        ```py
        (discord.AllowedMentions) allowed_mentions
        ```
        Controls the mentions being processed in this message
        ```py
        (discord.MessageReference) reference 
        ```
        The message to refer
        ```py
        List[Button] buttons
        ```
        A list of Buttons for the message to be included

        ```py
        (bool) ninjaMode
        ```
        If true, the client will respond to the button interaction with almost nothing
        """
        if ninjaMode:
            r = POST(self._discord.http.token, f'https://discord.com/api/v8/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
                "type": 6
            })
        else:
            json = jsonifyMessage(content=content, embed=embed, file=file, files=files, nonce=nonce, buttons=buttons)
            if "embed" in json:
                json["embeds"] = [json["embed"]]
                del json["embed"]

            r = POST(self._discord.http.token, f'https://discord.com/api/v8/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback', {
                "type": 4,
                "data": json
            })
        if r.status_code == 400:
            raise discord.HTTPException(r.text)
        