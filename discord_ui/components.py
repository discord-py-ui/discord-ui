from __future__ import annotations

from discord.ext.commands import BadArgument

from .tools import All
from .enums import ButtonStyle, ComponentType
from .errors import InvalidLength, OutOfValidRange, WrongType

import discord
from discord import InvalidArgument

import inspect
import string
from random import choice
from typing import List, Union

__all__ = (
    'SelectMenu',
    'SelectOption',
    'Button',
    'LinkButton',
    'ActionRow'
)

class ComponentStore():
    """A class for storing message components together with some useful methods"""
    def __init__(self, components=[]):
        """Creates a new `ComponentStore`
        
        Parameters
        ----------
        components: List[:class:`Button` | :class:`LinkButton` | :class:`SelectMenu`]
            The components that should be stored
        
        """
        self._components: List[Union[Button, LinkButton, SelectMenu]] = []
        # for checks
        [self.append(x) for x in components]
    def _get_index_for(self, key):
        if isinstance(key, int):
            return key
        if isinstance(key, str):
            s = [i for i, x in enumerate(self._components) if x.custom_id == key]
            if len(s) == 0:
                raise KeyError(key)
            return s[0]
        raise WrongType(key, "index", ["str", "int"])
    def __getitem__(self, key):
        return self._components[self._get_index_for(key)]
    def __setitem__(self, key, value):
        self._components[self._get_index_for(key)] = value
    def __delitem__(self, key):
        self._components.pop(self._get_index_for(key))
    def __iter__(self):
        return iter(self._components)
    def __len__(self):
        return len(self._components)
    def __repr__(self):
        return f"<{self.__class__.__name__}{str(self._components)}>"
    
    def to_list(self):
        """Returns this class as an list"""
        return self._components
    def copy(self):
        return self.__class__()
    def append(self, item):
        if hasattr(item, "custom_id") and item.custom_id in [x.custom_id if hasattr(x, "custom_id") else None for x in self._components]:
            raise BadArgument(f"A component with the custom_id '{item.custom_id} already exists! CustomIds have to be unique'")
        self._components.append(item)
    def clear(self):
        self._components = []
    
    def disable(self, index=All, disable=True):
        """
        Disables or enables component(s)

        index: :class:`int` | :class:`str` | :class:`range` | List[:class:`int` | :class:`str`], optional
            Index(es) or custom_id(s) for the components that should be disabled or enabled; default all components
        disable: :class:`bool`, optional
            Whether to disable (``True``) or enable (``False``) components; default True

        """
        if index is All:
            index = range(len(self._components))
        if isinstance(index, (range, list, tuple)):
            for i in index:
                self._components[i].disabled = disable
        elif isinstance(index, (int, str)):
            self._components[index].disabled = disable
        return self
    @property
    def buttons(self) -> List[Union[Button, LinkButton]]:
        """All components with the type `Button`"""
        return [self._components[i] for i, x in enumerate(self._components) if x.component_type == ComponentType.Button]
    @property
    def selects(self) -> List[SelectMenu]:
        """All components with the type `Select`"""
        return [self._components[i] for i, x in enumerate(self._components) if x.component_type == ComponentType.Select]
    def get_rows(self) -> List[ComponentStore]:
        """
        Returns the component rows as componentstores
        
        Example
        --------
        
        If the components are
        
        ```
        Button1, Button2
        Button3
        SelectMenu
        ```

        The `.get_rows` method would then return

        ```py
        >>> message.get_rows()
        [ 
            ComponentStore[Button1, Button2], 
            ComponentStore[Button3], 
            ComponentStore[SelectMenu]
        ]
        ```

        """
        rows = []
        current_row = []
        for i, x in enumerate(self._components):
            if getattr(x, 'new_line', True) == True and i > 0:
                rows.append(ComponentStore(current_row))
                current_row = []
            current_row.append(self._components[i])
        if len(current_row) > 0:
            rows.append(ComponentStore(current_row))
        return rows

