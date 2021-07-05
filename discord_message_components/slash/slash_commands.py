from discord_message_components.tools import MISSING


class BaseSlashCommand:
    def __init__(self, callback, name, description, choices=MISSING) -> None:
        self._json = {
            "name": name,
            "description": description,
        }
        if choices is not MISSING:
            self._json["choices"] = [x.to_dict() for x in choices]
        self.callback = callback

    def to_dict(self):
        return self._json


class SlashCommandOption:
    def __init__(
        self, type, name, description, required=False, choices=MISSING, options=MISSING
    ) -> None:
        self._json = {
            "type": type,
            "name": name,
            "description": description,
            "required": required,
        }
        if options is not MISSING:
            self._json["options"] = [x.to_dict() for x in options]
        if choices is not MISSING:
            self._json["choices"] = [x.to_dict() for x in choices]

    def to_dict(self):
        return self._json


class ApplicationCommandType:
    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
