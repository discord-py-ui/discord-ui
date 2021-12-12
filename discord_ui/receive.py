from __future__ import annotations


from .enums import InteractionResponseType
from .slash.http import ModifiedSlashState
from .errors import InvalidEvent, WrongType
from .http import BetterRoute, get_message_payload, send_files
from .slash.errors import AlreadyDeferred, EphemeralDeletion
from .tools import EMPTY_CHECK, MISSING, All, deprecated, setup_logger, get
from .slash.types import ContextCommand, SlashCommand, SlashPermission, SlashSubcommand
from .components import ActionRow, Button, ComponentStore, LinkButton, SelectMenu, SelectOption, UseableComponent, make_component

import discord
from discord import utils
from discord.ext import commands
from discord.state import ConnectionState

from typing import Any, List, Union, Dict
try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

logging = setup_logger("discord-ui")

__all__ = (
    'Message',
    'EphemeralMessage',
    'EphemeralResponseMessage',
    
    'ButtonInteraction',
    'PressedButton',    # deprecated

    'SelectInteraction',
    'SelectedMenu',     # deprecated

    'AutocompleteInteraction',
    'ChoiceGeneratorContext',   # deprecated

    'SlashInteraction',
    'SlashedCommand',           # deprecated

    'SubSlashInteraction',
    'SlashedSubCommand',        # deprecated

    'Interaction',
)

class InteractionType:
    PING                                =       Ping        =           1
    APPLICATION_COMMAND                 =      Command      =           2
    MESSAGE_COMPONENT                   =     Component     =           3
    APPLICATION_COMMAND_AUTOCOMPLETE    =    Autocomplete   =           4