class SelectOption():
    """
    An option for a select menu
    
    Parameters
    ----------
    value: :class:`str`
        The dev-define value of the option, max 100 characters
    label: :class:`str`
        The user-facing name of the option, max 25 characters; default \u200b ("empty" char)
    description: :class:`str`, optional
        An additional description of the option, max 50 characters
    emoji: :class:`discord.Emoji` | :class:`str`, optional
        Emoji appearing before the label; default MISSING
    default: :class:`bool`
        Whether this option should be selected by default in the select menu; default False

    Raises
    -------
    :class:`WrongType`
        A value you want to set is not an instance of a valid type
    :class:`InvalidLenght`
        The lenght of a value is not valid
    :class:`OutOfValidRange`
        A value is out of its valid range
    """
    def __init__(self, value, label="\u200b", description=None, emoji=None, default=False) -> None:
        """
        Creates a new SelectOption

        Example:
        ```py
        SelectOption(label="This is a option", value="my_value", description="This is the description of the option")
        ```
        """
        self._label = None
        self._value = None
        self._description = None
        self._emoji = None

        self.default: bool = default
        """Whether this option is selected by default in the menu or not"""
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
    def __repr__(self) -> str:
        return f"<discord_ui.SelectOption(label={self.label}, value={self.value})>"

    @property
    def content(self) -> str:
        """The complete option content, consisting of the emoji and label"""
        return (self.emoji + " ") if self.emoji is not None else "" + (self.label or '')
    
    @property
    def label(self) -> str:
        """The main text appearing on the option """
        return self._label
    @label.setter
    def label(self, value: str):
        if value is None:
            value = ""
        elif value is not None and not isinstance(value, str):
            raise WrongType("label", value, "str")
        elif value is not None and len(value) > 100 and value > 0:
            raise InvalidLength("label", value, 100, 0)
        self._label = value

    @property
    def value(self) -> str:
        """A unique value for the option, which will be usedd to identify the selected value"""
        return self._value
    @value.setter
    def value(self, value):
        if inspect.isclass(value):
            raise WrongType("value", value, ["int", "str", "bool", "float"])
        if isinstance(value, str):
            if len(value) > 100 or len(value) < 1:
                raise InvalidLength("value", _min=1, _max=100)
        self._value = value

    @property
    def description(self) -> str:
        """A short description for the option"""
        return self._description
    @description.setter
    def description(self, value):
        if value is not None and not isinstance(value, str):
            raise WrongType("description", "str")
        if value is not None and len(value) > 100:
            raise InvalidLength("description", 100, 0)
        self._description = value
    
    @property
    def emoji(self) -> str:
        """
        The mention of the emoji before the text

            .. note::
                For setting the emoji, you can use a :class:`str` or a :class:`discord.Emoji`
        """
        if self._emoji is None:
            return None
        if "id" not in self._emoji:
            return self._emoji["name"]
        return f'<{"a" if "animated" in self._emoji else ""}:{self._emoji["name"]}:{self._emoji["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[discord.Emoji, str, dict]):
        """The emoji appearing before the label"""
        if val is None:
            self._emoji = None
        elif isinstance(val, str):
            self._emoji = {
                "id": None,
                "name": val
            }
        elif isinstance(val, discord.Emoji):
            self._emoji = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif isinstance(val, dict):
            self._emoji = val
        elif val is None:
            self._emoji = None
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])


    def to_dict(self) -> dict:
        payload = {
            "label": self._label,
            "value": self._value,
            "default": self.default
        }
        if self._description is not None:
            payload["description"] = self._description
        if self._emoji is not None:
            payload["emoji"] = self._emoji
        return payload

    @classmethod
    def _from_data(cls, data) -> SelectOption:
        """
        Initializes a new SelectOption from a dict
        
        Parameters
        ----------
        data: :class:`dict`
            The data to initialize from
        Returns
        -------
        :class:`~SelectOption`
            The new Option generated from the dict
        
        """
        x = SelectOption(data["value"], data.get("label"), data.get("description"), data.get("emoji"))
        x.default = data.get("default", False)
        return x

class Component():
    def __init__(self, component_type) -> None:
        self._component_type = getattr(component_type, "value", component_type)
    @property
    def component_type(self) -> ComponentType:
        """The component type"""
        return ComponentType(self._component_type)

class UseableComponent(Component):
    def __init__(self, component_type) -> None:
        Component.__init__(self, component_type)
    @property
    def custom_id(self) -> str:
        """A custom identifier for this component"""
        return self._custom_id
    @custom_id.setter
    def custom_id(self, value: str):
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("custom_id", 0, 100)
        if not isinstance(value, str):
            raise WrongType("custom_id", value, "str")
        self._custom_id = value

