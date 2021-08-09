from discord.state import ConnectionState
from .slash.types import SlashCommand, SubSlashCommand
from .tools import MISSING
from .http import BetterRoute, jsonifyMessage, send_files
from .components import ActionRow, Button, LinkButton, SelectMenu, SelectOption

import discord
from discord.ext import commands as com
from discord.errors import HTTPException, InvalidArgument
import typing


class Interaction:
    def __init__(self, application_id, state, data, user=MISSING) -> None:
        self._application_id = application_id
        self._state: ConnectionState = state

        self._deferred = False
        self._deferred_hidden = False
        self._responded = False

        if user is not MISSING:
            self.member = user
            """The user who created the interaction
            
            :type: :class:`discord.Member`
            """
        self.interaction = {"token": data["token"], "id": data["id"]}

    async def defer(self, hidden=False):
        """This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        .. note::

            This function should be used if the bot needs more than 15 seconds to respond

        Parameters
        ----------
            hidden: :class:`bool`, optional
                Whether the loading thing should be only visible to the user; default False.

        """
        if self._deferred:
            raise Exception("interaction was already deferred")
        body = {"type": 5}

        if hidden is True:
            body["data"] = {"flags": 64}
            self._deferred_hidden = True

        await self._state.http.request(
            BetterRoute(
                "POST",
                f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
            ),
            json=body,
        )
        self._deferred = True

    async def respond(
        self,
        content=MISSING,
        *,
        tts=False,
        embed=MISSING,
        embeds=MISSING,
        file=MISSING,
        files=MISSING,
        nonce=MISSING,
        allowed_mentions=MISSING,
        mention_author=MISSING,
        components=MISSING,
        delete_after=MISSING,
        hidden=False,
        ninja_mode=False,
    ) -> typing.Union["Message", "EphemeralMessage"]:
        """Responds to the interaction

        Parameters
        ----------
        content: :class:`str`, optional
            The raw message content
        tts: :class:`bool`
            Whether the message should be send with text-to-speech
        embed: :class:`discord.Embed`
            Embed rich content
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
        delete_after: :class:`float`
            After how many seconds the message should be deleted, only works for non-hiddend messages; default MISSING
        hidden: :class:`bool`
            Whether the response should be visible only to the user
        ninja_mode: :class:`bool`
            If true, the client will respond to the button interaction with almost nothing and returns nothing

        Returns
        -------
        :return: Returns the sent message
        :type: :class:`~Message` | :class:`EphemeralMessage`

            .. note::

                If the response is hidden, a EphemeralMessage will be returned, which is an empty class

        """

        if ninja_mode:
            try:
                await self._state.http.request(
                    BetterRoute(
                        "POST",
                        f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
                    ),
                    json={"type": 6},
                )
            except HTTPException as x:
                if "value must be one of (4, 5)" in str(x).lower():
                    print(
                        x,
                        "The 'ninja_mode' parameter is not supported for slash commands!",
                    )
                else:
                    print(x)
            finally:
                return

        if self._responded:
            await self.send(
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                mention_author=mention_author,
                components=components,
                hidden=hidden,
            )
            return

        payload = jsonifyMessage(
            content=content,
            tts=tts,
            embed=embed,
            embeds=embeds,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            mention_author=mention_author,
            components=components,
        )

        hide_message = self._deferred_hidden or not self._deferred and hidden

        if delete_after is not MISSING and hide_message is True:
            raise InvalidArgument(
                "Cannot delete hidden message (delete_after won't work)"
            )

        if hide_message:
            payload["flags"] = 64

        if (
            (file is not MISSING or files is not MISSING)
            and self._deferred is False
            or (hide_message is True and not self._deferred)
        ):
            await self.defer(hidden=hide_message)

        if not self._deferred:
            route = BetterRoute(
                "POST",
                f'/interactions/{self.interaction["id"]}/{self.interaction["token"]}/callback',
            )
            await self._state.http.request(route, json={"type": 4, "data": payload})
        else:
            route = BetterRoute(
                "PATCH",
                f'/webhooks/{self._application_id}/{self.interaction["token"]}/messages/@original',
            )
            r = await self._state.http.request(route, json=payload)
            if hide_message:
                self._responded = True
                return EphemeralMessage(
                    state=self._state,
                    channel=self._state.get_channel(int(r["channel_id"])),
                    data=r,
                )

        if file is not MISSING and files is not MISSING:
            await send_files(
                route=BetterRoute(
                    "PATCH",
                    f"/webhooks/{self._application_id}/{self.interaction['token']}/messages/@original",
                ),
                files=[file] if files is MISSING else files,
                payload=payload,
                http=self._state.http,
            )

        if not hide_message:
            responseMSG = await self._state.http.request(
                BetterRoute(
                    "GET",
                    f"/webhooks/{self._application_id}/{self.interaction['token']}/messages/@original",
                )
            )
            msg = await getResponseMessage(
                self._state,
                data=responseMSG,
                application_id=self._application_id,
                response=False,
            )
            if delete_after is not MISSING:
                await msg.delete(delete_after)
            return msg

    async def send(
        self,
        content=None,
        *,
        tts=False,
        embed=MISSING,
        embeds=MISSING,
        file=MISSING,
        files=MISSING,
        nonce=MISSING,
        allowed_mentions=MISSING,
        mention_author=MISSING,
        components=MISSING,
        hidden=False,
    ) -> typing.Union["Message", "EphemeralMessage"]:
        """Sends a message to the interaction using a webhook

        Parameters
        ----------
        content: :class:`str`, optional
            The raw message content
        tts: `bool`
            Whether the message should be send with text-to-speech
        embed: :class:`discord.Embed`
            Embed rich content
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
        ninja_mode: :class:`bool`
            If true, the client will respond to the button interaction with almost nothing and returns nothing

        Returns
        -------
        :return: Returns the sent message
        :type: :class:`~Message` | :class:`EphemeralMessage`

            .. note::
                If the response is hidden, a EphemeralMessage will be returned, which is an empty class
        """
        if self._responded is False:
            return await self.respond(
                content=content,
                tts=tts,
                embed=embed,
                embeds=embeds,
                nonce=nonce,
                allowed_mentions=allowed_mentions,
                mention_author=mention_author,
                components=components,
                hidden=hidden,
            )

        payload = jsonifyMessage(
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
            payload["flags"] = 64

        route = BetterRoute(
            "POST", f'/webhooks/{self._application_id}/{self.interaction["token"]}'
        )
        r = await self._state.http.request(route, json=payload)

        if file is not MISSING and files is not MISSING:
            await send_files(
                route=BetterRoute(
                    "PATCH",
                    f"/webhooks/{self._application_id}/{self.interaction['token']}/messages/@original",
                ),
                files=[file] if files is MISSING else files,
                payload=payload,
                http=self._state.http,
            )

        if hidden:
            return EphemeralMessage(
                state=self._state,
                channel=self._state.get_channel(int(r["channel_id"])),
                data=r,
            )

        return await getResponseMessage(self._state, r, response=False)


class SelectedMenu(Interaction, SelectMenu):
    """A :class:`~SelectMenu` object in which an item was selected"""

    def __init__(self, data, application_id, user, s, state) -> None:
        Interaction.__init__(self, application_id, state, data)
        SelectMenu.__init__(self, "EMPTY", [SelectOption("EMPTY", "EMPTY")], 0, 0)
        self._json = s.to_dict()
        self.values: typing.List[SelectOption] = []
        """The list of values which were selected
        
        :type: :class:`~SelectOption`
        """

        for val in data["data"]["values"]:
            for x in self.options:
                if x.value == val:
                    self.values.append(x)

        self.member: discord.Member = user
        """The member who selected the value"""


class PressedButton(Interaction, Button):
    """A :class:`~Button` object that was pressed"""

    def __init__(self, data, application_id, user, b, state) -> None:
        Interaction.__init__(self, application_id, state, data)
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


class SlashedCommand(Interaction, SlashCommand):
    """A :class:`~SlashCommand` object that was used"""

    def __init__(
        self, client, command: SlashCommand, data, user, channel, guild_ids=None
    ) -> None:
        Interaction.__init__(self, client.user.id, client._connection, data, user)
        SlashCommand.__init__(self, None, "EMPTY", guild_ids)
        self._json = command.to_dict()
        self.member: discord.Member = user
        """The user who created the interaciton"""
        self.channel: discord.TextChannel = channel
        """The channel where the slash command was used"""


class SlashedSubCommand(SlashedCommand, SubSlashCommand):
    """A Sub-:class:`~SlashCommand` command that was used"""

    def __init__(self, client, command, data, user, channel, guild_ids) -> None:
        SlashedCommand.__init__(
            self, client, command, data, user, channel, guild_ids=guild_ids
        )
        SubSlashCommand.__init__(self, None, "EMPTY", "EMPTY")


async def getResponseMessage(
    state: ConnectionState, data, application_id=None, user=None, response=True
):
    """
    Async function to get the response message

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
    channel = state.get_channel(int(data["channel_id"]))
    if response and user:
        if data["message"]["flags"] == 64:
            return EphemeralMessage(state=state, channel=channel, data=data["message"])
        return ResponseMessage(
            state=state,
            application_id=application_id,
            channel=channel,
            data=data,
            user=user,
        )

    return Message(state=state, channel=channel, data=data)


class Message(discord.Message):
    """A fixed :class:`discord.Message` optimized for components"""

    def __init__(self, *, state, channel, data):
        self.__slots__ = discord.Message.__slots__ + ("components", "supressed")

        super().__init__(state=state, channel=channel, data=data)
        self.components: typing.List[typing.Union[Button, LinkButton, SelectMenu]] = []
        """The components in the message
        
        :type: List[]:class:`~Button` | :class:`~LinkButton` | :class:`SelectMenu`]
        """
        self.suppressed = False

        self._update_components(data)

    # region attributes
    @property
    def buttons(self):
        """The button components in the message

        :type: List[:class:`~Button` | :class:`~LinkButton`]
        """
        if hasattr(self, "components") and self.components is not None:
            return [x for x in self.components if type(x) in [Button, LinkButton]]
        return []

    @property
    def select_menus(self):
        """The select menus components in the message

        :type: List[:class:`~SelectMenu`]
        """
        if hasattr(self, "components") and self.components is not None:
            return [x for x in self.components if type(x) is SelectMenu]
        return []

    # endregion

    def _update_components(self, data):
        """Updates the message components"""
        if data.get("components") is None:
            return
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
            component_type = int(data["components"][0]["components"][0]["type"])
            component = data["components"][0]["components"][0]

            if component_type == 2:
                self.components.append(
                    Button._fromData(component)
                    if "url" not in component
                    else LinkButton._fromData(component)
                )
            elif component_type == 3:
                self.components.append(SelectedMenu._fromData(component))
            else:
                print("unknown component type")

    def _update(self, data):
        super()._update(data)
        self._update_components(data)

    async def edit(
        self,
        *,
        content=MISSING,
        embed=MISSING,
        embeds=MISSING,
        attachments=MISSING,
        suppress=MISSING,
        delete_after=MISSING,
        allowed_mentions=MISSING,
        components=MISSING,
    ):
        """Edits the message and updates its properties

        .. note::

            If a paremeter is `None`, the attribute will be removed from the message

        Parameters
        ----------------
        content: :class:`str`
            The new message content
        embed: :class:`discord.Embed`
            Embed rich content
        embeds: List[:class:`discord.Embed`]
            The new list of discord embeds
        attachments: List[:class:`discord.Attachment`]
            A list of new attachments
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
            attachments=attachments,
            suppress=suppress,
            flags=self.flags.value,
            components=components,
        )
        if suppress:
            self.suppressed = suppress
        data = await self._state.http.edit_message(self.channel.id, self.id, **payload)
        self._update(data)

        if delete_after is not MISSING:
            await self.delete(delay=delete_after)

    async def disable_action_row(self, row, disable=True):
        """Disables an action row of components in the message

        Parameters
        ----------
            row: :class:`int` |  :class:`range`
                Which rows to disable, first row is ``0``; If row parameter is of type :class:`int`, the nth row will be disabled, if type is :class:`range`, the range is going to be iterated and all rows in the range will be disabled

            disable: :class:`bool`, optional
                Whether to disable (``True``) or enable (``False``) the components; default True

        Raises
        ------
            :raises: :class:`InvalidArgument` : The specified range was out of the possible range of the component rows
            :raises: :class:`InvalidArgument` : The specified row was out of the possible range of the component rows

        """
        comps = []
        if type(row) is range:
            for i, _ in enumerate(self.action_rows):
                if i > len(self.action_rows) - 1 or i < 0:
                    raise InvalidArgument(
                        "the specified range is invalid! It has to be between 0 and "
                        + str(len(self.action_rows) - 1)
                    )
                for comp in self.action_rows[i]:
                    if i in row:
                        comp.disabled = disable
                    comps.append(comp)
        else:
            for i, _ in enumerate(self.action_rows):
                if i > len(self.action_rows) - 1 or i < 0:
                    raise InvalidArgument(
                        "the specified row is invalid! It has to be between 0 and "
                        + str(len(self.action_rows) - 1)
                    )
                for comp in self.action_rows[i]:
                    if i == row:
                        comp.disabled = disable
                    comps.append(comp)
        await self.edit(components=comps)

    async def disable_components(self, disable=True):
        """Disables all component in the message

        Parameters
        ----------
            disable: :class:`bool`, optional
                Whether to disable (``True``) or enable (``False``) als components; default True

        """
        fixed = []
        for x in self.components:
            x.disabled = disable
            fixed.append(x)
        await self.edit(components=fixed)

    @property
    def action_rows(self):
        """The action rows in the message

        :type: List[:class:`~Button` | :class:`LinkButton` | :class:`SelectMenu`]
        """
        rows: typing.List[
            typing.List[typing.Union[Button, LinkButton, SelectMenu]]
        ] = []

        c_row = []
        i = 0
        for x in self.components:
            if getattr(x, "new_line", True) == True and i > 0:
                rows.append(ActionRow(c_row))
                c_row = []
            c_row.append(x)
            i += 1
        if len(c_row) > 0:
            rows.append(c_row)
        return rows

    @typing.overload
    async def wait_for(self, client, event_name="button") -> PressedButton:
        ...

    @typing.overload
    async def wait_for(self, client, event_name="select") -> SelectedMenu:
        ...

    @typing.overload
    async def wait_for(self, client, event_name, custom_id) -> PressedButton:
        ...

    @typing.overload
    async def wait_for(self, client, event_name, custom_id) -> SelectedMenu:
        ...

    @typing.overload
    async def wait_for(self, client, event_name, timeout) -> PressedButton:
        ...

    @typing.overload
    async def wait_for(self, client, event_name, timeout) -> SelectedMenu:
        ...

    async def wait_for(
        self,
        client,
        event_name: typing.Literal["select", "button"],
        custom_id=MISSING,
        timeout=MISSING,
    ) -> typing.Union[PressedButton, SelectedMenu]:
        """Waits for a message component to be invoked in this message

        Parameters
        -----------
        client: :class:`discord.ext.commands.Bot`
            The discord client
        event_name: :class:`str`
            The name of the event which will be awaited [``"select"`` | ``"button"``]

            .. note::

                The event_name must be ``select`` for a select menu selection and ``button`` for a button press

        custom_id: :class:`str`, Optional
            Filters the waiting for a custom_id

        timeout: :class:`float`, Optional
            After how many seconds the waiting should be canceled.
            Throws an :class:`asyncio.TimeoutError` Exception

        Raises
        ------
            :raises: :class:`InvalidArgument` : The event name passed was invalid

        Returns
        ----------
        :returns: The component that was waited for
        :type: :class:`~PressedButton` | :class:`~SelectedMenu`
        """
        if event_name.lower() in ["button", "select"]:

            def check(btn, msg):
                if msg.id == self.id:
                    if custom_id is not MISSING and btn.custom_id == custom_id:
                        return True
                    return True

            return (
                await client.wait_for(
                    "button_press" if event_name.lower() == "button" else "menu_select",
                    check=check,
                    timeout=timeout,
                )
            )[0]

        raise InvalidArgument(
            "Invalid event name, event must be 'button' or 'select', not "
            + str(event_name)
        )