class Interaction():
    def __init__(self, state, data, user=None, message=None) -> None:
        self._state: ModifiedSlashState = state

        self.deferred: bool = False
        self.responded: bool = False
        self._deferred_hidden: bool = False
        self._original_payload: dict = data

        self.author: Union[discord.Member, discord.User] = user
        """The user who created the interaction"""
        self.application_id: int = data["application_id"]
        """The ID of the bot application"""
        self.token: str = data["token"]
        """The token for responding to the interaction"""
        self.id: int = int(data["id"])
        """The id of the interaction"""
        self.type: int = data["type"]
        """The type of the interaction. See :class:`~InteractionType` for more information"""
        self.version: int = data["version"]
        self.data: dict = data["data"]
        """The passed data of the interaction"""
        self.channel_id: int = int(data.get("channel_id")) if data.get("channel_id") is not None else None
        """The channel-id where the interaction was created"""
        self.guild_id: int = int(data["guild_id"]) if data.get("guild_id") is not None else None
        """The guild-id where the interaction was created"""
        self.message: Message = message
        """The message in which the interaction was created"""

    @property
    def created_at(self):
        """The interaction's creation time in UTC"""
        return utils.snowflake_time(self.id)
    
    @property
    def guild(self) -> discord.Guild:
        """The guild where the interaction was created"""
        return self._state._get_guild(self.guild_id)
    @property
    def channel(self) -> Union[discord.abc.GuildChannel, discord.abc.PrivateChannel]:
        """The channel where the interaction was created"""
        return self._state.get_channel(self.channel_id) or self._state.get_channel(self.author.id)

    async def defer(self, hidden=False):
        """
        This will acknowledge the interaction. This will show the (*Bot* is thinking...) Dialog

        .. note::
            
            This function should be used if the bot needs more than 15 seconds to respond
        
        Parameters
        ----------
        hidden: :class:`bool`, optional
            Whether the loading thing should be only visible to the user; default False.
        
        """
        if self.deferred:
            logging.error(AlreadyDeferred())
            return

        payload = None
        if hidden is True:
            payload = {"flags": 64}
            self._deferred_hidden = True
        
        await self._state.slash_http.respond_to(self.id, self.token, InteractionResponseType.Deferred_channel_message, payload)
        self.deferred = True

    async def respond(self, content=None, *, tts=False, embed=None, embeds=None, file=None, files=None, nonce=None,
    allowed_mentions=None, mention_author=None, components=None, delete_after=None, listener=None, 
    hidden=False, ninja_mode=False) -> Union['Message', 'EphemeralMessage']:
        """
        Responds to the interaction
        
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
        listener: :class:`Listener`
            A component-listener for this message
        hidden: :class:`bool`
            Whether the response should be visible only to the user 
        ninja_mode: :class:`bool`
            If true, the client will respond to the button interaction with almost nothing and returns nothing
        
        Returns
        -------
        :class:`~Message` | :class:`~EphemeralMessage`
            Returns the sent message
        """
        if ninja_mode is True or all(y in [None, False] for x, y in locals().items() if x not in ["self"]):
            try:
                await self._state.slash_http.respond_to(self.id, self.token, InteractionResponseType.Deferred_message_update)
                self.responded = True
                return
            except discord.errors.HTTPException as x:
                if "value must be one of (4, 5)" in str(x).lower():
                    logging.error(str(x) + "\n" + "The 'ninja_mode' parameter is not supported for slash commands!")
                    ninja_mode = False
                else:
                    raise x

        if self.responded is True:
            return await self.send(content=content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, 
                components=components, listener=listener, hidden=hidden
            )

        if components is None and listener is not None:
            components = listener.to_components()        
        payload = get_message_payload(content=content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, 
            mention_author=mention_author, components=components
        )
        
        if self._deferred_hidden is hidden:
            if self._deferred_hidden is False and hidden is True:
                logging.warning("Your response should be hidden, but the interaction was deferred public. This results in a public response.")
            if self._deferred_hidden is True and hidden is False:
                logging.warning("Your response should be public, but the interaction was deferred hidden. This results in a hidden response.")
        hide_message = self._deferred_hidden or not self.deferred and hidden is True


        r = None
        if delete_after is not None and hide_message is True:
            raise EphemeralDeletion()

        if hide_message:
            payload["flags"] = 64
        
        if self.deferred:
            route = BetterRoute("PATCH", f'/webhooks/{self.application_id}/{self.token}/messages/@original')
            if file is not None or files is not None:
                await send_files(route=route, files=files or ([file] if file is not None else None), payload=payload, http=self._state.http)
            else:
                await self._state.http.request(route, json=payload)    
        else:
            await self._state.slash_http.respond_to(self.id, self.token, InteractionResponseType.Channel_message, payload, files=files or [file] if file is not None else None)
        self.responded = True
        
        r = await self._state.http.request(BetterRoute("GET", f"/webhooks/{self.application_id}/{self.token}/messages/@original"))
        if hide_message is True:
            msg = EphemeralMessage(state=self._state, channel=self.channel, data=r, application_id=self.application_id, token=self.token)
        else:
            msg = await getMessage(self._state, data=r, response=False)
        if listener is not None:
            listener._start(msg)
        if delete_after is not None:
            await msg.delete(delete_after)
        return msg
    async def send(self, content=None, *, tts=None, embed=None, embeds=None, file=None, files=None, nonce=None,
        allowed_mentions=None, mention_author=None, components=None, delete_after=None, listener=None, hidden=False,
        force=False
    ) -> Union[Message, EphemeralMessage]:
        """
        Sends a message to the interaction using a webhook
        
        Parameters
        ----------
        content: :class:`str`, optional
            The raw message content
        tts: :class:`bool`, optional
            Whether the message should be send with text-to-speech
        embed: :class:`discord.Embed`, optional
            Embed rich content
        embeds: List[:class:`discord.Embed`], optional
            A list of embeds for the message
        file: :class:`discord.File`, optional
            The file which will be attached to the message
        files: List[:class:`discord.File`], optional
            A list of files which will be attached to the message
        nonce: :class:`int`, optional
            The nonce to use for sending this message
        allowed_mentions: :class:`discord.AllowedMentions`, optional
            Controls the mentions being processed in this message
        mention_author: :class:`bool`, optional
            Whether the author should be mentioned
        components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`]
            A list of message components to be included
        delete_after: :class:`float`, optional
            After how many seconds the message should be deleted, only works for non-hiddend messages; default MISSING
        listener: :class:`Listener`, optional
            A component-listener for this message
        hidden: :class:`bool`, optional
            Whether the response should be visible only to the user 
        ninja_mode: :class:`bool`, optional
            If true, the client will respond to the button interaction with almost nothing and returns nothing
        force: :class:`bool`, optional
            Whether sending the follow-up message should be forced.
            If ``False``, then a follow-up message will only be send if ``.responded`` is True; default False
        
        Returns
        -------
        :class:`~Message` | :class:`EphemeralMessage`
            Returns the sent message
        """
        if force is False and self.responded is False:
            return await self.respond(content=content, tts=tts, embed=embed, embeds=embeds, file=file, files=files, nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, components=components, delete_after=delete_after, listener=listener, hidden=hidden)

        if components is None and listener is not None:
            components = listener.to_components()
        payload = get_message_payload(content=content, tts=tts, embed=embed, embeds=embeds, nonce=nonce, allowed_mentions=allowed_mentions, mention_author=mention_author, components=components)
        
        if hidden:
            payload["flags"] = 64

        route = BetterRoute("POST", f'/webhooks/{self.application_id}/{self.token}')
        if file is not None or files is not None:
            r = await send_files(route=route, files=files or ([file] if file is None else None), payload=payload, http=self._state.http)
        else:
            r = await self._state.http.request(route, json=payload)

        if hidden is True:
            msg = EphemeralMessage(state=self._state, channel=self._state.get_channel(int(r["channel_id"])), data=r, application_id=self.application_id, token=self.token)
        else:
            msg = await getMessage(self._state, r, response=False)
        if delete_after is not None:
            await msg.delete(delete_after)
        if listener is not None:
            listener._start(msg)
        return msg
    def _handle_auto_defer(self, auto_defer):
        self.deferred = auto_defer[0]
        self._deferred_hidden = auto_defer[1]

