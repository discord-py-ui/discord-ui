from discord.enums import ButtonStyle
from .tools import MISSING
from .errors import InvalidLength, OutOfValidRange, WrongType

from discord import Emoji
from discord.errors import InvalidArgument

import inspect
from typing import Any, List, Union

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
    emoji : :class:`discord.Emoji` | :class:`str`, optional
        Emoji appearing before the label; default MISSING
    """
    def __init__(self, value, label="\u200b", description=None, emoji=None) -> None:
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
        self.default: bool = False
        """
        Whether this option is selected by default in the menu or not

        :type: :class:`bool`
        """

        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
    def __repr__(self) -> str:
        return f"<discord_ui.SelectOption(label={self.label}, value={self.value})>"

    @property
    def content(self) -> str:
        """
        The complete option content, consisting of the emoji and label

        :type: :class:`str`
        """
        return (self.emoji + " ") if self.emoji is not None else "" + (self.label or '')
    
    @property
    def label(self) -> str:
        """
        The main text appearing on the option 

        :type: :class:`str`
        """
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
    def value(self) -> Any:
        """
        A unique value for the option, which will be usedd to identify the selected value

        :type: :class:`str`
        """
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
        """
        A description appearing on the option

        :type: :class:`str`
        """
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
                For setting the emoji, you can use a str or discord.Emoji
        
        :type: :class:`str`
        """
        if self._emoji is None:
            return None
        if "id" not in self._emoji:
            return self._emoji["name"]
        return f'<{"a" if "animated" in self._emoji else ""}:{self._emoji["name"]}:{self._emoji["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[Emoji, str, dict]):
        """The emoji appearing before the label"""
        if isinstance(val, str):
            self._emoji = {
                "id": None,
                "name": val
            }
        elif isinstance(val, Emoji):
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
    def _fromData(cls, data) -> "SelectOption":
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
        self._custom_id = None
        self._component_type = component_type
        self._hash = None
    @property
    def component_type(self) -> int:
        """
        The message component type

        :type: :class:`int`
        """
        return self._component_type
    @property
    def custom_id(self) -> str:
        """
        The custom_id of the menu to identify it

        :type: :class:`str`
        """
        return self._custom_id
    @custom_id.setter
    def custom_id(self, value: str):
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("custom_id", 0, 100)
        if not isinstance(value, str):
            raise WrongType("custom_id", value, "str")
        self._custom_id = value
    @property
    def hash(self):
        """
        The calculated hash from the discord api for the button

        :type: :class:`str`
        """
        return self._hash

class SelectMenu(Component):
    """
    Represents a ui-dropdown selectmenu

    Parameters
    ----------
    custom_id: :class:`str`
        The custom_id for identifying the menu, max 100 characters
    options: List[:class:`~SelectOption`]
        A list of options to select from
    min_values: :class:`int`, optional
        The minimum number of items that must be chosen; default ``1``, min 0, max 25
    max_values: :class:`int`, optional
        The maximum number of items that can be chosen; default ``1``, max 25
    placeholder: :class:`str`, optional
        A custom placeholder text if nothing is selected, max 100 characters; default MISSING
    default: :class:`int`, optional
        The position of the option that should be selected by default; default MISSING
    disabled: :class:`bool`, optional
        Whether the select menu should be disabled or not; default ``False``
    """
    def __init__(self, custom_id, options, min_values = 1, max_values = 1, placeholder=None, default=None, disabled=False) -> None:
        """
        Creates a new ui select menu

        Example:
        ```py
        SelectMenu(custom_id="my_id", options=[SelectOption(...)], min_values=2, placeholder="select something", default=0)
        ```
        """
        Component.__init__(self, ComponentType.SELECT_MENU)
        self._options = None

        self.max_values: int = 0
        """
        The maximum number of items that can be chosen; default 1, max 25

        :type: :class:`int`
        """
        self.min_values: int = 0
        """
        The minimum number of items that must be chosen; default 1, min 0, max 25

        :type: :class:`int`
        """
        self.disabled = disabled
        """
        Whether the selectmenu is disabled or not

        :type: :class:`bool`
        """
        self.placeholder: str = placeholder
        """
        Custom placeholder text if nothing is selected

        :type: :class:`str` | :class:`None`
        """
        self.custom_id = custom_id
        self.disabled = disabled
        self.options = options

        if min_values is not None and max_values is None:
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = min_values
            self.max_values = min_values
        elif min_values is None and max_values is not None:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = 1
            self.max_values = max_values
        elif min_values is not None and max_values is not None:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = min_values
            self.max_values = max_values
        
        if default is not None:
            self.set_default_option(default)
    def __str__(self) -> str:
        return self.custom_id
    def __repr__(self) -> str:
        return f"<discord_ui.SelectMenu(custom_id={self.custom_id}, options={self.options})>"
    
    @staticmethod
    def _fromData(data) -> 'SelectMenu':
        x = SelectMenu(data["custom_id"], data["options"], data.get("min_values"), data.get("max_values"), data.get("placeholder"), disabled=data.get("disabled", False))
        if data.get("hash") is not None:
            x._hash = data["hash"]

    # region props
    @property
    def options(self) -> List[SelectOption]:
        """
        The choices in the select menu to select from

        :type: List[:class:`~SelectOption`]
        """
        return [SelectOption._fromData(x) for x in self._options]
    @options.setter
    def options(self, value: List[SelectOption]):
        if isinstance(value, list):
            if len(value) > 25 or len(value) == 0:
                raise OutOfValidRange("length of options", 1, 25)
            if all(isinstance(x, SelectOption) for x in value):
                self._options = [x.to_dict() for x in value]
            elif all(isinstance(x, dict) for x in value):
                self._options = value
            else:
                raise WrongType("options", value, ["List[SelectOption]", "List[dict]"])
        else:
            raise WrongType("options", value, "list")

    @property
    def default_option(self) -> Union[SelectOption, None]:
        """
        The option selected by default

        :type: :class:`~SelectOption` | :class:`None`
        """
        x = [x for x in self.options if x.default]
        if len(x) == 1:
            return x[0]
    def set_default_option(self, position: int) -> 'SelectMenu':
        """
        Selects the default selected option

        Parameters
        ----------
        position: :class:`int`
            The position of the option that should be default
        """
        if not isinstance(position, int):
            raise WrongType("position", position, "int")
        if position < 0 or position >= len(self.options):
            raise OutOfValidRange("default option position", 0, str(len(self.options) - 1))
        self._options[position]["default"] = True
        return self
    
   
    @property
    def hash(self) -> str:
        """
        Hash for the selectmenu

        :type: :class:`str`
        """
        return self._hash
    # endregion

    def to_dict(self) -> dict:
        payload = {
            "type": self._component_type,
            "custom_id": self._custom_id,
            "options": self._options,
            "disabled": self._disabled,
            "min_values": self.min_values,
            "max_values": self.max_values
        }
        if self.placeholder is not None:
            payload["placeholder"] = self.placeholder
        return payload

