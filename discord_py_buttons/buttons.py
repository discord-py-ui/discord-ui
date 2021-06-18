from discord import Emoji
from discord.errors import InvalidArgument


class Button:
    """
    Represents a message component Button

    Attributes
    ----------------
    content: `str`
        The whole text on the button
    custom_id: `str`
        A custom_id for identefying the button
    label: `str`
        The text that appears on the button
    color: `int`
        The color of the button
    emoji: `str or discord.Emoji`
        The emoji that appears befor the label
    new_line: `bool`
        Whether a new line should be added before the button
    disabled: `bool`
        Whether the button is clickable or not
    hash: `str`
        A unique hash for the button
    """

    def __init__(
        self,
        custom_id: str,
        label: str = None,
        color: str or int = "blurple",
        emoji: Emoji or str = None,
        new_line: bool = False,
        disabled: bool = False,
    ) -> None:
        """Creates a new Button Object

        Parameter
        ----------------
        ```py
        (str) custom_id
        ```
            A identifier for the button, max 100 characters
        ```py
        (str) label
        ```
            Text that appears on the button, max 80 characters
        ```py
        (str or int) color
        ```
            The color of the button
        ```py
        (discord.Emoji or str) emoji
        ```
            The emoji displayed before the text
        ```py
        (bool) new_line
        ```
            Whether a new line should be added before the button
        ```py
        (bool) disabled
        ```
            Whether the button is disabled, default `False`


        Exceptions
        ----------------
        ```py
        InvalidArgument
        ```
        - the custom_id is longer than 100 characters or is empty
        - the label is longer than 80 characters
        - No label and no emoji
        - an ivalid color was passed
        - passed agrument is wrong type
        """
        if label is None and emoji is None:
            raise InvalidArgument("You need to pass a label or an emoji")
        if label is not None and type(label) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(label)))
        if type(custom_id) is not str:
            raise InvalidArgument(
                "custom_id must be of type str, not " + str(type(custom_id))
            )
        if type(disabled) is not bool:
            raise InvalidArgument("disabled must be of type bool")
        if emoji is not None and type(emoji) not in [Emoji, str, dict]:
            raise InvalidArgument(
                "emoji msut be of type discord.Emoji or str, not " + str(type(emoji))
            )
        if len(custom_id) > 100:
            raise InvalidArgument("custom_id maximum character limit (100) exceeded")
        if len(custom_id) < 1:
            raise InvalidArgument("custom_id must be longer than 0 characters")
        if label is not None and len(label) > 80:
            raise InvalidArgument("lavel maximum character limit (80) exceeded")
        if label is not None and len(label) < 1:
            raise InvalidArgument("label must be longer than 0 characters")
        if Colors.getColor(color) is None:
            raise InvalidArgument(str(color) + " is not a valid color")

        self.new_line = new_line
        self._json = {
            "type": 2,
            "custom_id": custom_id,
            "style": Colors.getColor(color),
            "disabled": bool(disabled),
        }
        if label is not None:
            self._json["label"] = label
        if emoji is not None:
            if type(emoji) is str:
                self._json["emoji"] = {"id": None, "name": emoji}
            elif type(emoji) is Emoji:
                self._json["emoji"] = {
                    "id": emoji.id,
                    "name": emoji.name,
                    "animated": emoji.animated,
                }
            elif type(emoji) is dict:
                self._json["emoji"] = emoji

    def to_dict(self):
        """Converts to a dict"""
        return self._json

    # region props
    @property
    def content(self):
        return (self.emoji + " " if self.emoji is not None else "") + (
            self.label if self.label is not None else ""
        )

    @property
    def custom_id(self) -> str:
        """The custom_id for identifiying the button"""
        return self._json["custom_id"]

    @custom_id.setter
    def custom_id(self, val: str):
        if type(val) is not str:
            raise InvalidArgument(
                "custom_id must be of type str, not " + str(type(val))
            )

        if len(val) > 100:
            raise InvalidArgument("custom_id must be shorter than 100 characters")
        if len(val) < 1:
            raise InvalidArgument("custom_id must be longer than 0 characters")

        self._json["custom_id"] = str(val)

    @property
    def label(self) -> str:
        """The lbel displayed on the button"""
        return self._json.get("label", None)

    @label.setter
    def label(self, val: str):
        if type(val) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(val)))
        if len(val) > 80:
            raise InvalidArgument("label must be shorter than 80 characters")
        if len(val) < 1:
            raise InvalidArgument("label must be longer than 0 characters")

        self._json["label"] = str(val)

    @property
    def color(self) -> int:
        """The color for the button"""
        return self._json["style"]

    @color.setter
    def color(self, val):
        if Colors.getColor(val) is None:
            raise InvalidArgument(str(val) + " is not a valid color")
        self._json["style"] = Colors.getColor(val)

    @property
    def emoji(self) -> str or Emoji:
        """Emoji mention before the text"""
        if "emoji" not in self._json:
            return None
        if "id" not in self._json["emoji"]:
            return self._json["emoji"]["name"]
        return f'<{"a" if "animated" in self._json["emoji"] else ""}:{self._json["emoji"]["name"]}:{self._json["emoji"]["id"]}>'

    @emoji.setter
    def emoji(self, val: Emoji or str):
        if type(val) not in [Emoji, str]:
            raise InvalidArgument(
                "emoji msut be of type discord.Emoji or str, not " + str(type(val))
            )
        if type(val) is str:
            self._json["emoji"] = {"id": None, "name": val}
        elif type(val) is Emoji:
            self._json["emoji"] = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated,
            }

    @property
    def disabled(self) -> bool:
        """Whether the button is disabled"""
        return self._json["disabled"] if "disabled" in self._json else False

    @disabled.setter
    def disabled(self, val):
        if type(val) != bool:
            raise InvalidArgument("disabled must be type of bool")
        if "disabled" in self._json:
            self._json["disabled"] = bool(val)
        else:
            self._json |= {"disabled": bool(val)}

    @property
    def hash(self) -> str:
        return self._json.get("hash", None)

    # endregion

    @classmethod
    def _fromData(cls, data, new_line=False) -> "Button":
        b = cls("empty", "empty")
        b._json = data
        b.new_line = new_line
        return b


