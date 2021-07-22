from .client import Components, Slash
import discord
from discord import TextChannel
from discord.ext import commands

from .receive import Message
from .http import jsonifyMessage, BetterRoute, send_files

import sys

module = sys.modules["discord"]


async def send(
    self: TextChannel,
    content=None,
    *,
    tts=False,
    embed=None,
    embeds=None,
    file=None,
    files=None,
    delete_after=None,
    nonce=None,
    allowed_mentions=None,
    reference=None,
    mention_author=None,
    components=None,
) -> Message:
    """Sends a message to a textchannel

    Parameters
    ----------
    content: :class:`str`, optional
        The message text content; default None
    tts: :class:`bool`, optional
        True if this is a text-to-speech message; default False
    embed: :class:`discord.Embed`, optional
        Embedded rich content; default None
    embeds: List[:class:`discord.Embed`], optional
        embedded rich content (up to 6000 characters); default None
    file: :class:`discord.File`, optional
        A file sent as an attachment to the message; default None
    files: List[:class:`discord.File`], optional
        A list of file attachments; default None
    delete_after: :class:`float`, optional
        After how many seconds the message should be deleted; default None
    nonce: :class:`int`, optional
        The nonce to use for sending this message. If the message was successfully sent, then the message will have a nonce with this value; default None
    allowed_mentions: :class:`discord.AllowedMentions`, optional
        A list of mentions proceeded in the message; default None
    reference: :class:`discord.MessageReference` | :class:`discord.Message`, optional
        A message to refer to (reply); default None
    mention_author: :class:`bool`, optional
        True if the author should be mentioned; default None
    components: List[:class:`~Button` | :class:`~LinkButton` | :class:`~SelectMenu`], optional
        A list of message components included in this message; default None

    Returns
    -------
    :return: Returns the sent message
    :type: :class:`~Message`

    Raises
    ------
    :raises: :class:`discord.InvalidArgument`: A passed argument was invalid
    """
    payload = jsonifyMessage(
        content=content,
        tts=tts,
        embed=embed,
        embeds=embeds,
        nonce=nonce,
        allowed_mentions=allowed_mentions,
        reference=reference,
        mention_author=mention_author,
        components=components,
    )

    route = BetterRoute("POST", f"/channels/{self.id}/messages")

    r = None
    if file is None and files is None:
        r = await self._state.http.request(route, json=payload)
    else:
        r = await send_files(
            route, files=files or [file], payload=payload, http=self._state.http
        )

    msg = Message(state=self._state, channel=self, data=r)
    if delete_after is not None:
        await msg.delete(delay=delete_after)

    return msg


def message_overrride(cls, *args, **kwargs):
    if cls is discord.message.Message:
        return object.__new__(Message)
    else:
        return object.__new__(cls)


module.abc.Messageable.send = send
module.message.Message.__new__ = message_overrride


class Overriden_Bot(commands.bot.Bot):
    """
    Represents an overriden discord bot.

    This only adds two attributes, `.slash` and `.components`

    This class is a subclass of :class:`discord.Client` and as a result
    anything that you can do with a :class:`discord.Client` you can do with
    this bot.

    This class also subclasses :class:`.GroupMixin` to provide the functionality
    to manage commands.

    Attributes
    -----------
    command_prefix
        The command prefix is what the message content must contain initially
        to have a command invoked. This prefix could either be a string to
        indicate what the prefix should be, or a callable that takes in the bot
        as its first parameter and :class:`discord.Message` as its second
        parameter and returns the prefix. This is to facilitate "dynamic"
        command prefixes. This callable can be either a regular function or
        a coroutine.

        An empty string as the prefix always matches, enabling prefix-less
        command invocation. While this may be useful in DMs it should be avoided
        in servers, as it's likely to cause performance issues and unintended
        command invocations.

        The command prefix could also be an iterable of strings indicating that
        multiple checks for the prefix should be used and the first one to
        match will be the invocation prefix. You can get this prefix via
        :attr:`.Context.prefix`. To avoid confusion empty iterables are not
        allowed.

        .. note::

            When passing multiple prefixes be careful to not pass a prefix
            that matches a longer prefix occurring later in the sequence.  For
            example, if the command prefix is ``('!', '!?')``  the ``'!?'``
            prefix will never be matched to any message as the previous one
            matches messages starting with ``!?``. This is especially important
            when passing an empty string, it should always be last as no prefix
            after it will be matched.
    case_insensitive: :class:`bool`
        Whether the commands should be case insensitive. Defaults to ``False``. This
        attribute does not carry over to groups. You must set it to every group if
        you require group commands to be case insensitive as well.
    description: :class:`str`
        The content prefixed into the default help message.
    help_command: Optional[:class:`.HelpCommand`]
        The help command implementation to use. This can be dynamically
        set at runtime. To remove the help command pass ``None``. For more
        information on implementing a help command, see :ref:`ext_commands_help_command`.
    owner_id: Optional[:class:`int`]
        The user ID that owns the bot. If this is not set and is then queried via
        :meth:`.is_owner` then it is fetched automatically using
        :meth:`~.Bot.application_info`.
    owner_ids: Optional[Collection[:class:`int`]]
        The user IDs that owns the bot. This is similar to :attr:`owner_id`.
        If this is not set and the application is team based, then it is
        fetched automatically using :meth:`~.Bot.application_info`.
        For performance reasons it is recommended to use a :class:`set`
        for the collection. You cannot set both ``owner_id`` and ``owner_ids``.

        .. versionadded:: 1.3
    strip_after_prefix: :class:`bool`
        Whether to strip whitespace characters after encountering the command
        prefix. This allows for ``!   hello`` and ``!hello`` to both work if
        the ``command_prefix`` is set to ``!``. Defaults to ``False``.

        .. versionadded:: 1.7
    """

    def __init__(
        self,
        command_prefix,
        help_command=None,
        description=None,
        slash_settings=None,
        **options,
    ):
        commands.bot.Bot.__init__(
            self,
            command_prefix,
            help_command=help_command,
            description=description,
            **options,
        )

        self.slash = Slash(self, slash_settings)
        self.components = Components(self)


def client_override(cls, *args, **kwargs):
    if cls is commands.bot.Bot:
        return object.__new__(Overriden_Bot)
    else:
        return object.__new__(cls)


def override_client():
    """Overrides the default :class:`discord.ext.commands.Bot` client with a custom one,
    which automatically initalizes the :class:`~Slash` and :class:`~Component` classes and adds them
    to the client's attributes

    Without overriding

    ```py
        from discord.ext import commands
        from discord_message_components import Extension

        client = commands.Bot(...)
        extension = Extension(client)
    ```

    With overridding

    ```py

        from discord.ext import commands
        from discord_message_components import override_client

        override_client()
        client = commands.Bot(...)
    ```

    ``client.slash`` and ``client.components`` are now accesable, if you want intellisense to work, change it to

    ```py

        from discord.ext import commands
        from discord_message_components import override_client, OverridenClient

        override_client()
        client: OverridenClient = commands.Bot(...)
    ```

    Or you could use

    ```py

        from discord_message_components import OverridenClient
        client = OverridenClient(...)
    ```

    it would still result in the same
    """
    module.ext.commands.bot.Bot.__new__ = client_override


sys.modules["discord"] = module
