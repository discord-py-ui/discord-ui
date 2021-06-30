from .buttons import Button, LinkButton
from .tools import V8Route, jsonifyMessage

import discord
from discord.ext import commands

from typing import List

class PressedButton(Button):
    """Represents a pressed button
    
    - - -

    Attributes
    ----------------
    interaction: `dict`
        The most important stuff from the received interaction
        - `token`: The interaction token
        - `id`: The ID for the interaction

    member: `discord.Member`
        The guild member who pressed the button
    custom_id: `str`
        The custom_id for the button to identify it
    label: `str`
        The text appearing on the button
    emoji: `discord.Emoji or str`
        The emoji appearing before the label
    color: `int`
        The buttons color style.
        For the values, take a look at `Colors`
    new_line: `bool`
        If a new line was added before the button
    disabled: `bool`
        Whether the button is disabled
    hash: `str`
        A unique hash for the button
    """
    def __init__(self, data, user, b: Button) -> None:
        super().__init__("empty", "empty")
        self._json = b.to_dict()
        self.interaction = {
            "token": data["token"],
            "id": data["id"]
        }
        self.member: discord.Member = user

async def getResponseMessage(client: commands.Bot, data, user = None, response = True):
    """
    Async function to get the Response Message

    - - -

    Parameters
    -----------------

    client: `commands.Bot`
        The discord bot client
    data: `dict`
        The raw data
    user: `discord.User`
        The User which pressed the button
    response
        Whether the Message returned should be of type `ResponseMessage` or `Message`

    - - -

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
    r"""A fixed discord.Message optimized for buttons

    - - -

    Added attributes
    ----------------
    buttons: `List[Button]`
        The Buttons the message contains
    edit: `function` [patched]
        A fixed edit function with button support
    
    - - -

    Attributes
    ----------------
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: :class:`abc.User`
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has the left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
    nonce
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is not stored long term within Discord's servers and is only used ephemerally.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    channel: Union[:class:`abc.Messageable`]
        The :class:`TextChannel` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    call: Optional[:class:`CallMessage`]
        The call that the message refers to. This is only applicable to messages of type
        :attr:`MessageType.call`.

        .. deprecated:: 1.7

    reference: Optional[:class:`~discord.MessageReference`]
        The message that this message references. This is only applicable to messages of
        type :attr:`MessageType.pins_add`, crossposted messages created by a
        followed channel integration, or message replies.

        .. versionadded:: 1.5

    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    mentions: List[:class:`abc.User`]
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a Discord limitation, not one with the library.
    channel_mentions: List[:class:`abc.GuildChannel`]
        A list of :class:`abc.GuildChannel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: List[:class:`Role`]
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: :class:`int`
        The message ID.
    webhook_id: Optional[:class:`int`]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    flags: :class:`MessageFlags`
        Extra features of the message.

        .. versionadded:: 1.3

    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`dict`]
        The rich presence enabled application associated with this message.

        It is a dictionary with the following keys:

        - ``id``: A string representing the application's ID.
        - ``name``: A string representing the application's name.
        - ``description``: A string representing the application's description.
        - ``icon``: A string representing the icon ID of the application.
        - ``cover_image``: A string representing the embed's image asset ID.
    stickers: List[:class:`Sticker`]
        A list of stickers given to the message.


    ### For more information, take a look at the `discord.Message` object
    """
    def __init__(self, *, state, channel, data):
        super().__init__(state=state, channel=channel, data=data)

        self.buttons: List[Button] = []
        self._update_components(data)
        
    def _update_components(self, data):
        """Updates the message components"""
        if len(data["components"]) == 0:
            self.buttons = []
        elif len(data["components"]) > 1:
            # multiple lines
            for componentWrapper in data["components"]:
                # newline
                for index, btn in enumerate(componentWrapper["components"]):
                    # Button in this line
                    self.buttons.append(
                        Button._fromData(btn, index == 0)
                            if "url" not in btn else 
                        LinkButton._fromData(btn, index == 0)
                    )
        elif len(data["components"][0]["components"]) > 1:
            # All inline
            for index, btn in enumerate(data["components"][0]["components"]):
                self.buttons.append(Button._fromData(btn, index == 0) if "url" not in btn else LinkButton._fromData(btn, index == 0))
        else:
            # One button
            self.buttons.append(Button._fromData(data["components"][0]["components"][0]) if "url" not in data["components"][0]["components"][0] else LinkButton._fromData(data["components"][0]["components"][0]))
    def _update(self, data):
        super()._update(data)
        self._update_components(data)

    async def edit(self, *, content: str = None, embed: discord.Embed = None, embeds: List[discord.Embed] = None, attachments: List[discord.Attachment] = None, suppress: bool = None, delete_after: float = None, allowed_mentions: discord.AllowedMentions = None, buttons: List[Button or LinkButton] = None):
        """
        | coro |
        
        Edits the message

        - - -

        Parameters
        ----------------
        content: `str`
            The new message content
        embded: `discord.Embed`
            The new discord embed
        embeds: `List[discord.Embed]`
            The new list of discord embeds
        attachments: `List[discord.Attachments]`
            A list of new attachments
        supress: `bool`
            Whether the embeds should be shown
        delete_after: `float`
            After how many seconds the message should be deleted
        allowed_mentions: `discord.AllowedMentions`
            The mentions proceeded in the message
        buttons: `List[Button]`
            A list of buttons in the message
        """
        payload = jsonifyMessage(content, embed=embed, embeds=embeds, allowed_mentions=allowed_mentions, suppress=suppress, flags=self.flags.value, buttons=buttons)
        data = await self._state.http.edit_message(self.channel.id, self.id, **payload)
        self._update(data)

        if delete_after is not None:
            await self.delete(delay=delete_after)
class ResponseMessage(Message):
    r"""A message Object which extends the `Message` Object optimized for an interaction button (pressed button)

    - - -

    Added attributes
    ----------------
    pressedButton: `PressedButton`
        The button which was presed
    defer: `function`
        Function to defer the button-press interaction
    respond: `function`
        Function to respond to the buttonPress interaction
    deferred: `bool`
        Whether the button was deferred with the defer functionn

    - - -

    Attributes
    ----------------
    buttons: `List[Button]`
        The Buttons the message contains

    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a discord limitation.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: :class:`abc.User`
        A :class:`Member` that sent the message. If :attr:`channel` is a
        private channel or the user has the left the guild, then it is a :class:`User` instead.
    content: :class:`str`
        The actual contents of the message.
    nonce
        The value used by the discord guild and the client to verify that the message is successfully sent.
        This is not stored long term within Discord's servers and is only used ephemerally.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    channel: Union[:class:`abc.Messageable`]
        The :class:`TextChannel` that the message was sent from.
        Could be a :class:`DMChannel` or :class:`GroupChannel` if it's a private message.
    call: Optional[:class:`CallMessage`]
        The call that the message refers to. This is only applicable to messages of type
        :attr:`MessageType.call`.

        .. deprecated:: 1.7

    reference: Optional[:class:`~discord.MessageReference`]
        The message that this message references. This is only applicable to messages of
        type :attr:`MessageType.pins_add`, crossposted messages created by a
        followed channel integration, or message replies.

        .. versionadded:: 1.5

    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    mentions: List[:class:`abc.User`]
        A list of :class:`Member` that were mentioned. If the message is in a private message
        then the list will be of :class:`User` instead. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a Discord limitation, not one with the library.
    channel_mentions: List[:class:`abc.GuildChannel`]
        A list of :class:`abc.GuildChannel` that were mentioned. If the message is in a private message
        then the list is always empty.
    role_mentions: List[:class:`Role`]
        A list of :class:`Role` that were mentioned. If the message is in a private message
        then the list is always empty.
    id: :class:`int`
        The message ID.
    webhook_id: Optional[:class:`int`]
        If this message was sent by a webhook, then this is the webhook ID's that sent this
        message.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    flags: :class:`MessageFlags`
        Extra features of the message.

        .. versionadded:: 1.3

    reactions : List[:class:`Reaction`]
        Reactions to a message. Reactions can be either custom emoji or standard unicode emoji.
    activity: Optional[:class:`dict`]
        The activity associated with this message. Sent with Rich-Presence related messages that for
        example, request joining, spectating, or listening to or with another member.

        It is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    application: Optional[:class:`dict`]
        The rich presence enabled application associated with this message.

        It is a dictionary with the following keys:

        - ``id``: A string representing the application's ID.
        - ``name``: A string representing the application's name.
        - ``description``: A string representing the application's description.
        - ``icon``: A string representing the icon ID of the application.
        - ``cover_image``: A string representing the embed's image asset ID.
    stickers: List[:class:`Sticker`]
        A list of stickers given to the message.

    ### For more information, take a look at the `buttons.Message` and `discord.Message` objects
    """
    def __init__(self, *, state, channel, data, user, client):
        super().__init__(state=state, channel=channel, data=data["message"])

        self._discord = client
        self.deferred = False
        for x in self.buttons:
            if hasattr(x, 'custom_id') and x.custom_id == data["data"]["custom_id"]:
                self.pressedButton = PressedButton(data, user, x)

    async def defer(self, hidden=False):
        """
        | coro |

        This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        This function should be used if the Bot needs more than 15 seconds to respond
        
        - - -

        Parameters
        ----------------
        hidden: `bool`
            Whether the loading thing will be only visible to the user
            Default: `False`
        
        
        """

        body = {"type": 5}
        if hidden:
            body |= { "flags": 64 }
        
        await self._discord.http.request(V8Route("POST", f'/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback'), json=body)
        self.deferred = True

    async def respond(self, content=None, *, tts=False, embed = None, embeds=None, file=None, files=None, nonce=None,
        allowed_mentions=None, mention_author=None, buttons=None, hidden=False,
        ninjaMode = False) -> Message or None:
        """
        | coro |

        Responds to the interaction

        - - -

        Parameters
        -----------------------
        content: `str`
            The raw message content
        tts: `bool` 
            Whether the message should be send with text-to-speech
        embed: `discord.Embed`
            The embed for the message
        embeds: `List[discord.Embed]`
            A list of embeds for the message
        file: `discord.File`
            The file which will be attached to the message
        files: `List[discord.File]`
            A list of files which will be attached to the message
        nonce: `int`
            The nonce to use for sending this message
        allowed_mentions: `discord.AllowedMentions`
            Controls the mentions being processed in this message
        mention_author: `bool`
            Whether the author should be mentioned
        buttons: `List[Button]`
            A list of Buttons for the message to be included
        hidden: `bool`
            Whether the response should be visible only to the user 
        ninjaMode: `bool`
            If true, the client will respond to the button interaction with almost nothing and returns nothing
        
        - - -
        
        Returns
        -----------------------
        ```py
        (Message or None)
        ```
            The sent message if ninjaMode is false, otherwise `None` 

        """
        if ninjaMode:
            await self._discord.http.request(V8Route("POST", f'/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback'), json={
                "type": 6
            })
            return

        body = jsonifyMessage(content=content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, reference=discord.MessageReference(message_id=self.id, channel_id=self.channel.id), mention_author=mention_author, buttons=buttons)
        
        if hidden:
            body |= {"flags": 64}

        await self._discord.http.request(V8Route("POST", f'/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback'), json={
            "type": 4,
            "data": body
        })
        if not hidden:
            responseMSG = await self._discord.http.request(V8Route("GET", f"/webhooks/{self._discord.user.id}/{self.pressedButton.interaction['token']}/messages/@original"))
            
            return await getResponseMessage(self._discord, responseMSG, response=False)