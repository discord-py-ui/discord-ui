"""
discord_ui.listeners
=====================

A module for listeners that are going to be attached to a message. 
You could think of it like a cog but for message components.


.. code-block::

    from discord_ui import Listener


- - -

Usage
======

To use the ``Listener`` class, you need to create a subclass of it

Example

.. code-block::

    class MyListener(Listener):
        ...

Listeners
---------

To add a button listener, you need to use the ``Listener.button`` deorator

.. code-block::

    class MyListener(Listener):
        ...

        @Listener.button("custom_id here")
        async def somebutton(self, ctx):
            ...

This will add a button listener that will wait for a button with the custom id "custom_id here"


To add a select listener, you need to use the ``Listener.select`` decoratorr

.. code-block::

    class MyListener(Listener):
        ...

        @Listener.select("my_id")
        async def someselect(self, ctx):
            ...
    
This will add a select menu listener that will wait for a select menu with the custom id "my_id"

You can filter the select callback with the ``values`` parameter

.. code-block::

    class MyListener(Listener):
        ...

        @Listener.select("my_id", values=["2"])
        async def someselect(self, ctx):
            ...

The callback will now be only called if the selected values of a select menu equal to ``values``

There are some more useful things you can use


Class
------

You can add a timeout to the listener after which the listener will be removed from the message

.. code-block::

    class MyListener(Listener):
        def __init__(self):
            self.timeout = 20   # 20 seconds timeout

If you **set** timeout to ``None``, the listener will never timeout

You can also add a list of target users to the listener

.. code-block::

    class MyListener(Listener):
        def __init__(self):
            self.target_users = [a, list, of, users]

And last but not least, you can supress the `discord_ui.listener.NoListenerFound` errors when no 
listener could be found

.. code-block::

    class MyListener(Listener):
        def __init__(self):
            self.supress_no_listener_found = True


Sending
--------

To send components and add the listener, you can use five different ways

First method:

.. code-block::

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                pass
            @Listener.button("test")
            async def test(self, ctx):
                ...

        await message.channel.send("showcase", components=[Button("this is a showcase", "test")], listener=MyListener())

Second method:

.. code-block::

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                self.components = [Button("this is a showcase", "test")]
            @Listener.button("test")
            async def test(self, ctx):
                ...

        # MyListener.components will be used for the components in the message
        await message.channel.send("showcase", listener=MyListener())

Third method:

.. code-block::

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                ...
            
            @Listener.button("test")
            async def test(self, ctx):
                ...

        msg = await message.channel.send("showcase", components=[Button("this is a showcase", "test")])
        msg.attach_listener(MyListener())

Fourth method:

.. code-block::

    ui = discord_ui.UI(bot)

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                pass
            @Listener.button("test")
            async def test(self, ctx):
                ...

        msg = await message.channel.send("showcase", components=[Button("this is a showcase", "test")])
        ui.components.attach_listener_to(msg, MyListener())

And the last method:

.. code-block::

    ui = discord_ui.UI(bot)

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                pass
            @Listener.button("test")
            async def test(self, ctx):
                ...

        msg = await message.channel.send("showcase", components=[Button("this is a showcase", "test")])
        MyListener().attach_me_to(msg)
"""

from .tools import setup_logger
from .receive import ComponentContext, Message, ButtonInteraction, SelectInteraction
from .components import Button, ComponentType, LinkButton, SelectMenu

import discord
from discord.ext.commands import CheckFailure

import asyncio
from inspect import getmembers
from typing import Dict, List, Union, Callable, Coroutine

__all__ = (
    'Listener',
)

logging = setup_logger(__name__)

class AnyID:
    pass

class _Listener():
    def __init__(self, callback, custom_id, component_type, values=None) -> None:
        self.callback = callback
        self.custom_id = custom_id or AnyID
        self.type = component_type
        self.target_values = [str(v) for v in values] if values is not None else None 

        self.__commands_checks__ = []
        if hasattr(self.callback, "__command_checks__"):
            self.__commands_checks__ = self.callback.__commands_checks__

    async def __call__(self, *args, **kwargs):
        return await self.invoke(*args, **kwargs)
    def add_check(self, check):
        self.__commands_checks__.append(check)
    def remove_check(self, check):
        self.__commands_checks__.remove(check)
    @property
    def checks(self):
        return self.__commands_checks__
    async def can_run(self, ctx):
        """Whether the command can be run"""
        predicates = self.checks
        if not predicates:
            # since we have no checks, then we just return True.
            return True
        return await discord.utils.async_all(predicate(ctx) for predicate in predicates)
    
    async def invoke(self, ctx, listener):
        if not await self.can_run(ctx):
            raise CheckFailure()
        await self.callback(listener, ctx)