class SelectMenu(UseableComponent):
    """
    A ui-dropdown selectmenu

    Parameters
    ----------
    options: List[:class:`~SelectOption`]
        A list of options to select from
    custom_id: :class:`str`, optional
        The custom_id for identifying the menu, max 100 characters
    min_values: :class:`int`, optional
        The minimum number of items that must be chosen; default ``1``, min 0, max 25
    max_values: :class:`int`, optional
        The maximum number of items that can be chosen; default ``1``, max 25
    placeholder: :class:`str`, optional
        A custom placeholder text if nothing is selected, max 100 characters; default MISSING
    default: :class:`int` | :class:`range`, optional
        The position of the option that should be selected by default; default MISSING
    disabled: :class:`bool`, optional
        Whether the select menu should be disabled or not; default ``False``
    """
    def __init__(self, options, custom_id=None, min_values=1, max_values=1, placeholder=None, default=None, disabled=False) -> None:
        """
        Creates a new ui select menu

        Example:
        ```py
        SelectMenu(options=[SelectOption(...)], custom_id="my_id", min_values=2, placeholder="select something", default=0)
        ```
        """
        UseableComponent.__init__(self, ComponentType.Select)
        self.options: List[SelectOption] = options or None

        self.max_values: int = 0
        """The maximum number of items that can be chosen; default 1, max 25"""
        self.min_values: int = 0
        """
        The minimum number of items that must be chosen; default 1, min 0, max 25
        """
        self.disabled = disabled
        """
        Whether the selectmenu is disabled or not"""
        self.placeholder: str = placeholder
        """
        Custom placeholder text if nothing is selected"""
        self.custom_id = custom_id or ''.join([choice(string.ascii_letters) for _ in range(100)])
        self.disabled = disabled

        if min_values is not None and max_values is None:
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 0, 25)
            self.min_values = min_values
            self.max_values = min_values
        elif min_values is None and max_values is not None:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 0, 25)
            self.min_values = 1
            self.max_values = max_values
        elif min_values is not None and max_values is not None:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 0, 25)
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 0, 25)
            self.min_values = min_values
            self.max_values = max_values
        
        if default is not None:
            self.set_default_option(default)
    def __str__(self) -> str:
        return self.custom_id
    def __repr__(self) -> str:
        return f"<discord_ui.SelectMenu(custom_id={self.custom_id}, options={self.options})>"
    
    @staticmethod
    def _from_data(data) -> SelectMenu:
        return SelectMenu([
            SelectOption._from_data(d) for d in data["options"]
        ], data["custom_id"], data.get("min_values"), data.get("max_values"), data.get("placeholder"), disabled=data.get("disabled", False)
    )
    # region props
    
    @property
    def default_options(self) -> List[SelectOption]:
        """The option selected by default"""
        return [x for x in self.options if x.default]
    def set_default_option(self, position) -> SelectMenu:
        """
        Selects the default selected option

        Parameters
        ----------
        position: :class:`int` | :class:`range`
            The position of the option that should be default. 
            If ``position`` is of type :class:`range`, it will iterate through it and disable all components with the index of the indexes.
        """
        if not isinstance(position, (int, range)):
            raise WrongType("position", position, "int")
        if isinstance(position, int):
            if position < 0 or position >= len(self.options):
                raise OutOfValidRange("default option position", 0, str(len(self.options) - 1))
            self.options[position].default = True
            return self
        for pos in position:
            self.options[pos].default = True
    # endregion

    def to_dict(self) -> dict:
        payload = {
            "type": self._component_type,
            "custom_id": self._custom_id,
            "options": [x.to_dict() for x in self.options],
            "disabled": self.disabled,
            "min_values": self.min_values,
            "max_values": self.max_values
        }
        if self.placeholder is not None:
            payload["placeholder"] = self.placeholder
        return payload

