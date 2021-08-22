class DuplicateComponentListener(Exception):
    def __init__(self, custom_id, *args: object) -> None:
        super().__init__("Listener for custom_id " + custom_id + " is already in use")
class InvalidLength(Exception):
    """This exception is thrown whenever a invalid length was provided"""
    def __init__(self, my_name, _min=None, _max=None, *args: object) -> None:
        if _min is not None and _max is not None:
            err = "Length of '" + my_name + "' must be between " + str(_min) + " and " + str(_max)
        elif _min is None and _max is not None:
            err = "Length of '" + my_name + "' must be less than " + str(_max)
        elif _min is not None and _max is None:
            err = "Lenght of '" + my_name + "' must be more than " + str(_min)
        super().__init__(err)
class OutOfValidRange(Exception):
    """This exception is thrown whenever a value was ot of its valid range"""
    def __init__(self, name, _min, _max, *args: object) -> None:
        super().__init__("'" + name + "' must be in range " + str(_min) + " and " + str(_max))
class WrongType(TypeError):
    """This exception is thrown whenever a value is of the wrong type"""
    def __init__(self, name, me, valid_type, *args: object) -> None:
        super().__init__("'" + name + "' must be of type " + (str(valid_type) if type(valid_type) is not list else ' or '.join(valid_type)) + ", not " + str(type(me)))
class InvalidEvent(Exception):
    """This exception is thrown whenever a invalid eventname was passed"""
    def __init__(self, name, events, *args: object) -> None:
        super().__init__("Invalid event name, event must be " + " or ".join(events) + ", not " + str(name))
class MissingListenedComponentParameters(Exception):
    """This exception is thrown whenever a callback for a listening component is missing parameters"""
    def __init__(self, *args: object) -> None:
        super().__init__("Callback function for listening components needs to accept 2 parameters (the used component, the message)", *args)
class CouldNotParse(Exception):
    """This exception is thrown whenever the libary was unable to parse the data with the given method"""
    def __init__(self, data, type, method, *args: object) -> None:
        super().__init__("Could not parse '" + str(data) + " [" + str(type) + "]' with method " + str(method), *args)