class AutocompleteInteraction(Interaction):
    """Autocomplete interaction"""
    def __init__(self, command, state, data, options, user=None) -> None:
        Interaction.__init__(self, state, data, user=user)
        self.focused_option: dict = options[get(options, check=lambda x: options[x].get("focused", False))]
        """The option for which the choices should be generated"""
        self.value_query: Union[str, int] = self.focused_option["value"]
        """The current input of the focused option"""
        self.selected_options: Dict[str, Any] = {options[x]["name"]: options[x]["value"] for x in options}
        """All the options that were already selected. Format: ``{"option name": value}``"""
        self.command: Union[SlashInteraction, SlashInteraction, ContextInteraction] = command
        """The slash command for which the choices should be generated"""

    async def defer(self, *args, **kwargs):
        """Cannot defer this type of interaction"""
        raise NotImplementedError()
    async def respond(self, *args, **kwargs):
        """Response will be made automatically with the choices that are returned"""
        raise NotImplementedError()
    async def send(self, *args, **kwargs):
        """Cannot send followup message to this type of interaction"""
        raise NotImplementedError()
class ChoiceGeneratorContext(AutocompleteInteraction):
    """Deprecated, please use :class:`AutocompleteInteraction` instead"""
    ...

class ComponentInteraction(Interaction):
    """A received component"""
    def __init__(self, state, data, user, message) -> None:
        Interaction.__init__(self, state, data, user=user, message=message)
        self.component: UseableComponent = UseableComponent(data["data"]["component_type"])
        self.component._custom_id = data["data"]["custom_id"]
class ComponentContext(ComponentInteraction):
    """Deprecated, please use :class:`ComponentInteraction` instead"""
    ...

class SelectInteraction(Interaction):
    """An interaction that was created by a :class:`~SelectMenu`"""
    def __init__(self, data, user, s, msg, client) -> None:
        Interaction.__init__(self, client._connection, data, user, msg)
        
        self.component: SelectMenu = s
        self.bot: commands.Bot = client
        self.selected_options: List[SelectOption] = []
        """The list of the selected options"""
        self.selected_values: List[str] = []
        """The list of raw values which were selected"""
        for val in data["data"]["values"]:
            for x in self.component.options:
                if x.value == val:
                    self.selected_options.append(x)
                    self.selected_values.append(x.value)
        self.author: discord.Member = user
        """The user who selected the value"""
