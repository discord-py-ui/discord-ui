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

To add a button listener, you need to use the ``Listener.button`` deorator

.. code-block::

    class MyListener(Listener):
        ...

        @Listener.button("custom_id here")
        async def somebutton(self, ctx):
            ...

Listeners
---------


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

There are some more usefull things you can use


Class
-----

You can add a timeout to the listener after which the listener will be removed from the message

.. code-block::

    .. code-block::

    class MyListener(Listener):
        def __init__(self):
            self.timeout = 20   # 20 seconds timeout

If you set timeout to ``None``, the listener will never timeout

Sending
--------

To send components and add the listener, you can use four different ways

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

        await message.channel.send("showcase", components=[Button("test", "this is a showcase")], listener=MyListener())

Second method:

.. code-block::

    @bot.listen()
    async def on_message(message)
        class MyListener(Listener):
            def __init__(self):
                self.components = [Button("test", "this is a showcase")]
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
                pass
            @Listener.button("test")
            async def test(self, ctx):
                ...

        msg = await message.channel.send("showcase", components=[Button("test", "this is a showcase")])
        msg.attach_listener(MyListener())

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

        msg = await message.channel.send("showcase", components=[Button("test", "this is a showcase")])
        ui.components.attach_listener_to(msg, MyListener())
"""

from .tools import setup_logger
from .components import Button, ComponentType, LinkButton, SelectMenu
from .receive import ComponentContext

import discord
from discord.ext import commands
from discord.state import ConnectionState

import asyncio
from inspect import getmembers
from typing import Dict, List, Union

logging = setup_logger(__name__)

class _Listener():
    def __init__(self, callback, custom_id, component_type, values=None) -> None:
        self.callback = callback
        self.custom_id = custom_id
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
            raise commands.errors.CheckFailure()
        await self.callback(listener, ctx)

class NoListenerFound(Exception):
    """Exception that will be thrown when no matching listener was found"""
    def __init__(self, msg=None, *args: object) -> None:
        super().__init__(msg or "Could not find a matching listener", *args)
class WrongUser(Exception):
    def __init__(self, msg=None, *args: object) -> None:
        super().__init__(msg or "Wrong user used component", *args)


class Listener():
    """A class for a listener attached to a message that will receive components of it

    To use this class you have to create a subclass inhering this class

    Example
    --------

    .. code-block::

        class MyListener(Listener):
            def __init__(self, ...)
                ...

    Parameters
    -----------
    timeout: :class:`float`, optional
        A timeout after how many seconds the listener shouold be deleted.
        If ``None``, the listener will never timeout
    target_user: :class:`discord.Member` | :class:`discord.User`
        The user from which the interactions should be received. 
        Every interaction by other users will be ignored
    """
    def __init__(self, timeout=180.0, target_user=None) -> None:
        self.timeout: float = timeout
        """Timeout after how many seconds the listener should timeout and be deleted"""
        self.target_user: Union[discord.Member, discord.User] = target_user
        """The user from who the interaction has to come8"""
        self.components: List[Union[List[Button, LinkButton, SelectMenu], Button, LinkButton, SelectMenu]] = []
        """The components that are going to be send together with the listener"""
    def __init_subclass__(cls) -> None:
        cls.__listeners__ = []

    @staticmethod
    def button(custom_id=None):
        """A decorator that will setup a callback for a button
        
        Parameters
        ----------
        custom_id: :class:`str`, optional
            The custom id of the target button. 
            If no custom_id is passed, the name of the callback will be used for the custom id.

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
        def wraper(callback):
            return _Listener(callback, custom_id or callback.__name__, ComponentType.Button)
        return wraper
    @staticmethod
    def select(custom_id=None, values=None):
        """A decorator that will set a callback up for a selecct menu
        
        Parameters
        ----------
        custom_id: :class:`str`, optional
            The custom id of the target menu. If no id specified, the name of the callback will be used.
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
        def wraper(callback):
            return _Listener(callback, custom_id or callback.__name__, ComponentType.Select, values)
        return wraper

    async def _call_listeners(self, interaction_component):
        listeners = self._get_listeners_for(interaction_component)
        if len(listeners) > 0:
            for listener in listeners:
                await listener.invoke(interaction_component, self)
        else:
            raise NoListenerFound()
    def _get_listeners(self) -> Dict[str, List[_Listener]]:
        all_listeners = [x[1] for x in getmembers(self, predicate=lambda x: isinstance(x, _Listener))]
        listeners = {}
        for lister in all_listeners:
            if not listeners.get(lister.custom_id):
                listeners[lister.custom_id] = []
            listeners[lister.custom_id].append(lister)
        return listeners

    def _get_listeners_for(self, interaction_component: ComponentContext) -> _Listener:
        listeners = self._get_listeners()
        listers = []
        for listener in listeners.get(interaction_component.custom_id):
            if hasattr(self, 'target_user') and self.target_user.id != interaction_component.author.id:
                continue
            if listener.type == interaction_component.component_type:
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
    def _start(self, state, message_id: int):
        self._state: ConnectionState = state
        self._target_message_id = str(message_id)
        self._state._component_listeners[self._target_message_id] = self
        
        # region removal
        loop = asyncio.get_event_loop()
        if getattr(self, 'timeout', None) is not None:
                loop.call_later(self.timeout, self._stop)
    def attach_me_to(self, message):
        """Attaches this listener to a message after it was sent
        
        Parameters
        ----------
        message: :class:`~Message`
            The target message
        
        """
        self._start(message._state, message.id)
    async def put_me_to(self, message):
        """Attaches this listener to a message and edits it if the message is missing components
        
        Parameters
        ----------
        message: :class:`~Message`
            The target message
        
        """
        if len(message.components) == 0:
            await message.edit(components=self.to_components)
        self.attach_me_to(message)