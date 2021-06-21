from .buttons import Button, LinkButton
from .apiRequests import POST, url, jsonifyMessage

import discord
from discord.ext import commands

from typing import List


class PressedButton(Button):
    """Represents a pressed button

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
        self.interaction = {"token": data["token"], "id": data["id"]}
        self.member: discord.Member = user


async def getResponseMessage(client: commands.Bot, data, user=None, response=True):
    """
    Async function to get the Response Message


    Parameters
    -----------------

    ```py
    (commands.Bot) client
    ```
        The discord bot client
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
        Whether the Message returned should be of type `ResponseMessage` or `Message`

    Returns
    -----------------
    ```py
    (ResponseMessage or Message)
    ```
    """
    channel = await client.fetch_channel(data["channel_id"])
    if response and user:
        return ResponseMessage(
            state=client._connection,
            channel=channel,
            data=data,
            user=user,
            client=client,
        )

    return Message(state=client._connection, channel=channel, data=data)


class Message(discord.Message):
    r"""A fixed discord.Message optimized for buttons

    Added attributes
    ----------------
    buttons: `List[Button]`
        The Buttons the message contains

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
                        if "url" not in btn
                        else LinkButton._fromData(btn, index == 0)
                    )
        elif len(data["components"][0]["components"]) > 1:
            # All inline
            for index, btn in enumerate(data["components"][0]["components"]):
                self.buttons.append(
                    Button._fromData(btn, index == 0)
                    if "url" not in btn
                    else LinkButton._fromData(btn, index == 0)
                )
        else:
            # One button
            self.buttons.append(
                Button._fromData(data["components"][0]["components"][0])
                if "url" not in data["components"][0]["components"][0]
                else LinkButton._fromData(data["components"][0]["components"][0])
            )


class ResponseMessage(Message):
    r"""A message Object which extends the `Message` Object optimized for an interaction button (pressed button)

    Added attributes
    ----------------
    pressedButton: `PressedButton`
        The button which was presed
    acknowledge: `function`
        Function to acknowledge the button-press interaction
    respond: `function`
        Function to respond to the buttonPress interaction
    acknowledged: `bool`
        Whether the button was acknowledged with the acknowledge functionn

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
        self.acknowledged = False
        for x in self.buttons:
            if hasattr(x, "custom_id") and x.custom_id == data["data"]["custom_id"]:
                self.pressedButton = PressedButton(data, user, x)

    def acknowledge(self):
        """
        This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        This function should be used if the Bot needs more than 15 seconds to respond
        """

        r = POST(
            self._discord.http.token,
            f'{url}/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback',
            {"type": 5},
        )
        if r.status_code == 403:
            raise discord.ClientException(r.json(), "forbidden")

        self.acknowledged = True

    async def respond(
        self,
        content=None,
        *,
        tts=False,
        embed=None,
        embeds=None,
        file=None,
        files=None,
        nonce=None,
        allowed_mentions=None,
        mention_author=None,
        buttons=None,
        ninjaMode=False,
    ) -> Message or None:
        """
        | coro |

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
            Whether the message should be send with text-to-speech
        ```py
        (discord.Embed) embed
        ```
            The embed for the message
        ```py
        (List[discord.Embed]) embeds
        ```
            A list of embeds for the message
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
        (bool) mention_author
        ```
            Whether the author should be mentioned
        ```py
        List[Button] buttons
        ```
            A list of Buttons for the message to be included

        ```py
        (bool) ninjaMode
        ```
            If true, the client will respond to the button interaction with almost nothing and returns nothing

        Returrns
        -----------------------
        ```py
        (Message or None)
        ```
        The sent message if ninjaMode is false, otherwise `None`

        """
        msg = None
        if not ninjaMode:
            json = jsonifyMessage(
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                file=file,
                files=files,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                reference=discord.MessageReference(
                    message_id=self.id, channel_id=self.channel.id
                ),
                mention_author=mention_author,
                buttons=buttons,
            )
            r = POST(
                token=self._discord.http.token,
                URL=(url + f"/channels/{self.channel.id}/messages"),
                data=json,
            )
            msg = await getResponseMessage(self._discord, r.json(), response=False)

        r = POST(
            self._discord.http.token,
            f'https://discord.com/api/v8/interactions/{self.pressedButton.interaction["id"]}/{self.pressedButton.interaction["token"]}/callback',
            {"type": 6},
        )

        if r.status_code == 403:
            raise discord.ClientException(r.json(), "Forbidden")
        if r.status_code == 400:
            raise discord.ClientException(r.json(), "Error while sending message")

        return msg