class SelectedMenu(SelectInteraction):
    """deprecated, please use :class:`SelectInteraction` instead"""
    ...

class ButtonInteraction(Interaction):
    """An interaction that was created by a :class:`~Button`"""
    def __init__(self, data, user, b, message, client) -> None:
        Interaction.__init__(self, client._connection, data, user, message)
        self.custom_id: str = data['data']['custom_id']
        self.component: Button = b
        """The component that created the interaction"""
        self.bot: commands.Bot = client
        self.author: discord.Member = user
        """The user who pressed the button"""
class PressedButton(ButtonInteraction):
    """deprecated, please use :class:`ButtonInteraction` instead"""
    ...

class SlashInteraction(Interaction):
    """An interaction created by a :class:`~SlashCommand`"""
    def __init__(self, client, command: SlashCommand, data, user, args = None) -> None:
        Interaction.__init__(self, client._connection, data, user)
        self.custom_id: str = data['data']['custom_id']
        self.command: SlashCommand = command
        """The original command instance that was used. If you change things here, the changes will be applied globally"""
        self.bot: commands.Bot = client
        self.author: discord.Member = user
        """The user who used the command"""
        self.args: Dict[str, Union[str, int, bool, discord.Member, discord.TextChannel, discord.Role, float]] = args
        """The options that were received"""
        self.permissions: SlashPermission = command.guild_permissions.get(self.guild_id) if command.guild_permissions is not None else None
        """The permissions for this guild"""
class SlashedCommand(SlashInteraction):
    """deprecated, please use :class:`SlashInteraction` instead"""
    ...

class SubSlashInteraction(SlashInteraction):
    """An interaction created by a :class:`~SlashSubcommand`"""

    command: SlashSubcommand
    def __init__(self, client, command, data, user, args = None) -> None:
        SlashInteraction.__init__(self, client, command, data, user, args)
class SlashedSubCommand(SubSlashInteraction):
    """deprecated, please use ``SubSlashInteraction`` instead"""
    ...

class ContextInteraction(Interaction):
    """An interaction created by a :class:`~MessageCommand` or a :class:`~UserCommand`"""
    def __init__(self, client, command: ContextCommand, data, user, target) -> None:
        Interaction.__init__(self, client._connection, data, user)
        self.command: ContextCommand = command
        """The original command instance that was used"""
        self.bot: commands.Bot = client
        self.target: Union[Message, Union[discord.Member, discord.User]] = target
        """The target object on which the interaction was used"""
        self.permissions: SlashPermission = command.guild_permissions.get(self.guild_id) if command.guild_permissions is not None else None 
        """The permissions for this guild"""
        

