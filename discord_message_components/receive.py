from discord.errors import InvalidArgument
from discord.state import ConnectionState
from .tools import MISSING, V8Route, jsonifyMessage
from .components import Button, LinkButton, SelectMenu, SelectMenuOption

import discord

from typing import List


class Interaction:
    def __init__(self, client, data) -> None:
        self._client = client
        self._state = client._get_state()
        self._application_id = client.user.id
        self.defered = False
        self.interaction = {"token": data["token"], "id": data["id"]}

    async def defer(self, hidden=False):
        """
        ``| coro |``

        This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        This function should be used if the Bot needs more than 15 seconds to respond

        Parameters
        ----------
            hidden: :class:`bool`, optional
                Whether the loading thing should be only visible to the user; default False.

        """
        body = {"type": 5}
        if hidden:
            body["flags"] = 64

        await self._state.http.request(
            V8Route(
                "POST",
                f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
            ),
            json=body,
        )
        self.deferred = True

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
        components=None,
        hidden=False,
        ninjaMode=False,
    ) -> "Message" or None:
        """
        ``| coro |``

        Responds to the interaction

        Parameters
        ----------
        content: :class:`str`, optional
            The raw message content
        tts: `bool`
            Whether the message should be send with text-to-speech
        embed: :class:`discord.Embed`
            The embed for the message
        embeds: List[:class:`discord.Embed`]
            A list of embeds for the message
        file: :class:`discord.File`
            The file which will be attached to the message
        files: List[:class:`discord.File`]
            A list of files which will be attached to the message
        nonce: :class:`int`
            The nonce to use for sending this message
        allowed_mentions: :class:`discord.AllowedMentions`
            Controls the mentions being processed in this message
        mention_author: :class:`bool`
            Whether the author should be mentioned
        components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`]
            A list of message components to be included
        hidden: :class:`bool`
            Whether the response should be visible only to the user
        ninjaMode: :class:`bool`
            If true, the client will respond to the button interaction with almost nothing and returns nothing

        Returns
        -------
        :return: Returns the sent message
        :type: :class:`~Message` | :class:`None`

            .. note::
                If the response is hidden, no message will be returned

        """

        if ninjaMode:
            await self._state.http.request(
                V8Route(
                    "POST",
                    f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
                ),
                json={"type": 6},
            )
            return
        body = jsonifyMessage(
            content=content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            components=components,
        )

        if hidden:
            body["flags"] = 64

        await self._state.http.request(
            V8Route(
                "POST",
                f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
            ),
            json={"type": 4, "data": body},
        )
        if not hidden:
            responseMSG = await self._state.http.request(
                V8Route(
                    "GET",
                    f"/webhooks/{self._application_id}/{self.interaction['token']}/messages/@original",
                )
            )
            return getResponseMessage(self._client, data=responseMSG, response=False)


class SelectedMenu(Interaction, SelectMenu):
    """A `SelectMenu` in which an item was selected"""

    def __init__(self, data, user, s, client) -> None:
        Interaction.__init__(self, client, data)
        SelectMenu.__init__(self, "EMPTY", [SelectMenuOption("EMPTY", "EMPTY")], 0, 0)
        self._json = s.to_dict()
        self.values: List[SelectMenuOption] = []
        """The list of values which were selected
        
        :type: :class:`~SelectMenuOption`
        """

        for val in data["data"]["values"]:
            for x in self.options:
                if x.value == val:
                    self.values.append(x)

        self.member: discord.Member = user
        """The member who selected the value"""


class PressedButton(Interaction, Button):
    """A pressed button"""

    def __init__(self, data, user, b, client) -> None:
        Interaction.__init__(self, client, data)
        Button.__init__(self, "empty", "empty")
        self._json = b.to_dict()

        """interaction: :class:`dict`
        
        The most important stuff from the received interaction
        
        *  ``token``
                The interaction token
        *   ``id``
                The ID for the interaction
        """
        self.member: discord.Member = user
        """The user who pressed the button"""


def getResponseMessage(client, data, user=None, response=True):
    """
    Async function to get the Response Message

    Parameters
    -----------------

    state: :class:`discord.state.ConnectionState`
        The discord bot client
    data: :class:`dict`
        The raw data
    user: :class:`discord.User`
        The User which pressed the button
    response: :class:`bool`
        Whether the Message returned should be of type `ResponseMessage` or `Message`

    Returns
    -------
    :class:`~Message` | :class:`~ResponseMessage`
        The sent message

    .. note::
            If the message comes from an interaction, it will be of type :class:`~ResponseMessage`, if it is sent to a textchannel, it will be of type :class:`~Message`
    """
    channel = client._get_state().get_channel(data["channel_id"])
    if response and user:
        return ResponseMessage(client=client, channel=channel, data=data, user=user)

    return Message(client=client, channel=channel, data=data)


