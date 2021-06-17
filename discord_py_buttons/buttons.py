from discord.errors import InvalidArgument


class Button:
    """
    Represents a message component Button

    Attributes
    ----------------
    custom_id: `str`
        A custom_id for identefying the button
    label: `str`
        The text that appears on the button
    color: `int`
        The color of the button
    inline: `bool`
        Whether the button should be in the current line or in a new line
    disabled: `bool`
        whether the button is clickable or not
    """

    def __init__(
        self,
        custom_id: str,
        label: str,
        color: str or int = "blurple",
        inline: bool = False,
        disabled: bool = False,
    ) -> None:
        """Creates a new Button Object

        Parameter
        ----------------
        ```py
        (str) custom_id
        ```
        A developer-defined identifier for the button, max 100 characters
        ```py
        (str or int) color
        ```
        The color of the button
        ```py
        (str) label
        ```
        Text that appears on the button, max 80 characters
        ```py
        (bool) inline
        ```
        whether the button should be in a new line (False) or in the same, current line (True)
        ```py
        (bool) disabled
        ```
        Whether the button is disabled, default `False`


        Exceptions
        ----------------
        ```py
        InvalidArgument
        ```
        - the custom_id is longer than 100 characters or 0
        - the label is longer than 80 characters or 0
        - an ivalid color was passed
        - passed agrument is wrong type
        """
        if type(label) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(label)))
        if type(custom_id) is not str:
            raise InvalidArgument(
                "custom_id must be of type str, not " + str(type(custom_id))
            )
        if type(disabled) is not bool:
            raise InvalidArgument("disabled must be of type bool")
        if len(custom_id) > 100:
            raise InvalidArgument("custom_id maximum character limit (100) exceeded")
        if len(custom_id) < 1:
            raise InvalidArgument("custom_id must be longer than 0 characters")
        if len(label) > 80:
            raise InvalidArgument("lavel maximum character limit (80) exceeded")
        if len(label) < 1:
            raise InvalidArgument("label must be longer than 0 characters")
        if Colors._getColor(color) is not None:
            raise InvalidArgument(str(color) + " is not a valid color")

        self.inline = inline
        self._json = {
            "type": 2,
            "custom_id": custom_id,
            "label": label,
            "style": Colors._getColor(color),
            "disabled": bool(disabled),
        }

    def to_dict(self):
        """Converts to a dict"""
        return self._json

    # region props
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
        return self._json["label"]

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
        if Colors._getColor(val) is not None:
            raise InvalidArgument(str(val) + " is not a valid color")
        self._json["style"] = Colors._getColor(val)

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

    # endregion
    @classmethod
    def _fromData(cls, data) -> "Button":
        b = cls("", 1, "")
        b._json = data
        return b


class LinkButton:
    """
    Represents a message component LinkButton

    Attributes
    ----------------
    url: `str`
        The url which opens when the button is pressed
    label: `str`
        The text that appears on the button
    color: `int`
        One of button styles
    inline: `bool`
        Whether the button should be in the current line or in a new line
    disabled: `bool`
        whether the button is clickable or not
    """

    def __init__(
        self, url: str, label: str, inline: bool = False, disabled: bool = False
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
        ```py
        (bool) inline
        ```
        whether the button should be in a new line (False) or in the same, current line (True)
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
        if type(label) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(label)))
        if type(url) is not str:
            raise InvalidArgument("url must be of type str, not " + str(type(url)))
        if not url.startswith("http://") and not url.startswith("https://"):
            raise InvalidArgument("Link must start with 'http://' or 'https://'")
        if type(disabled) is not bool:
            raise InvalidArgument(
                "disabled must be of type bool, not " + str(type(disabled))
            )
        if len(label) > 80:
            raise InvalidArgument("lavel maximum character limit (80) exceeded")
        if len(label) < 1:
            raise InvalidArgument("label must be longer than 0 characters")

        self.inline = inline
        self._json = {
            "type": 2,
            "url": url,
            "label": label,
            "style": 5,
            "disabled": disabled,
        }

    def to_dict(self):
        return self._json

    # region props
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
        return self._json["label"]

    @label.setter
    def label(self, val):
        if type(val) is not str:
            raise InvalidArgument("label must be of type str, not " + str(type(val)))
        self._json["label"] = val

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

    # endregion

    @staticmethod
    def _fromData(data) -> "LinkButton":
        b = LinkButton("", "")
        b._json = data
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
    def _getColor(cls, s):
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
