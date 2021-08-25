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
    def __init__(self, value, label="\u200b", description=MISSING, emoji=MISSING) -> None:
        """
        Creates a new SelectOption

        Example:
        ```py
        SelectOption(label="This is a option", value="my_value", description="This is the description of the option")
        ```
        """
        self._json = {}
        
        self.label = label
        self.value = value
        if description is not MISSING:
            self.description = description
        if emoji is not MISSING:
            self.emoji = emoji
    def __repr__(self) -> str:
        return f"<discord_ui.SelectOption({self.custom_id}:{self.content})>"

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
        return self._json["label"]
    @label.setter
    def label(self, value: str):
        if value is None:
            value = ""
        elif value is not None and type(value) is not str:
            raise WrongType("label", value, "str")
        elif value is not None and len(value) > 100 and value > 0:
            raise InvalidLength("label", value, 100, 0)
        self._json["label"] = value

    @property
    def value(self) -> Any:
        """
        A unique value for the option, which will be usedd to identify the selected value

        :type: :class:`str`
        """
        return self._json["value"]
    @value.setter
    def value(self, value):
        if inspect.isclass(value):
            raise WrongType("value", value, ["int", "str", "bool", "float"])
        self._json["value"] = value

    @property
    def description(self) -> str:
        """
        A description appearing on the option

        :type: :class:`str`
        """
        return self._json.get("description")
    @description.setter
    def description(self, value):
        if value is not MISSING and type(value) is not str:
            raise WrongType("description", "str")
        if value is not MISSING and len(value) > 50:
            raise InvalidLength("description", 50, 0)
        self._json["description"] = value
    
    @property
    def default(self) -> bool:
        """
        Whether the button is selected by default in the menu or not

        :type: :class:`bool`
        """
        return self._json.get("default", False)


    @property
    def emoji(self) -> str:
        """
        The mention of the emoji before the text

            .. note::
                For setting the emoji, you can use a str or discord.Emoji
        
        :type: :class:`str`
        """
        if "emoji" not in self._json:
            return None
        if "id" not in self._json["emoji"]:
            return self._json["emoji"]["name"]
        return f'<{"a" if "animated" in self._json["emoji"] else ""}:{self._json["emoji"]["name"]}:{self._json["emoji"]["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[Emoji, str, dict]):
        """The emoji appearing before the label"""
        if type(val) is str:
            self._json["emoji"] = {
                "id": None,
                "name": val
            }
        elif type(val) is Emoji:
            self._json["emoji"] = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif type(val) is dict:
            self._json["emoji"] = val
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])


    def to_dict(self) -> dict:
        return self._json

    @classmethod
    def _fromData(cls, data) -> "SelectOption":
        """Initializes a new SelectOption from a dict
        
        Parameters
        ----------
            data: :class:`dict`
                The data to initialize from
        Returns
        -------
            :class:`~SelectOption`
                The new Option generated from the dict
        
        """
        x = SelectOption("EMPTY", "EMPTY")
        x._json = data
        return x