class ResponseMessage(Interaction, Message):
    r"""A message Object which extends the `Message` Object optimized for an interaction component"""

    def __init__(self, *, state, application_id, channel, data, user):
        Interaction.__init__(self, application_id, state, data)
        Message.__init__(self, state=state, channel=channel, data=data["message"])

        self.interaction_component = None

        if int(data["data"]["component_type"]) == 2:
            for x in self.buttons:
                if hasattr(x, "custom_id") and x.custom_id == data["data"]["custom_id"]:
                    self.interaction_component = PressedButton(
                        data, self._application_id, user, x, self._state
                    )
        elif int(data["data"]["component_type"]) == 3:
            for x in self.select_menus:
                if x.custom_id == data["data"]["custom_id"]:
                    self.interaction_component = SelectedMenu(
                        data, self._application_id, user, x, self._state
                    )


class WebhookMessage(Message, discord.WebhookMessage):
    def __init__(self, *, state, channel, data):
        Message.__init__(self, state=state, channel=channel, data=data)
        discord.WebhookMessage.__init__(self, state=state, channel=channel, data=data)

    async def edit(self, **fields):
        """Edits the message

        content: :class:`str`, Optional
            The content to edit the message with or None to clear it.
        embed: :class:`discord.Embed`
            Embed rich content
        embeds: List[:class:`discord.Embed`], Optional
            A list of embeds to edit the message with.
        supress: :class:`bool`
            Whether to supress all embeds in the message
        allowed_mentions: :class`discord.AllowedMentions`
            Controls the mentions being processed in this message. See `discord.abc.Messageable.send` for more information.
        """
        return await self._state._webhook._adapter.edit_webhook_message(
            message_id=self.id, payload=jsonifyMessage(**fields)
        )