# region Button
class BaseButton(Component):
    def __init__(self, label, color, emoji, new_line, disabled) -> None:
        Component.__init__(self, ComponentType.BUTTON)
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

    def __str__(self) -> str:
        return self.content
    def to_dict(self):
        payload = {"style": self._style, "disabled": self.disabled, "emoji": self._emoji}
        if self._style == ButtonStyle.link:
            payload["url"] = self._url
        else:
            payload["custom_id"] = self._custom_id
        if self._emoji is not None:
            payload["emoji"] = self._emoji
        if self._label is not None:
            payload["label"] = self._label

    @property
    def content(self) -> str:
        """
        The complete content in the button ("{emoji} {label}")

        :type: :class:`str`
        """
        return (self.emoji + " " if self.emoji is not None else "") + (self.label or '')
        
    @property
    def label(self) -> str:
        """
        The label displayed on the button

        :type: :class:`str`
        """
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
        """
        The color for the button

        :type: :class:`int`, one of :class:`~ButtonStyles`
        """
        return self._style
    @color.setter
    def color(self, val):
        if ButtonStyles.getColor(val) is None:
            raise InvalidArgument(str(val) + " is not a valid color")
        self._style = ButtonStyles.getColor(val)
    
    @property
    def emoji(self) -> str:
        """
        The mention of the emoji before the text
        
            .. note::
                For setting the emoji, you can use a str or discord.Emoji          
        
        :type: :class:`str`
        """
        if self._emoji is None:
            return None
        if "id" not in self._emoji:
            return self._emoji["name"]
        return f'<{"a" if "animated" in self._emoji else ""}:{self._emoji["name"]}:{self._json_emoji["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[Emoji, str, dict]):
        if isinstance(val, str):
            self._emoji = {
                "id": None,
                "name": val
            }
        elif isinstance(val, Emoji):
            self._emoji = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif isinstance(val, dict):
            self._emoji = val
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])
    