async def getMessage(state: discord.state.ConnectionState, data, response=True):
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
    channel: :class:`discord.Messageable`
        An alternative channel that will be used when no channel was found

    Returns
    -------
    :class:`~Message` | :class:`~EphemeralMessage`
        The sent message
    """
    msg_base = data.get("message", data)

    channel = state.get_channel(int(data["channel_id"])) or state.get_channel(int(msg_base["author"]["id"]))
    if response:
        if msg_base["flags"] == 64:
            return EphemeralResponseMessage(state=state, channel=channel, data=data.get("message", data))
        return Message(state=state, channel=channel, data=msg_base)

    if msg_base["flags"] == 64:
        return EphemeralMessage(state=state, channel=channel, data=msg_base)
    return Message(state=state, channel=channel, data=msg_base)

class Message(discord.Message):
    """A :class:`discord.Message` optimized for components"""

    _state: ConnectionState
    def __init__(self, *, state, channel, data):
        self.__slots__ = discord.Message.__slots__ + ("components",)
        discord.Message.__init__(self, state=state, channel=channel, data=data)
        self.components = ComponentStore()
        """The components in the message"""

        self._update_components(data)

    # region attributes
    @property
    @deprecated(".components.buttons")
    def buttons(self) -> List[Union[Button, LinkButton]]:
        """The button components in the message"""
        return self.components.buttons
    @property
    @deprecated(".components.selects")
    def select_menus(self) -> List[SelectMenu]:
        """The select menus components in the message"""
        return self.components.selects
    @property
    @deprecated(".components.get_rows()")
    def action_rows(self) -> List[ActionRow]:
        return self.components.get_rows()

    def _update_components(self, data):
        """Updates the message components"""
        if data.get("components") is None:
            self.components = ComponentStore()
            return
        self.components = ComponentStore()
        if len(data["components"]) == 0:
            pass
        elif len(data["components"]) > 1:
            # multiple lines
            for componentWrapper in data["components"]:
                # newline
                for index, com in enumerate(componentWrapper["components"]):
                    self.components.append(make_component(com, index==0))
        elif len(data["components"][0]["components"]) > 1:
            # All inline
            for index, com in enumerate(data["components"][0]["components"]):
                self.components.append(make_component(com, index==0))
        else:
            # One button
            component = data["components"][0]["components"][0]
            self.components.append(make_component(component))
    def _update(self, data):
        super()._update(data)
        self._update_components(data)

    async def edit(self, content=MISSING, *, embed=MISSING, embeds=MISSING, attachments=MISSING, suppress=MISSING, 
        delete_after=MISSING, allowed_mentions=MISSING, components=MISSING):
        """Edits the message and updates its properties

        .. note::

            If a paremeter is `None`, the attribute will be removed from the message

        Parameters
        ----------------
        content: :class:`str`
            The new message content
        embed: :class:`discord.Embed`
            The new embed of the message
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
        payload = get_message_payload(content, embed=embed, embeds=embeds, allowed_mentions=allowed_mentions, attachments=attachments, suppress=suppress, flags=self.flags.value, components=components)
        data = await self._state.http.edit_message(self.channel.id, self.id, **payload)
        self._update(data)

        if delete_after is not MISSING:
            await self.delete(delay=delete_after)

    async def disable_components(self, index=All, disable=True, **fields):
        """Disables component(s) in the message
        
        Parameters
        ----------
        index: :class:`int` | :class:`str` | :class:`range` | List[:class:`int` | :class:`str`], optional
            Index(es) or custom_id(s) for the components that should be disabled or enabled; default all components
        disable: :class:`bool`, optional
            Whether to disable (``True``) or enable (``False``) components; default True
        ``**fields``
            Other parameters for editing the message (like `content=`, `embed=`)
        """
        self.components.disable(index, disable)
        await self.edit(components=self.components, **fields)

    async def wait_for(self, event_name: Literal["select", "button", "component"], client, custom_id=None, by=None, check=EMPTY_CHECK, timeout=None) -> Union[ButtonInteraction, SelectInteraction, ComponentContext]:
        """Waits for a message component to be invoked in this message

        Parameters
        -----------
        event_name: :class:`str`
            The name of the event which will be awaited [``"select"`` | ``"button"`` | ``"component"``]
            
            .. note::

                ``event_name`` must be ``select`` for a select menu selection, ``button`` for a button press and ``component`` for any component

        client: :class:`discord.ext.commands.Bot`
            The discord client
        custom_id: :class:`str`, Optional
            Filters the waiting for a custom_id
        by: :class:`discord.User` | :class:`discord.Member` | :class:`int` | :class:`str`, Optional
            The user or the user id by that has to create the component interaction
        check: :class:`function`, Optional
            A check that has to return True in order to break from the event and return the received component
                The function takes the received component as the parameter
        timeout: :class:`float`, Optional
            After how many seconds the waiting should be canceled. 
            Throws an :class:`asyncio.TimeoutError` Exception

        Raises
        ------
        :class:`discord_ui.errors.InvalidEvent`
            The event name passed was invalid 

        Returns
        --------
        :class:`~ButtonInteraction` | :class:`~SelectInteraction`
            The component that was waited for

        Example
        -------

        .. code-block::

            # send a message with comoponents
            msg = await ctx.send("okay", components=[Button(custom_id="a_custom_id", ...)])
            try:
                # wait for the button
                btn = await msg.wait_for("button", client, "a_custom_id", by=ctx.author, timeout=20)
                # send response
                btn.respond()
            except asyncio.TimeoutError:
                # no button press was received in 20 seconds timespan
        """
        def _check(com):
            if com.message.id == self.id:
                statements = []
                if custom_id is not None:
                    statements.append(com.custom_id == custom_id)
                if by is not None:
                    statements.append(com.author.id == (by.id if hasattr(by, "id") else int(by)))
                if check is not None:
                    statements.append(check(com))
                return all(statements)
            return False
        if not isinstance(client, commands.Bot):
            raise WrongType("client", client, "discord.ext.commands.Bot")
        
        if event_name.lower() == "button":
            return await client.wait_for('button', check=_check, timeout=timeout)
        if event_name.lower() == "select":
            return await client.wait_for("select", check=_check, timeout=timeout)
        if event_name.lower() == "component":
            return await client.wait_for("component", check=_check, timeout=timeout)
        
        raise InvalidEvent(event_name, ["button", "select", "component"])

    async def put_listener(self, listener):
        """Adds a listener to this message and edits the message if the components of the listener are missing in this message
        
        Parameters
        ----------
        listener: :class:`Listener`
            The listener which should be put to the message
        
        """
        if len(self.components) == 0:
            await self.edit(components=listener.to_components())
        self.attach_listener(listener)       
    def attach_listener(self, listener):
        """Attaches a listener to this message after it was sent
        
        Parameters
        ----------
        listener: :class:`Listener`
            The listener that should be attached
        
        """
        listener._start(self)
    def remove_listener(self):
        """Removes the listener from this message"""
        try:
            del self._state._component_listeners[str(self.id)]
        except KeyError:
            pass