class NoListenerFound(Exception):
    """Exception that will be thrown when no matching listener was found"""
    def __init__(self, msg=None, *args: object) -> None:
        super().__init__(msg or "Could not find a matching listener", *args)
class WrongUser(Exception):
    def __init__(self, msg=None, *args: object) -> None:
        super().__init__(msg or "Wrong user used component", *args)


class Listener():
    """A class for a listener attached to a message that will receive components of it.
        To use this class you have to create a subclass inhering this class


    Example
    -------

    .. code-block::

        class MyListener(Listener)
            ...

    Parameters
    -----------
    timeout: :class:`float`, optional
        A timeout after how many seconds the listener shouold be deleted.
        If ``None``, the listener will never timeout
    target_users: List[:class:`discord.Member` | :class:`discord.User` | :class:`int` | :class:`str`]
        A list of users or user ids from which the interactions has to be be received. 
        Every interaction by other users will be ignored
    """
    def __init__(self, timeout=180.0, target_users=None) -> None:
        self._target_users = []
        self.timeout: float = timeout
        """Timeout after how many seconds the listener should timeout and be deleted"""
        self.target_users = target_users
        self.components: List[Union[List[Button, LinkButton, SelectMenu], Button, LinkButton, SelectMenu]] = []
        """The components that are going to be send together with the listener"""
        self.message: Message = None
        """The target message"""
        self.supress_no_listener_found: bool = False
        """Whether `discord_ui.listener.NoListenerFound` should be supressed and not get thrown 
        when no target component listener could be found"""

    def __init_subclass__(cls) -> None:
        cls.__listeners__ = []
        cls.timeout = 180.0
        cls._target_users = None
        cls.supress_no_listener_found = False
        cls._on_error = {x[1].__exception_cls__: x[1] for x in getmembers(cls, predicate=lambda x: getattr(x, "__on_error__", False))}
        cls._wrong_user = next(iter([x[1] for x in getmembers(cls, predicate=lambda x: getattr(x, "__wrong_user__", False))]), None)


    @property
    def target_users(self) -> List[int]:
        """A list of user ids from which the interaction has to come"""
        return self._target_users
    @target_users.setter
    def target_users(self, value):
        if value != None:
            self._target_users = [int(getattr(x, 'id', x)) for x in value]
        else:
            self._target_users = None

    @staticmethod
    def button(custom_id=None):
        """A decorator that will setup a callback for a button
        
        Parameters
        ----------
        custom_id: :class:`str`, optional
            The custom id of the target button.  If no custom_id is passed, the name of the callback will be used for the custom id.
                Note that you can't have two callbacks with the same function name

        Example
        --------

        .. code-block::

            class MyListener(Listener):
                def __init__(self, ...):
                    ...

                @Listener.button("my_id")
                async def callback(self, ctx):
                    ...
        
        """
        def wrapper(callback):
            return _Listener(callback, custom_id, ComponentType.Button)
        return wrapper
    @staticmethod
    def select(custom_id=None, values=None):
        """A decorator that will set a callback up for a select menu
        
        Parameters
        ----------
        custom_id: :class:`str`, optional
            The custom id of the target menu. If no id specified, the name of the callback will be used.
                Note that you can't have two callbacks with the same function name
        values: List[:class:`str`], optional
            What values must be selected in order to invoke the callback; default None
        
        Example
        --------

        .. code-block::

            class MyListener(Listener):
            def __init__(self, ...)
                ...

            @Listener.select("my_id")
            async def callback(self, ctx):
                ...

            # This callback will be only called if the selected values of the menu are '2' 
            @Listener.select("my_id", values=['2'])
            async def othere_callback(self, ctx):
                ...
        """
        def wrapper(callback):
            return _Listener(callback, custom_id or callback.__name__, ComponentType.Select, values)
        return wrapper
    
    @staticmethod
    def on_error(exception_cls=BaseException):
        """Decorator for a function that will handle exceptions
        
        Parameters
        ----------
        exception_cls: :class:`class`, optional
            The type of the exception that should be handled; default Exception

        Example
        -------

        .. code-block::

            from discord.ext.commands import CheckFailure

            class MyListener(Listener):
                ...
            # exception handler for checkfailures
            @Listener.on_error(CheckFailure)
            async def check_failure(self, ctx, exception):
                await ctx.send("check failed: " + str(exception), hidden=True)
            @Listener.on_error(Exception)
            async def exception(self, ctx, exception):
                await ctx.send("base exception occured " + str(exception))
        
        """
        def wrapper(callback: Callable[[Listener, Union[ButtonInteraction, SelectInteraction], Exception], Coroutine[None, None, None]]):
            callback.__on_error__ = True
            callback.__exception_cls__ = exception_cls
            return callback
        return wrapper
    @staticmethod
    def wrong_user():
        """Decorator for a function that will be called when a user that is not in `.target_users` tried
        to use a component

        Example
        -------

        .. code-block::

            class MyListener(Listener):
                def __init__(self):
                    self.components = [Button()]
                    self.target_users = [785567635802816595]
                @Listener.button()
                async def a_button(self, ctx):
                    await ctx.send("you are allowed")
                @Listener.wrong_user()
                async def you_wrong(self, ctx):
                    await ctx.send("this component is not for you")


        """
        def wrapper(callback):
            callback.__wrong_user__ = True
            return callback
        return wrapper

    async def _call_listeners(self, interaction_component):
        listeners = self._get_listeners_for(interaction_component)
        if len(listeners) > 0:
            for listener in listeners:
                if self._target_users is not None and not interaction_component.author.id in self._target_users:
                    if self._wrong_user is not None:
                        await self._wrong_user(interaction_component)
                    raise WrongUser()
                try:
                    await listener.invoke(interaction_component, self)
                except tuple([x for x in self._on_error]) as ex:
                    handler = self._on_error.get(next(iter([x for x in self._on_error if isinstance(ex, x)]), None))
                    if handler is not None:
                        await handler(self, interaction_component, ex)
                    else:
                        raise ex
        elif not self.supress_no_listener_found:
            raise NoListenerFound()
    def _get_listeners(self) -> Dict[str, List[_Listener]]:
        all_listeners = [x[1] for x in getmembers(self, predicate=lambda x: isinstance(x, _Listener))]
        listeners = {}
        for lister in all_listeners:
            # prevent NoneType has no attribute 'append'
            if not listeners.get(lister.custom_id):
                listeners[lister.custom_id] = []
            listeners[lister.custom_id].append(lister)
        return listeners
    def _get_listeners_for(self, interaction_component: ButtonInteraction) -> List[_Listener]:
        listeners = self._get_listeners()
        listers = listeners.get(AnyID, []) # fill list with any_id listeners directly
        for listener in listeners.get(interaction_component.custom_id, []):
            if listener.type == interaction_component.component.component_type:
                if listener.target_values is not None:
                    if sorted(interaction_component.data["values"]) == sorted(listener.target_values):
                    # if all(v in interaction_component.data["values"] for v in listener.target_values):
                        listers.append(listener)
                else:
                    listers.append(listener)
        return listers
   
    def to_components(self):
        return self.components

    def _stop(self):
        del self._state._component_listeners[self._target_message_id]
        logging.debug("deleted listener")
    def _start(self, message):
        self.message = message
        self._state: discord.state.ConnectionState = message._state
        self._target_message_id = str(self.message.id)
        self._state._component_listeners[self._target_message_id] = self
        
        loop = asyncio.get_event_loop()
        # call deletion function later
        if getattr(self, 'timeout', None) is not None:
            loop.call_later(self.timeout, self._stop)
    
    def attach_me_to(self, message):
        """Attaches this listener to a message after it was sent
        
        Parameters
        ----------
        message: :class:`~Message`
            The target message
        
        """
        self._start(message)
    async def put_me_to(self, message):
        """Attaches this listener to a message and edits it if the message is missing components
        
        Parameters
        ----------
        message: :class:`~Message`
            The target message
        
        """
        if len(message.components) == 0:
            await message.edit(components=self.to_components())
        self.attach_me_to(message)