class Button(Component):
    """
    A ui-button

    Parameters
    ----------
    custom_id: :class:`str`
        A identifier for the button, max 100 characters
    label: :class:`str`, optional
        Text that appears on the button, max 80 characters; default \u200b ("empty" char)
    color: :class:`str` | :class:`int`, optional
        The color of the button; default "blurple"

        .. tip:

            You can either use a string for a color or an int. Color strings are: 
            (`primary`, `blurple`), (`secondary`, `grey`), (`succes`, `green`) and (`danger`, `Red`)
            
            If you want to use integers, take a lot at the :class:`~ButtonStyles` class

    emoji: :class:`discord.Emoji` | :class:`str`, optional
        The emoji displayed before the text; default MISSING
    new_line: :class:`bool`, optional
        Whether a new line should be added before the button; default False
    disabled: :class:`bool`, optional
        Whether the button is disabled; default False
    """
    def __init__(self, custom_id, label="\u200b", color = "blurple", emoji=None, new_line=False, disabled=False) -> None:
        """
        Creates a new ui-button

        Example:
        ```py
        Button("my_custom_id", "This is a cool button", "green", new_line=True)
        ```
        """
        BaseButton.__init__(self, label, color, emoji, new_line, disabled)
        self.custom_id = custom_id
    def __repr__(self) -> str:
        return f"<discord_ui.Button({self.custom_id}:{self.content})>"
    def copy(self) -> 'Button':
        return Button(self.custom_id, self.label, self.color, self.emoji, self.new_line, self.disabled)

    @classmethod
    def _fromData(cls, data, new_line=False) -> 'Button':
        """
        Returns a new button initialized from api response data

        Returns
        -------
        Button
            The initialized button
        """
        b = Button(data["custom_id"], data.get("label"), data["style"], data.get("emoji"), new_line, data.get("disabled", False))
        if data.get("hash"):
            b._hash = data["hash"]
        return b

class LinkButton(BaseButton):
    """
    A discord-ui linkbutton

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
    """
    def __init__(self, url, label="\u200b", emoji=None, new_line=False, disabled=False) -> None:
        """
        Creates a new LinkButton object
        
        Example:
        ```py
        LinkButton("https://discord.com/", "press me (if you can)!", emoji="😀", disabled=True)
        ```
        """
        BaseButton.__init__(self, label, ButtonStyles.url, emoji, new_line, disabled) 
        self._url = None
        self.url = url

    def __repr__(self) -> str:
        return f"<discord_ui.LinkButton({self.custom_id}:{self.content})>"
    def copy(self) -> 'LinkButton':
        x = LinkButton(self.url, self.label, self.emoji, self.new_line, self.disabled)
        x._hash = self._hash
        return x

    @property
    def custom_id(self):
        """Always ``None``"""
        return None

    @property
    def url(self) -> str:
        """
        The link which will be opened upon pressing the button

        :type: :class:`str`
        """
        return self._url
    @url.setter
    def url(self, val: str):
        if not isinstance(val, str):
            raise WrongType("url", val, "str")
        self._url = str(val)

    @classmethod
    def _fromData(cls, data, new_line=False) -> 'LinkButton':
        b = LinkButton(data["url"], data.get("label"), data.get("emoji"), new_line, data.get("disabled", False))
        if data.get("hash") is not None:
            b._hash = data["hash"]
        return b


class ButtonStyles:
    """
    A list of button styles (colors) in message components
    """
    Primary     =   blurple         = 1
    Secondary   =   grey            = 2
    Succes      =   green           = 3
    Danger      =   red             = 4
    url                             = 5

    @classmethod
    def getColor(cls, s):
        if isinstance(s, int):
            return s
        s = s.lower()
        if s in ("blurple", "primary"):
            return cls.blurple
        if s in ("grey", "gray", "secondary"):
            return cls.grey
        if s in ("green", "succes"):
            return cls.green
        if s in ("red", "danger"):
            return cls.red
# endregion


class ActionRow():
    """
    Alternative to setting ``new_line`` in a full component list or putting the components in a list
        
    Only works for :class:`~Button` and :class:`~LinkButton`, because :class:`~SelectMenu` is always in a new line
    
    Parameters
    ----------
        disbaled: :class:`bool`, optional
            Whether all components should be disabled; default False   
    """
    def __init__(self, *items, disabled = False):
        """
        Creates a new component list

        Examples
        ```py
        ActionRow(Button(...), Button(...))
        
        ActionRow([Button(...), Button(...)])
        ```
        """
        self.items = items[0] if all(isinstance(i, list) for i in items) else items
        """The componetns in the action row"""
        self.component_type = 1
        self.disable(disabled)
        
    def disable(self, disable=True) -> 'ActionRow':
        for i, _ in enumerate(self.items):
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
            :returns: The filtered components
            :type: List[:class:`~Button` | :class:`~LinkButton`]
        
        """
        return [x for x in self.items if check(x)]


class ComponentType:
    """
    A list of component types
    """
    ACTION_ROW      =       Action_row       =           1
    BUTTON          =        Button          =           2
    SELECT_MENU     =        Select          =           3

def make_component(data, new_line = False):
    if data["type"] == ComponentType.BUTTON:
        if data["style"] == ButtonStyles.url:
            return LinkButton._fromData(data, new_line)
        return Button._fromData(data, new_line)
    if data["type"] == ComponentType.SELECT_MENU:
        return SelectMenu._fromData(data)
    # if data["type"] == ComponentType.ACTION_ROW:
        # return ActionRow._fromData(data)