class SelectMenu():
    """A select menu

    Parameters
    ----------
    custom_id: :class:`str`
        The custom_id for identifying the menu, max 100 characters
    options: List[:class:`~SelectOption`]
        A list of optionns to select from
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
    def __init__(self, custom_id, options, min_values = 1, max_values = 1, placeholder=MISSING, default=MISSING, disabled=False) -> None:
        """
        Creates a new ui select menu

        Example:
        ```py
        SelectMenu(custom_id="my_id", options=[SelectOption(...)], min_values=2, placeholder="select something", default=0)
        ```
        """
        self._json = { "type": ComponentType.SELECT_MENU }
        self.custom_id = custom_id
        self.disabled = disabled
        self.options = options

        if placeholder is not MISSING:
            self.placeholder = placeholder

        if min_values is not MISSING and max_values is MISSING:
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = min_values
            self.max_values = min_values
        elif min_values is MISSING and max_values is not MISSING:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = 1
            self.max_values = max_values
        elif min_values is not MISSING and max_values is not MISSING:
            if max_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            if min_values < 0 or min_values > 25:
                raise OutOfValidRange("min_values", 1, 25)
            self.min_values = min_values
            self.max_values = max_values
        
        if default is not MISSING:
            self.set_default_option(default)
    def __str__(self) -> str:
        return self.custom_id
    def __repr__(self) -> str:
        return f"<discord_ui.SelectMenu({self.custom_id}:{self.options})>"
    
    @classmethod
    def _fromData(cls, data) -> 'SelectMenu':
        x = cls._empty()
        x._json = data
        return x

    @staticmethod
    def _empty() -> 'SelectMenu':
        """
        Creates a new "empty" select menu
        
        Returns
        -------
            :class:`~SelectMenu`
                An "empty" SelectMenu
        """
        return SelectMenu("empty", [SelectOption("EMPTY", "EMPTY", "EMPTY")], 0, 0)

    # region props
    @property
    def component_type(self) -> int:
        """
        The message component type
        
            .. note::
                The message component type will be always 3, because 3 is a select menu
        
        :type: :class:`int`
        """
        return self._json["type"]
    @property
    def custom_id(self) -> str:
        """
        The custom_id of the menu to identify it

        :type: :class:`str`
        """
        return self._json["custom_id"]
    @custom_id.setter
    def custom_id(self, value: str):
        if len(value) > 100 or len(value) < 1:
            raise InvalidLength("custom_id", 0, 100)
        if type(value) is not str:
            raise WrongType("custom_id", value, "str")
        self._json["custom_id"] = value

    @property
    def options(self) -> List[SelectOption]:
        """
        The choices in the select menu to select from

        :type: List[:class:`~SelectOption`]
        """
        return [SelectOption._fromData(x) for x in self._json["options"]]
    @options.setter
    def options(self, value: List[SelectOption]):
        if type(value) is list:
            if len(value) > 25 or len(value) == 0:
                raise OutOfValidRange("options", 1, 25)
            if all(type(x) is SelectOption for x in value):
                self._json["options"] = [x.to_dict() for x in value]
            elif all(type(x) is dict for x in value):
                self._json["options"] = value
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
        """Selects the default selected option

        Parameters
        ----------
        position: :class:`int`
            The position of the option that should be default
        """
        if type(position) is not int:
            raise WrongType("position", position, "int")
        if position < 0 or position >= len(self.options):
            raise OutOfValidRange("default option position", 0, str(len(self.options) - 1))
        self._json["options"][position]["default"] = True
        return self
    
    @property
    def placeholder(self) -> Union[str, None]:
        """
        Custom placeholder text if nothing is selected

        :type: :class:`str` | :class:`None`
        """
        return self._json.get("placeholder")
    @placeholder.setter
    def placeholder(self, value: str):
        self._json["placeholder"] = value

    @property
    def min_values(self) -> int:
        """
        The minimum number of items that must be chosen; default 1, min 0, max 25

        :type: :class:`int`
        """
        return self._json["min_values"]
    @min_values.setter
    def min_values(self, value: int):
        self._json["min_values"] = value

    @property
    def max_values(self) -> int:
        """
        The maximum number of items that can be chosen; default 1, max 25

        :type: :class:`int`
        """
        return self._json["max_values"]
    @max_values.setter
    def max_values(self, value: int):
        self._json["max_values"] = value
    
    @property
    def disabled(self) -> bool:
        """
        Whether the selectmenu is disabled or not

        :type: :class:`bool`
        """
        return self._json.get('disabled', False)
    @disabled.setter
    def disabled(self, value):
        self._json["disabled"] = value

    @property
    def hash(self):
        """Hash for the selectmenu

        :type: :class:`str`
        """
        return self._json.get("hash")
    # endregion

    def to_dict(self) -> dict:
        return self._json

# region Button
class Button():
    """A discord-ui button

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
            
            If you want to use integers, take a lot at the :class:`~Colors` class

    emoji: :class:`discord.Emoji` | :class:`str`, optional
        The emoji displayed before the text; default MISSING
    new_line: :class:`bool`, optional
        Whether a new line should be added before the button; default False
    disabled: :class:`bool`, optional
        Whether the button is disabled; default False
    """
    def __init__(self, custom_id, label="\u200b", color = "blurple", emoji=MISSING, new_line=False, disabled=False) -> None:
        """
        Creates a new ui-button

        Example:
        ```py
        Button("my_custom_id", "This is a cool button", "green", new_line=True)
        ```
        """
        self._json = {"type": ComponentType.BUTTON}
        if label is MISSING and emoji is MISSING:
            raise InvalidArgument("You need to pass a label or an emoji")
        
        self.custom_id = custom_id
        self.new_line = new_line
        self.label = label
        self.color = color
        if emoji is not MISSING:
            self.emoji = emoji
        self.disabled = disabled
    def __str__(self) -> str:
        return self.content
    def __repr__(self) -> str:
        return f"<discord_ui.Button({self.custom_id}:{self.content})>"

    def to_dict(self):
        return self._json

    # region props
    @property
    def component_type(self) -> int:
        """
        The message component type

            .. note::
                The message component type will be always 2 (button)
        
        :type: :class:`int`
        """
        return self._json["type"]

    @property
    def content(self) -> str:
        """
        The complete content in the button ("{emoji} {label}")

        :type: :class:`str`
        """
        return (self.emoji + " " if self.emoji is not None else "") + (self.label or '')

    @property
    def custom_id(self) -> str:
        """
        The unique custom_id for identifiying the button

        :type: :class:`str`
        """
        return self._json["custom_id"]
    @custom_id.setter
    def custom_id(self, val: str):
        if type(val) is not str:
            raise WrongType("custom_id", val, "str")
        if len(val) > 100:
            raise InvalidLength("custom_id", _max=100)
        if len(val) < 1:
            raise InvalidLength("custom_id", _min=0)

        self._json["custom_id"] = str(val)

    @property
    def label(self) -> str:
        """
        The label displayed on the button

        :type: :class:`str`
        """
        return self._json.get("label", None)
    @label.setter
    def label(self, val: str):
        if val is None:
            val = ""
        elif val is not None and type(val) is not str:
            raise WrongType("label", val, "str")
        elif val is not None and len(val) > 80:
            raise InvalidLength("label", _max=80)
        elif val is not None and len(val) < 1:
            raise InvalidLength("label", _min=0)

        self._json["label"] = str(val)

    @property
    def color(self) -> int:
        """
        The color for the button

        :type: :class:`int`, one of :class:`~ButtonStyles`
        """
        return self._json["style"]
    @color.setter
    def color(self, val):
        if Colors.getColor(val) is None:
            raise InvalidArgument(str(val) + " is not a valid color")
        self._json["style"] = Colors.getColor(val)
    
    @property
    def emoji(self) -> str:
        """The mention of the emoji before the text
        
            .. note::
                For setting the emoji, you can use a str or discord.Emoji          
        
        :type: :class:`str`
        """
        if "emoji" not in self._json:
            return None
        if "id" not in self._json["emoji"]:
            return self._json["emoji"]["name"]
        return f'<{"a" if "animated" in self._json["emoji"] else ""}:{self._json["emoji"]["name"]}:{self._json["emoji"]["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[Emoji, str, dict]):
        if type(val) is str:
            self._json["emoji"] = {
                "id": None,
                "name": val
            }
        elif type(val) is Emoji:
            self._json["emoji"] = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif type(val) is dict:
            self._json["emoji"] = val
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])

    @property
    def disabled(self) -> bool:
        """
        Whether the button is dissabled
        If true, the button is shown but not clickable

        :type: :class:`bool`
        """
        return self._json["disabled"] if "disabled" in self._json else False
    @disabled.setter
    def disabled(self, val):
        if type(val) is not bool:
            raise WrongType("disabled", val, "bool")
        self._json["disabled"] = bool(val)
    
    @property
    def hash(self) -> str:
        """
        The calculated hash from the discord api for the button

        :type: :class:`str`
        """
        return self._json.get('hash', None)
    # endregion
    
    @classmethod
    def _empty(cls):
        """Returns an "empty" button"""
        return cls("empty", "empty")
    @classmethod
    def _fromData(cls, data, new_line=False) -> 'Button':
        """Returns a new button initialized from api response data

        Returns
        -------
        Button
            The initialized button
        """
        b = cls("empty", "empty")
        b._json = data
        b.new_line = new_line
        return b

class LinkButton():
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
    def __init__(self, url, label="\u200b", emoji=MISSING, new_line=False, disabled=False) -> None:
        """
        Creates a new LinkButton object
        
        Example:
        ```py
        LinkButton("https://discord.com/", "press me (if you can)!", emoji="😀", disabled=True)
        ```
        """
        self._json = { "type": ComponentType.BUTTON, "style": Colors.url }

        self.label = label
        self.url = url
        self.new_line = new_line
        self.disabled = disabled

        if emoji is not MISSING:
            self.emoji = emoji

    def __repr__(self) -> str:
        return f"<discord_ui.LinkButton({self.custom_id}:{self.content})>"
    def __str__(self) -> str:
        return self.content

    def to_dict(self):
        return self._json

    # region props
    @property
    def component_type(self) -> int:
        """
        The message component type

            .. note::
                The message component type will be always 2 (button)
        
        :type: :class:`int`
        """
        return self._json["type"]

    @property
    def content(self) -> str:
        """
        The complete content in the button ("{emoji} {label}")

        :type: :class:`str`
        """
        return (self.emoji + " " if self.emoji is not None else "") + (self.label or '')

    @property
    def url(self) -> str:
        """
        The link which will be opened upon pressing the button

        :type: :class:`str`
        """
        return self._json["url"]
    @url.setter
    def url(self, val: str):
        if type(val) is not str:
            raise WrongType("url", val, "str")
        self._json["url"] = str(val)

    @property
    def label(self) -> str:
        """
        The label displayed on the button

        :type: :class:`str`
        """
        return self._json.get("label", None)
    @label.setter
    def label(self, val: str):
        if val is None:
            val = ""
        elif val is not None and type(val) is not str:
            raise WrongType("label", val, "str")
        elif val is not None and len(val) > 80:
            raise InvalidLength("label", _max=80)
        elif val is not None and len(val) < 1:
            raise InvalidArgument("label", _min=0)

        self._json["label"] = str(val)

    @property
    def color(self) -> int:
        """
        The color for the button, will always be ``5`` (link)

        :type: :class:`int`
        """
        return self._json["style"]
    
    @property
    def emoji(self) -> str:
        """The mention of the emoji before the text
        
            .. note::
                For setting the emoji, you can use a str or discord.Emoji          
        
        :type: :class:`str`
        """
        if "emoji" not in self._json:
            return None
        if "id" not in self._json["emoji"]:
            return self._json["emoji"]["name"]
        return f'<{"a" if "animated" in self._json["emoji"] else ""}:{self._json["emoji"]["name"]}:{self._json["emoji"]["id"]}>'
    @emoji.setter
    def emoji(self, val: Union[Emoji, str, dict]):
        if type(val) is str:
            self._json["emoji"] = {
                "id": None,
                "name": val
            }
        elif type(val) is Emoji:
            self._json["emoji"] = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated
            }
        elif type(val) is dict:
            self._json["emoji"] = val
        else:
            raise WrongType("emoji", val, ["str", "discord.Emoji", "dict"])

    @property
    def disabled(self) -> bool:
        """
        Whether the button is dissabled
        If true, the button is shown but not clickable

        :type: :class:`bool`
        """
        return self._json["disabled"] if "disabled" in self._json else False
    @disabled.setter
    def disabled(self, val):
        if type(val) is not bool:
            raise WrongType("disabled", val, "bool")
        self._json["disabled"] = bool(val)
    # endregion

    @classmethod
    def _empty(cls):
        """Returns an empty button"""
        return cls("empty", "empty")
    @classmethod
    def _fromData(cls, data, new_line=False) -> 'LinkButton':
        """Returns a new Linkbutton initialized from api response data"""
        b = cls("https://empty", "empty")
        b._json = data
        b.new_line = new_line
        return b


class Colors:
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
        if type(s) is int:
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
    """Alternative to setting ``new_line`` in a full component list or putting the components in a list 
    
    Only works for :class:`~Button` and :class:`~LinkButton`, because :class:`~SelectMenu` is always in a new line
    
    Parameters
    ----------
        disbaled: :class:`bool`, optional
            Whether all components should be disabled; default False   
    """
    def __init__(self, *items, disabled = False):
        """Creates a new component list

        Examples
        ```py
        ActionRow(Button(...), Button(...))
        
        ActionRow([Button(...), Button(...)])
        ```
        """
        self.items = items[0] if all(type(i) is list for i in items) else items
        """The componetns in the action row"""
        self.component_type = 1
        self.disable(disabled)
        
    def disable(self, disable=True) -> 'ActionRow':
        for i, _ in enumerate(self.items):
            self.items[i].disabled = disable
        return self
    def filter(self, check = lambda x: ...):
        """Filters all components
        
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
    ACTION_ROW      =        1
    BUTTON          =        2
    SELECT_MENU     =        3

def make_component(data, new_line = False):
    if data["type"] == ComponentType.BUTTON:
        if data["style"] == Colors.url:
            return LinkButton._fromData(data, new_line)
        return Button._fromData(data, new_line)
    if data["type"] == ComponentType.SELECT_MENU:
        return SelectMenu._fromData(data, new_line)
    # if data["type"] == ComponentType.ACTION_ROW:
        # return ActionRow._fromData(data)