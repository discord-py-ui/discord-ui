import discord

class Button(object):
    def __init__(self, custom_id: str, color: str or int, label: str, inline: bool = False, disabled: bool = False) -> None:
        self.inline = inline

        self._json = {
            "type": 2,
            "custom_id": custom_id,
            "label": label,
            "style": Colors._getColor(color),
            "disabled": disabled
        }

    #region props
    @property
    def custom_id(self) -> str:
        """The customID for identifiying the button"""
        return self._json["custom_id"]
    @custom_id.setter
    def custom(self, val):
        self._json["custom_id"] = val

    @property
    def label(self) -> str:
        """The text on the button"""
        return self._json["label"]
    @label.setter
    def label(self, val):
        self._json["label"] = val

    @property
    def color(self) -> int:
        """The Color for the button"""
        return self._json["style"]
    @color.setter
    def color(self, val):
        self._json["style"] = val

    @property
    def disabled(self) -> bool:
        return self._json["disabled"] if "disabled" in self._json else False
    @disabled.setter
    def disabled(self, val):
        if "disabled" in self._json:
            self._json["disabled"] = val
        else:
            self._json |= {"disabled": val}
    #endregion
    @staticmethod
    def _fromData(data) -> 'Button':
        b = Button("", 1, "")
        b._json = data
        return b

class LinkButton(object):
    def __init__(self, url: str, label: str, inline: bool = False, disabled: bool = False) -> None:
        self.inline = inline

        self._json = {
            "type": 2,
            "url": url,
            "label": label,
            "style": 5,
            "disabled": disabled
        }

    #region props
    @property
    def url(self) -> str:
        """The url which will be opened after the button is pressed"""
        return self._json["url"]
    @url.setter
    def url(self, val: str):
        if not val.startswith("http://") and not val.startswith("https://"):
            raise discord.InvalidData("Link must start with 'https://' or 'http://'")
        self._json["url"] = val
    
    @property
    def label(self):
        return self._json["label"]
    @label.setter
    def label(self, val):
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
        self._json["disabled"] = disabled
    #endregion
    @staticmethod
    def _fromData(data) -> 'LinkButton':
        b = LinkButton("", "")
        b._json = data
        return b

class Colors:
    Primary = blurple = 1
    Secondary = grey = 2
    Succes = green = 3
    Danger = red = 4

    def _getColor(s):
        if type(s) == int:
            return s
        s = s.lower()
        if s in ("blurple", "primary"):
            return Colors.blurple
        if s in ("grey", "secondary"):
            return Colors.grey
        if s in ("green", "succes"):
            return Colors.green
        if s in ("red", "danger"):
            return Colors.red