class Message(discord.Message):
    r"""A fixed discord.Message optimized for components"""

    def __init__(self, *, client, channel, data):
        super().__init__(state=client._get_state(), channel=channel, data=data)

        self.client = client
        self.components = []

        self._update_components(data)

    # region attributes
    @property
    def buttons(self):
        """The button components in the message

        :type: List[:class:`~Button` | :class:`~LinkButton`]
        """
        return [x for x in self.components if type(x) in [Button, LinkButton]]

    @property
    def select_menus(self):
        """The select menus components in the message

        :type: List[:class:`~SelectMenu`]
        """
        return [x for x in self.components if type(x) is SelectMenu]

    # endregion

    def _update_components(self, data):
        """Updates the message components"""
        if len(data["components"]) == 0:
            self.components = []
        elif len(data["components"]) > 1:
            # multiple lines
            for componentWrapper in data["components"]:
                # newline
                for index, com in enumerate(componentWrapper["components"]):
                    if com["type"] == 2:
                        self.components.append(
                            Button._fromData(com, index == 0)
                            if "url" not in com
                            else LinkButton._fromData(com, index == 0)
                        )
                    elif com["type"] == 3:
                        self.components.append(SelectMenu._fromData(com))
        elif len(data["components"][0]["components"]) > 1:
            # All inline
            for index, com in enumerate(data["components"][0]["components"]):
                if com["type"] == 2:
                    self.components.append(
                        Button._fromData(com, index == 0)
                        if "url" not in com
                        else LinkButton._fromData(com, index == 0)
                    )
                elif com["type"] == 3:
                    self.components.append(SelectedMenu._fromData(com))
        else:
            # One button
            type = int(data["components"][0]["components"][0]["type"])
            component = data["components"][0]["components"][0]

            if type == 2:
                self.components.append(
                    Button._fromData(component)
                    if "url" not in component
                    else LinkButton._fromData(component)
                )
            elif type == 3:
                self.components.append(SelectedMenu._fromData(component))
            else:
                print("unknown component type")

    def _update(self, data):
        super()._update(data)
        self._update_components(data)

    async def edit(
        self,
        *,
        content=None,
        embed=None,
        embeds=None,
        suppress=None,
        delete_after=None,
        allowed_mentions=None,
        components=None,
    ):
        """

        ``| coro |``

        Edits the message and updates its properties

        Parameters
        ----------------
        content: :class:`str`
            The new message content
        embded: :class:`discord.Embed`
            The new discord embed
        embeds: List[:class:`discord.Embed`]
            The new list of discord embeds
        supress: :class:`bool`
            Whether the embeds should be shown
        delete_after: :class:`float`
            After how many seconds the message should be deleted
        allowed_mentions: :class:`discord.AllowedMentions`
            The mentions proceeded in the message
        components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`]
            A list of components to be included the message
        """
        payload = jsonifyMessage(
            content,
            embed=embed,
            embeds=embeds,
            allowed_mentions=allowed_mentions,
            suppress=suppress,
            flags=self.flags.value,
            components=components,
        )
        data = await self._state.http.edit_message(self.channel.id, self.id, **payload)
        self._update(data)

        if delete_after is not None:
            await self.delete(delay=delete_after)

    async def wait_for(
        self, event_name, custom_id=MISSING
    ) -> PressedButton or SelectedMenu:
        """
        ``| coro |``

        Waits for a message component activation on the message

        Parameters
        -----------
        event_name: :class:`str`
            The name of the event which will be awaited

            .. note::

                The event_name must be ``select`` for a select menu selection and ``button`` for a button press

        Returns
        ----------
        :returns: The component was waited waited for
        :type: :class:`~PressedButton` | :class:`~SelectedMenu`
        """
        if event_name == "button" or event_name == "select":

            def check(btn, msg):
                if msg.id == self.id:
                    if custom_id is not MISSING:
                        if btn.custom_id == custom_id:
                            return True
                    return True

            return (
                await self.client.wait_for(
                    "button_press" if event_name == "button" else "menu_select",
                    check=check,
                )
            )[0]
        else:
            raise InvalidArgument(
                "Invalid event name, event must be 'button' or 'select', not "
                + str(event_name)
            )


class ResponseMessage(Interaction, Message):
    r"""A message Object which extends the `Message` Object optimized for an interaction component"""

    def __init__(self, *, client, channel, data, user):
        Interaction.__init__(self, client, data)
        Message.__init__(self, client=client, channel=channel, data=data["message"])

        self._application_id = client.user.id
        self.interaction_component = None

        if int(data["data"]["component_type"]) == 2:
            for x in self.buttons:
                if hasattr(x, "custom_id") and x.custom_id == data["data"]["custom_id"]:
                    self.interaction_component = PressedButton(
                        data, user, x, self._client
                    )
        elif int(data["data"]["component_type"]) == 3:
            for x in self.select_menus:
                if x.custom_id == data["data"]["custom_id"]:
                    self.interaction_component = SelectedMenu(
                        data, user, x, self._client
                    )
