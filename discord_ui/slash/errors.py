class AlreadyDeferred(Exception):
    """This type of exception is thrown whenever the user tries to defer an interaction which was already deferred"""

    def __init__(self, *args: object) -> None:
        super().__init__("Interaction was already deferred")
class EphemeralDeletion(Exception):
    """This exception is thrown whenever the user tries to delete an ephemeral message (cannot be deleted)"""
    
    def __init__(self, *args: object) -> None:
        super().__init__("Cannot delete an ephemeral message")
class MissingOptionParameter(Exception):
    """This exception is thrown whenever a callback is missing a parameter which was specified in the slash command"""
    
    def __init__(self, option_name, *args: object) -> None:
        super().__init__("Missing parameter '" + option_name + "' in callback function")
class OptionalOptionParameter(Exception):
    """This exception is thrown whenever a callback function has a required parameter which is marked optional in the slash command"""
    
    def __init__(self, param_name, *args: object) -> None:
        super().__init__("Parameter '" + param_name + "' in callback function needs to be optional (" + param_name + "=None)")
class NoAsyncCallback(Exception):
    """This exception is thrown whenever a sync callback was provided"""
    def __init__(self, *args: object) -> None:
        super().__init__("callback has to be async")
class CallbackMissingContextCommandParameters(Exception):
    """This exception is thrown whenever a callback is missing the context parmeters"""
    
    def __init__(self, *args: object) -> None:
        super().__init__("Callback function for context commands has to accept 2 parameters (the used command, the message/user on which the interaction was used)")