class BaseButton(Component):
    def __init__(self, label, color, emoji, new_line, disabled) -> None:
        Component.__init__(self, ComponentType.Button)
        if label is None and emoji is None:
            raise InvalidArgument("You need to pass a label or an emoji")
        self._label = None
        self._style = None
        self._emoji = None
        self._url = None

        self.new_line = new_line
        self.label = label
        self.color = color
        self.disabled = disabled
        self.emoji = emoji

    def __repr__(self):
        return f"<{self.__class__.__name__}(custom_id={self.custom_id}, color={self.color})>"
    def __str__(self) -> str:
        return self.content
    def to_dict(self):
        payload = {"type": self._component_type, "style": self._style, "disabled": self.disabled, "emoji": self._emoji}
        if self._style == ButtonStyle.URL:
            payload["url"] = self._url
        else:
            payload["custom_id"] = self._custom_id
        if self._emoji is not None:
            payload["emoji"] = self._emoji
        if self._label is not None:
            payload["label"] = self._label
        return payload

    @property
    def content(self) -> str:
        """The complete content in the button ("{emoji} {label}")"""
        return (self.emoji + " " if self.emoji is not None else "") + (self.label or '')
        
    @property
    def label(self) -> str:
        """The label displayed on the button"""
        return self._label
    @label.setter
    def label(self, val: str):
        if val is None:
            val = ""
        elif val is not None and not isinstance(val, str):
            raise WrongType("label", val, "str")
        elif val is not None and len(val) > 100:
            raise InvalidLength("label", _max=100)
        elif val is not None and len(val) < 1:
            raise InvalidLength("label", _min=0)

        self._label = str(val)

    @property
    def color(self) -> int:
        """The color for the button"""
        return self._style
    @color.setter
    def color(self, val):
        if ButtonStyle.getColor(val) is None:
            raise InvalidArgument(str(val) + " is not a valid color")
        self._style = ButtonStyle.getColor(val).value
    
    @property
    def emoji(self) -> str:
        """
        The mention of the emoji before the text
        
            .. note::
                For setting the emoji, you can use a str or discord.Emoji          
        """
        if self._emoji is None:
            return None
        if "id" not in self._emoji:
            return self._emoji["name"]
        return f'<{"a" if "animated" in self._emoji else ""}:{self._emoji["name"]}:{self._emoji["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[discord.Emoji, str, dict]):
        if val is None:
            self._emoji = None
        elif isinstance(val, str):
            self._emoji = {
                "name": val
            }
        elif isinstance(val, discord.Emoji):
            self._emoji = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif isinstance(val, dict):
            self._emoji = val
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])

class Button(BaseButton, UseableComponent):
    """
    A ui-button

    Parameters
    ----------
    custom_id: :class:`str`, optional
        A identifier for the button, max 100 characters
            If no custom_id was passed, a random 100 character string will be generated
    label: :class:`str`, optional
        Text that appears on the button, max 80 characters; default \u200b ("empty" char)
    color: :class:`str` | :class:`int`, optional
        The color of the button; default "blurple"

        .. tip:

            You can either use a string for a color or an int. Color strings are: 
            (`primary`, `blurple`), (`secondary`, `grey`), (`succes`, `green`) and (`danger`, `Red`)
            
            If you want to use integers, take a lot at the :class:`~ButtonStyle` class

    emoji: :class:`discord.Emoji` | :class:`str`, optional
        The emoji displayed before the text; default MISSING
    new_line: :class:`bool`, optional
        Whether a new line should be added before the button; default False
    disabled: :class:`bool`, optional
        Whether the button is disabled; default False

    Raises
    -------
    :class:`WrongType`
        A value you want to set is not an instance of a valid type
    :class:`InvalidLenght`
        The lenght of a value is not valid
    :class:`OutOfValidRange`
        A value is out of its valid range
    :class:`InvalidArgument`
        The color you provided is not a valid color alias
    """
    def __init__(self, label="\u200b", custom_id=None, color="blurple", emoji=None, new_line=False, disabled=False) -> None:
        """
        Creates a new ui-button

        Example:
        ```py
        Button("This is a cool button", "my_custom_id", "green")
        ```
        """
        BaseButton.__init__(self, label, color, emoji, new_line, disabled)
        UseableComponent.__init__(self, self.component_type)
        self.custom_id = custom_id or ''.join([choice(string.ascii_letters) for _ in range(100)])
    def copy(self) -> Button:
        return self.__class__(
            label=self.label, 
            custom_id=self.custom_id, 
            color=self.color, 
            emoji=self.emoji, 
            new_line=self.new_line, 
            disabled=self.disabled
        )

    @classmethod
    def _from_data(cls, data, new_line=False) -> Button:
        """
        Returns a new button initialized from api response data

        Returns
        -------
        Button
            The initialized button
        """
        return Button(
            label=data.get("label"),
            custom_id=data["custom_id"],
            color=data["style"], 
            emoji=data.get("emoji"), 
            new_line=new_line, 
            disabled=data.get("disabled", False)
        )

