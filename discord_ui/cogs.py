from .components import ComponentType
from .tools import MISSING
from .slash.types import MessageCommand, SlashCommand, SlashSubcommand, UserCommand

import discord
from discord.errors import InvalidArgument
from discord.ext.commands import errors
from discord.ext.commands.cooldowns import BucketType, CooldownMapping

import asyncio
import datetime
import inspect
from typing import Literal, Optional, Union

class WrongListener(errors.CheckFailure):
    """Exception raised when a listening component received a component event that doesn't meet the check conditions

    This inherits from :exc:`CheckFailure`
    """
    def __init__(self, message: Optional[str] = None) -> None:
        super().__init__(message or "The used component doesn't this listener's check conditions.")

class BaseCallable():
    """A base class for all cog objects
    
    IMPORTANT: Most of this code is taken out of the discord.ext.commands module
        Ref: https://github.com/Rapptz/discord.py/blob/a2a7b0f076c763f08c871d76f9477d1d0eed1973/discord/ext/commands/core.py#L205
    """
    def __init__(self, callback) -> None:
        self.callback = callback
        self._before_invoke = None
        self._after_invoke = None
        
        # Checks for the dpy decorator
        self.__commands_checks__ = []
        if hasattr(self.callback, "__commands_checks__"):
            self.__commands_checks__ = self.callback.__commands_checks__

        cooldown = None
        if hasattr(self.callback, "__commands_cooldown__"):
            cooldown = self.callback.__commands_cooldown__
        try:
            self._buckets = CooldownMapping(cooldown)
        except TypeError:
            self._buckets = CooldownMapping(cooldown, BucketType.default)

        self._max_concurrency = None
        if hasattr(self.callback, "__commands_max_concurrency__"):
            self._max_concurrency = self.callback.__commands_max_concurrency__

        self._before_invoke = None
        try:
            before_invoke = self.callback.__before_invoke__
        except AttributeError:
            pass
        else:
            self.before_invoke(before_invoke)

        self._after_invoke = None
        try:
            after_invoke = self.callback.__after_invoke__
        except AttributeError:
            pass
        else:
            self.after_invoke(after_invoke)

        self.on_error = None
        
    async def __call__(self, *args, **kwds):
        return self.callback(*args, **kwds)
    async def invoke(self, ctx, *args, **kwargs):
        if self._before_invoke is not None:
            await self._before_invoke(ctx)
        if not await self.can_run(ctx):
            raise errors.CheckFailure()

        if self._max_concurrency is not None:
            await self._max_concurrency.acquire(ctx)
        try:
            # cooldown checks
            self._prepare_cooldowns(ctx)
        except Exception:
            if self._max_concurrency is not None:
                await self._max_concurrency.release(ctx)
            raise
        try:
            if hasattr(self, "cog"):
                await self.callback(self.cog, ctx, *args, **kwargs)
            else:
                await self.callback(ctx, *args, **kwargs)
        except Exception as ex:
            if not self.on_error:
                raise ex
            else:
                self.on_error(getattr(self, "cog", None), ctx, ex)
        if self._after_invoke is not None:
            await self._after_invoke(ctx)

    async def can_run(self, ctx):
        """Whether the command can be run"""
        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True
        return await discord.utils.async_all(predicate(ctx) for predicate in predicates)  # type: ignore
    @property
    def checks(self):
        return self.__commands_checks__
    def add_check(self, check):
        self.__commands_checks__.append(check)
    def remove_check(self, check):
        self.__commands_checks__.remove(check)
    def _prepare_cooldowns(self, ctx) -> None:
        if self._buckets.valid:
            dt = ctx.message.edited_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            bucket = self._buckets.get_bucket(ctx.message, current)
            if bucket is not None:
                retry_after = bucket.update_rate_limit(current)
                if retry_after:
                    raise CommandOnCooldown(bucket, retry_after, self._buckets.type)  # type: ignore

    def is_on_cooldown(self, ctx) -> bool:
        """Checks whether the command is currently on cooldown.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to use when checking the commands cooldown status.

        Returns
        --------
        :class:`bool`
            A boolean indicating if the command is on cooldown.
        """
        if not self._buckets.valid:
            return False

        bucket = self._buckets.get_bucket(ctx.message)
        dt = ctx.message.edited_at or ctx.message.created_at
        current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
        return bucket.get_tokens(current) == 0
    def reset_cooldown(self, ctx) -> None:
        """Resets the cooldown on this command.

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to reset the cooldown under.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx.message)
            bucket.reset()
    def get_cooldown_retry_after(self, ctx) -> float:
        """Retrieves the amount of seconds before this command can be tried again.

        .. versionadded:: 1.4

        Parameters
        -----------
        ctx: :class:`.Context`
            The invocation context to retrieve the cooldown from.

        Returns
        --------
        :class:`float`
            The amount of time left on this command's cooldown in seconds.
            If this is ``0.0`` then the command isn't on cooldown.
        """
        if self._buckets.valid:
            bucket = self._buckets.get_bucket(ctx.message)
            dt = ctx.message.edited_at or ctx.message.created_at
            current = dt.replace(tzinfo=datetime.timezone.utc).timestamp()
            return bucket.get_retry_after(current)

        return 0.0
    def error(self, coro):
        """A decorator that registers a coroutine as a local error handler.

        A local error handler is an :func:`.on_command_error` event limited to
        a single command. However, the :func:`.on_command_error` is still
        invoked afterwards as the catch-all.

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the local error handler.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The error handler must be a coroutine.')

        self.on_error = coro
        return coro
    def has_error_handler(self) -> bool:
        """:class:`bool`: Checks whether the command has an error handler registered.

        .. versionadded:: 1.7
        """
        return hasattr(self, 'on_error')
    def before_invoke(self, coro):
        """A decorator that registers a coroutine as a pre-invoke function.

        This function is called directly before the command is
        called. This makes it a useful function to set up database
        connections or any type of set up required.

        This post-invoke function takes a sole parameter, one of :class:`~SlashedCommand` | :class:`~SlashedSubCommand` | 
        :class:`~SlashedContext` | :class:`~PressedButton` | :class:`SelectedMenu`, depending on what this is used for

        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the pre-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The pre-invoke hook must be a coroutine.')

        self._before_invoke = coro
        return coro
    def after_invoke(self, coro):
        """A decorator that registers a coroutine as a post-invoke function.

        A post-invoke function is called directly after the command is
        called. This makes it a useful function to clean-up database
        connections or any type of clean up required.

        This post-invoke function takes a sole parameter, one of :class:`~SlashedCommand` | :class:`~SlashedSubCommand` | 
        :class:`~SlashedContext` | :class:`~PressedButton` | :class:`SelectedMenu`, depending on what this is used for


        Parameters
        -----------
        coro: :ref:`coroutine <coroutine>`
            The coroutine to register as the post-invoke hook.

        Raises
        -------
        TypeError
            The coroutine passed is not actually a coroutine.
        """
        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('The post-invoke hook must be a coroutine.')

        self._after_invoke = coro
        return coro
class BaseSlash(BaseCallable):
    def __init__(self, callback) -> None:
        self.__type__ = 1
        BaseCallable.__init__(self, callback)

class CogCommand(BaseSlash, SlashCommand):
    def __init__(self, *args, **kwargs) -> None:
        SlashCommand.__init__(self, *args, **kwargs)
        BaseSlash.__init__(self, args[0])
class CogSubCommandGroup(BaseSlash, SlashSubcommand):
    def __init__(self, *args, **kwargs) -> None:
        SlashSubcommand.__init__(self, *args, **kwargs)
        BaseSlash.__init__(self, args[0])
class CogMessageCommand(BaseSlash, MessageCommand):
    def __init__(self, *args, **kwargs) -> None:
        MessageCommand.__init__(self, *args, **kwargs)
        BaseSlash.__init__(self, args[0])
class CogUserCommand(BaseSlash, UserCommand):
    def __init__(self, *args, **kwargs) -> None:
        UserCommand.__init__(self, *args, **kwargs)
        BaseSlash.__init__(self, args[0])


class ListeningComponent(BaseCallable):
    def __init__(self, callback, messages, users, component_type, check, custom_id) -> None:
        BaseCallable.__init__(self, callback)
        self.__type__ = 2
        def predicate(ctx):
            checks = []
            if messages not in [MISSING, []]:
                checks.append(ctx.message.id in [(x.id if hasattr(x, "id") else int(x)) for x in messages])
            if users is not MISSING:
                checks.append(ctx.author.id in [(x.id if hasattr(x, "id") else int(x)) for x in users])
            if component_type is not MISSING:
                checks.append(ctx.component_type == (ComponentType.BUTTON if component_type in [ComponentType.BUTTON, "button"] else ComponentType.SELECT_MENU))
            if check is not MISSING:
                checks.append(check(ctx) is True)
                if not all(checks):
                    raise WrongListener()
            return True
        self.add_check(predicate)
        self.custom_id = custom_id

def slash_cog(name=MISSING, description=MISSING, options=[], guild_ids=MISSING, default_permission=MISSING, guild_permissions=MISSING):
    """A decorator for cogs that will register a slashcommand
    
    command in discord
        ``/name [options]``
    
    Parameters
    ----------
        name: :class:`str`, optional
            1-32 characters long name; default MISSING

            .. note::

                The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
        
        description: :class:`str`, optional
            1-100 character description of the command; default the command name
        options: List[:class:`~SlashOptions`], optional
            The parameters for the command; default MISSING
        choices: List[:class:`dict`], optional
            Choices for string and int types for the user to pick from; default MISSING
        guild_ids: List[:class:`str` | :class:`int`], optional
            A list of guild ids where the command is available; default MISSING
        default_permission: :class:`bool`, optional
            Whether the command can be used by everyone or not
        guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
            The permissions for the command in guilds
                Format: ``{"guild_id": SlashPermission}``

    Decorator
    ---------

        callback: :class:`method(ctx)`
            The asynchron function that will be called if the command was used
                ctx: :class:`~SlashedCommand`
                    The used slash command

                .. note::

                    ``ctx`` is just an example name, you can use whatever you want for that

    Example
    --------

    .. code-block::

        class My_Cog(commands.Cog)
            ... 

            @slash_cog(name="hello_world", options=[
                SlashOption(str, name="parameter", description="this is a parameter", choices=[{ "name": "choice 1", "value": "test" }])
            ], guild_ids=["785567635802816595"], default_permission=False, 
            guild_permissions={
                    "785567635802816595": SlashPermission(allowed={"539459006847254542": SlashPermission.USER})
                }
            )
            async def hello_world(self, ctx, parameter = None):
                ...
    """
    def wraper(callback):
        return CogCommand(callback, name, description, options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
    return wraper
def subslash_cog(base_names, name=MISSING, description=MISSING, options=[], guild_ids=MISSING, default_permission=MISSING, guild_permissions=MISSING):
    """A decorator for cogs that will register a subcommand/subcommand-group
        
    command in discord
        ``/base_names... name [options]``

    Parameters
    ----------
        base_names: List[:class:`str`] | :class:`str`
            The names of the parent bases, currently limited to 2
                If you want to make a subcommand (``/base name``), you have to use a str instead of a list
        name: :class:`str`, optional
            1-32 characters long name; default MISSING
            
            .. note::

                The name will be corrected automaticaly (spaces will be replaced with "-" and the name will be lowercased)
        description: :class:`str`, optional
            1-100 character description of the command; default the command name
        options: List[:class:`~SlashOptions`], optional
            The parameters for the command; default MISSING
        choices: List[:class:`dict`], optional
            Choices for string and int types for the user to pick from; default MISSING
        guild_ids: List[:class:`str` | :class:`int`], optional
            A list of guild ids where the command is available; default MISSING
        default_permission: :class:`bool`, optional
            Whether the command can be used by everyone or not
        guild_permissions: Dict[``guild_id``: :class:`~SlashPermission`]
            The permissions for the command in guilds
                Format: ``{"guild_id": SlashPermission}``

        .. note::

            Permissions will be the same for every subcommand with the same base

    Decorator
    ---------
        callback: :class:`method(ctx)`
            The asynchron function that will be called if the command was used
                ctx: :class:`~SlashedSubCommand`
                    The used slash command

                .. note::

                    ``ctx`` is just an example name, you can use whatever you want for that
    
    Example
    --------
    subcommand

    .. code-block::

        class My_Cog(commands.Cog):
            ...

            @subslash_cog(base_names="hello", name="world", options=[
                SlashOption(argument_type="user", name="user", description="the user to tell the holy words")
            ], guild_ids=["785567635802816595"])
            async def command(ctx, user):
                ...

    subcommand-group

    .. code-block::

        class My_Cog(commands.Cog):
            ...

            @subslash_cog(base_names=["hello", "beautiful"], name="world", options=[
                SlashOption(argument_type="user", name="user", description="the user to tell the holy words")
            ], guild_ids=["785567635802816595"])
            async def command(ctx, user):
                ...

    """
    def wraper(callback):
        return CogSubCommandGroup(callback, base_names, name, description=description, options=options, guild_ids=guild_ids, default_permission=default_permission, guild_permissions=guild_permissions)
    return wraper
def context_cog(type: Literal["user", 2, "message", 3], name=MISSING, guild_ids=MISSING, default_permission=MISSING, guild_permission=MISSING):
    """Decorator for cogs that will register a context command in discord
            ``Right-click message or user`` -> ``apps`` -> ``commands is displayed here``


        Parameters
        ----------
            type: Literal[``'user'``, ``2`` | ``'message'`` | ``3``]
                The type of the contextcommand. 
                    ``'user'`` and ``2`` are user-commands; ``'message'`` and ``3`` are message-commansd
            name: :class:`str`, optional
                The name of the command; default MISSING
            guild_ids: List[:class:`str` | :class:`int`]
                A list of guilds where the command can be used
            default_permission: :class:`bool`, optional
                Whether the command can be used by everyone; default True
            guild_permissions: Dict[:class:`SlashPermission`], optional
                Special permissions for guilds; default MISSING

        Decorator
        ---------

            callback: :class:`method(ctx, message)`
                The asynchron function that will be called if the command was used
                    ctx: :class:`~SlashedSubCommand`
                        The used slash command
                    message: :class:`~Message`
                        The message on which the command was used
                    
                    .. note::

                        ``ctx`` and ``message`` are just example names, you can use whatever you want for that
        
        Example
        -------
        
        .. code-block::

            class My_Cog(commands.Cog):
                ...

                # message command
                @context_cog(type="message", name="quote", guild_ids=["785567635802816595"])
                async def quote(ctx, message):
                    ...
                
                # user command
                @context_cog(type="user", name="mention", guild_ids=[785567635802816595])
                async def mention(ctx, user):
                    ...
        """
    def wraper(callback):
        if type in ["user", 2]:
            return CogMessageCommand(callback, name, guild_ids=guild_ids, default_permission=default_permission, guild_permission=guild_permission)
        elif type in ["message", 3]:
            return CogUserCommand(callback, name, guild_ids=guild_ids, default_permission=default_permission, guild_permission=guild_permission)
        else:
            raise InvalidArgument("Invalid context type! type has to be one of 'user', 1, 'message', 2!")
    return wraper
def listening_component_cog(custom_id, messages=MISSING, users=MISSING, component_type: Literal['button', 'select'] = MISSING, check=lambda _ctx: True):
    """Decorator for cogs that will register a listening component

    Parameters
    ----------
        custom_id: :class:`str`
            The custom_id of the components to listen to
        messages: List[:class:`discord.Message` | :class:`int` :class:`str`], Optional
            A list of messages or message ids to filter the listening component
        users: List[:class:`discord.User` | :class:`discord.Member` | :class:`int` | :class:`str`], Optional
            A list of users or user ids to filter
        component_type: Literal[``'button'`` | ``'select'``]
            What type the used component has to be of (select: SelectMenu, button: Button)
        check: :class:`function`, Optional
            A function that has to return True in order to invoke the listening component
                The check function takes to parameters, the component and the message

    Decorator
    ---------
        callback: :class:`method(ctx)`
            The asynchron function that will be called if a component with the custom_id was invoked

            There will be one parameters passed

                ctx: :class:`~PressedButton` or :class:`~SelectedMenu`
                    The invoked component
                
                .. note::

                    ``ctx`` is just an example name, you can use whatever you want for it

    Example
    -------
    
    .. code-block::
    
        @ui.components.listening_component("custom_id", [539459006847254542], [53945900682362362])
        async def callback(ctx):
            ...
    """
    def wraper(callback):
        return ListeningComponent(callback, messages, users, component_type, check, custom_id)
    return wraper