class EphemeralMessage(Message):
    """Represents a hidden (ephemeral) message"""
    def __init__(self, state, channel, data, application_id=None, token=None):
        #region fix reference keyerror
        if data.get("message_reference"):
            if data["message_reference"].get("channel_id") is None:
                data["message_reference"]["channel_id"] = str(channel.id)
        #endregion
        Message.__init__(self, state=state, channel=channel, data=data)
        self._application_id = application_id
        self._interaction_token = token
    async def edit(self, *args, **fields):
        r = BetterRoute("PATCH", f"/webhooks/{self._application_id}/{self._interaction_token}/messages/{self.id}")
        self._update(await self._state.http.request(r, json=get_message_payload(*args, **fields)))        
    async def delete(self):
        """Override for delete function that will throw an exception"""
        raise EphemeralDeletion()

class EphemeralResponseMessage(Message):
    """A ephemeral message which was created from an interaction
    
    .. important::

        Methods like `.edit()`, which change the original message, need a `token` paremeter passed in order to work
    """
    def __init__(self, *, state, channel, data):
        Message.__init__(self, state=state, channel=channel, data=data)

    async def edit(self, token, *args, **fields):
        """Edits the message
        
        Parameters
        ----------
        token: :class:`str`
            The token of the interaction with wich this ephemeral message was sent
        fields: :class:`kwargs`
            The fields to edit (ex. `content="...", embed=..., attachments=[...]`)

        Example

        .. code-block::

            async def testing(ctx):
                msg = await ctx.send("hello hidden world", components=[Button("test")])
                btn = await msg.wait_for("button", client)
                await btn.message.edit(ctx.token, content="edited", components=None)
    
        """
        route = BetterRoute("PATCH", f"/webhooks/{self.interaction.application_id}/{token}/messages/{self.id}")
        self._update(await self._state.http.request(route, json=get_message_payload(*args, **fields)))
    async def delete(self):
        """Override for delete function that will throw an exception"""
        raise EphemeralDeletion()
    async def disable_components(self, token, disable = True, **fields):
        """Disables all component in the message
        
        Parameters
        ----------
        disable: :class:`bool`, optional
            Whether to disable (``True``) or enable (``False``) all components; default True
        
        """
        self.components.disable(disable=disable)
        await self.edit(token, components=self.components, **fields)