class LinkButton:
    """
    Represents a message component LinkButton

    Attributes
    ----------------
    content: `str`
        The whole content of the button text
    url: `str`
        The url which opens when the button is pressed
    label: `str`
        The text that appears on the button
    color: `int`
        One of button styles
    emoji: `discord.Emoji or str`
        The emoji before the label
    new_line: `bool`
        Whether a new line should be added before the button
    disabled: `bool`
        whether the button is clickable or not
    hash: `str`
        A unique hash for the button
    """

    def __init__(
        self,
        url: str,
        label: str = None,
        emoji: Emoji or str = None,
        new_line: bool = False,
        disabled: bool = False,
    ) -> None:
        """Creates a new LinkButton Object

        Parameter
        ----------------
        ```py
        (str) url
        ```
            A url which will be opened when pressing the button
        ```py
        (str) label
        ```
            Text that appears on the button, max 80 characters
        ```
        (discord.Emoji or str) emoji
        ```
            Emoji that appears before the label
        ```py
        (bool) new_line
        ```
            Whether a new line should be added before the button
        ```py
        (bool) disabled
        ```
            Whether the button is disabled, default `False`

        Exceptions
        ----------------
        ```py
        InvalidArgument
        ```
        - url doesn't start with 'http://' or 'https://'
        - the label is longer than 80 characters or 0
        - passed argument is wrong type

        """
        if label is None and emoji is None:
            raise InvalidArgument("You need to pass a label or an emoji")
        if label is not None and type(label) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(label)))
        if label is not None and type(label) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(label)))
        if type(url) is not str:
            raise InvalidArgument("url must be of type str, not " + str(type(url)))
        if not url.startswith("http://") and not url.startswith("https://"):
            raise InvalidArgument("Link must start with 'http://' or 'https://'")
        if type(disabled) is not bool:
            raise InvalidArgument(
                "disabled must be of type bool, not " + str(type(disabled))
            )
        if emoji is not None and type(emoji) not in [Emoji, str]:
            raise InvalidArgument(
                "emoji msut be of type discord.Emoji or str, not " + str(type(emoji))
            )
        if label is not None and len(label) > 80:
            raise InvalidArgument("lavel maximum character limit (80) exceeded")
        if label is not None and len(label) < 1:
            raise InvalidArgument("label must be longer than 0 characters")

        self.new_line = new_line
        self._json = {"type": 2, "url": url, "style": 5, "disabled": disabled}
        if label is not None:
            self._json["label"] = label
        if emoji is not None:
            self._json["emoji"] = {
                "id": None if type(emoji) is str else emoji.id,
                "name": emoji if type(emoji) is str else emoji.name,
                "animated": False if type(emoji) is str else emoji.animated,
            }

    def to_dict(self):
        return self._json

    # region props
    @property
    def content(self):
        return (self.emoji + " " if self.emoji is not None else "") + (
            self.label if self.label is not None else ""
        )

    @property
    def url(self) -> str:
        """The url which will be opened after the button is pressed"""
        return self._json["url"]

    @url.setter
    def url(self, val: str):
        if type(val) is not str:
            raise InvalidArgument("url must be of type str, not " + str(type(val)))
        if not val.startswith("http://") and not val.startswith("https://"):
            raise InvalidArgument("Link must start with 'https://' or 'http://'")
        self._json["url"] = val

    @property
    def label(self):
        return self._json.get("label", None)

    @label.setter
    def label(self, val):
        if type(val) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(val)))
        self._json["label"] = val

    @property
    def emoji(self) -> str or Emoji:
        """The emoji before the text"""
        if "emoji" not in self._json:
            return None
        if "id" not in self._json["emoji"]:
            return self._json["emoji"]["name"]
        return f'<{"a" if "animated" in self._json["emoji"] else ""}:{self._json["emoji"]["name"]}:{self._json["emoji"]["id"]}>'

    @emoji.setter
    def emoji(self, val: Emoji or str):
        if type(val) not in [Emoji, str]:
            raise InvalidArgument(
                "emoji msut be of type discord.Emoji or str, not " + str(type(val))
            )
        if type(val) is str:
            self._json["emoji"] = {"id": None, "name": val}
        elif type(val) is Emoji:
            self._json["emoji"] = {
                "id": val.id,
                "name": val.name,
                "animated": val.animated,
            }

    @property
    def color(self) -> int:
        """The Color for the button"""
        return self._json["style"]

    @property
    def disabled(self) -> bool:
        return self._json["disabled"]

    @disabled.setter
    def disabled(self, val):
        self._json["disabled"] = val

    @property
    def hash(self) -> str:
        return self._json.get("hash", None)

    # endregion

    @staticmethod
    def _fromData(data, new_line=False) -> "LinkButton":
        b = LinkButton("https://empty", "empty")
        b._json = data
        b.new_line = new_line
        return b


class Colors:
    """
    A class for button styles in message components

    Attributes
    ----------------
    Primary, blurple: `int`   => 1

    Secondary, grey: `int`    => 2

    Succes green: `int`       => 3

    Danger, red: `int`        => 4
    """

    Primary = blurple = 1
    Secondary = grey = 2
    Succes = green = 3
    Danger = red = 4

    @classmethod
    def getColor(cls, s):
        if type(s) is int:
            return s
        s = s.lower()
        if s in ("blurple", "primary"):
            return cls.blurple
        if s in ("grey", "secondary"):
            return cls.grey
        if s in ("green", "succes"):
            return cls.green
        if s in ("red", "danger"):
            return cls.red