class LinkButton(BaseButton):
    """
    A ui-button that will open a link when it's pressed

    Parameters
    ----------
    url: :class:`str`
        A url which will be opened when pressing the button
    label: :class:`str`, optional
        Text that appears on the button, max 80 characters; default \u200b ("empty" char)
    emoji: :class:`discord.Emoji` | :class:`str`, optional
        Emoji that appears before the label; default MISSING
    new_line: :class:`bool`, optional
        Whether a new line should be added before the button; default False
    disabled: :class:`bool`, optional
        Whether the button is disabled; default False

    Raises
    -------
    :class:`WrongType`
        A value you want to set is not an instance of a valid type
    :class:`InvalidLenght`
        The lenght of a value is not valid
    :class:`OutOfValidRange`
        A value is out of its valid range
    """
    def __init__(self, url, label="\u200b", emoji=None, new_line=False, disabled=False) -> None:
        """
        Creates a new LinkButton object
        
        Example:
        ```py
        LinkButton("https://discord.com/", "press me (if you can)!", emoji="😀", disabled=True)
        ```
        """
        BaseButton.__init__(self, label, ButtonStyle.URL, emoji, new_line, disabled)
        self._url = None
        self.url = url

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(url={self.url}, content={self.content}, custom_id={self.custom_id})>"
    def copy(self) -> LinkButton:
        return self.__class__(
            url=self.url, 
            label=self.label, 
            emoji=self.emoji, 
            new_line=self.new_line, 
            disabled=self.disabled
        )

    @property
    def url(self) -> str:
        """The link which will be opened when the button was pressed"""
        return self._url
    @url.setter
    def url(self, val: str):
        if not isinstance(val, str):
            raise WrongType("url", val, "str")
        self._url = str(val)

    @classmethod
    def _from_data(cls, data, new_line=False) -> LinkButton:
        return LinkButton(
            url=data["url"], 
            label=data.get("label"), 
            emoji=data.get("emoji"), 
            new_line=new_line, 
            disabled=data.get("disabled", False)
        )


class ActionRow():
    """
    Alternative to setting ``new_line`` in a full component list or putting the components in a list
        
    Only works for :class:`~Button` and :class:`~LinkButton`, because :class:`~SelectMenu` is always in a new line
    """
    def __init__(self, *items):
        """
        Creates a new component list

        Examples
        ```py
        ActionRow(Button(...), Button(...))
        
        ActionRow([Button(...), Button(...)])
        ```
        """
        self.items: List[Union[Button, LinkButton, SelectMenu]] = items[0] if all(isinstance(i, list) for i in items) else items
        """The componetns in the action row"""
        self.component_type = 1
        
    def disable(self, disable=True) -> ActionRow:
        for i, _ in enumerate(self.items):
            if isinstance(self.items[i], list):
                for j, _ in enumerate(self.items[i]):
                    self.items[i][j].disabled = disable
                continue
            self.items[i].disabled = disable
        return self
    def filter(self, check = lambda x: ...):
        """
        Filters all components
        
        Parameters
        ----------
        check: :class:`lambda`
            What condition has to be True that the component will pass the filter
        
        Returns
        -------
        List[:class:`~Button` | :class:`~LinkButton`]
            The filtered components
        
        """
        return [x for x in self.items if check(x)]


def make_component(data, new_line = False):
    if ComponentType(data["type"]) == ComponentType.Button:
        if data["style"] == ButtonStyle.URL:
            return LinkButton._from_data(data, new_line)
        return Button._from_data(data, new_line)
    if ComponentType(data["type"]) is ComponentType.Select:
        return SelectMenu._from_data(data)
    # if data["type"] == ComponentType.ACTION_ROW:
        # return ActionRow._from_data(data)