class EphemeralComponent(Interaction):
    """Represents a component in a hidden message

    .. note::

        You will only get this class for components if you set a component on a hidden response in an interaction and the component was used

    This class only has the custom_id of the used component, the component type and values
    """

    def __init__(self, application_id, state, user, data) -> None:
        Interaction.__init__(self, application_id, state, data, user)
        self.custom_id = data["data"]["custom_id"]
        self.component_type = data["data"]["component_type"]
        if self.component_type == 3:

            class EphemeralValue:
                def __init__(self, value) -> None:
                    self.name = None
                    self.value = value

            self.values = [EphemeralValue(x) for x in data["data"]["values"]]


class EphemeralMessage(Message):
    """Represents a hidden (ephemeral) message

    .. note::

        You will get this class for a message only if you sent a hidden response

    This class is almost the same as the :class:`~Message` class, but you can't edit, delete or reply to the message

    If you want to "reply" to id, use the `interaction.send` method instead
    """

    def __init__(self, *, state, channel, data):
        if data.get("attachments") is None:
            data["attachments"] = []
        if data.get("embeds") is None:
            data["embeds"] = []
        if data.get("edited_timestamp") is None:
            data["edited_timestamp"] = None
        if data.get("type") is None:
            data["type"] = 0
        if data.get("pinned") is None:
            data["pinned"] = False
        if data.get("mention_everyone") is None:
            data["mention_everyone"] = False
        if data.get("tts") is None:
            data["tts"] = False
        if data.get("content") is None:
            data["content"] = None
        Message.__init__(self, state=state, channel=channel, data=data)

    async def edit(self, **kwargs):
        raise Exception("Cannot edit ephemeral message")

    async def delete(self, *, delay):
        raise Exception("Cannot delete ephemeral message")

    async def respond(self, **kwargs):
        raise Exception(
            "Cannot reply to ephemeral message. Instead, use the '.send' function of the interaction"
        )
