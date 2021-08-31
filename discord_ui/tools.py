import logging
from typing import Any, List

class _MISSING:
    def __repr__(self) -> str:
        return "..."
    def __eq__(self, o: object) -> bool:
        return isinstance(o, _MISSING)
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)
    def __str__(self) -> str:
        return self.__repr__()
    def __sizeof__(self) -> int:
        return 0
    def get(self, *args):
        return self

MISSING = _MISSING()

def _or(*args, default=None):
    for i in range(len(args)):
        if args[i] not in [MISSING, None]:
            return args[i]
    return default

def get_index(l: list, elem: Any, mapping = lambda x: x, default: int = -1) -> int:
    """Returns the index of an element in the list
    
    Parameters
    ----------
        l: :class:`List`
            The list to get from
        elem: :class:`Any`
            The element that has to be found
        mapping: :class:`function`
            A function that will be applied to the current element that is checked, before comparing it to the target
        default: :class:`Any`
            The element that will be returned if nothing is found; default -1

    Returns
    -------
        :returns: The found element
        :type: :class:`Any`
    

    Example:
    ```py
    any_list = [(1, 2), (2, 3), (3, 4)]
    get(any_list, 4, lambda x: x[1])
    ```
    """
    i = 0
    for x in l: 
        if mapping(x) == elem: 
            return i
        i += 1
    return default

def get(l: list, elem: Any, mapping = lambda x: x, default: Any = None, check=lambda x: True):
    """Gets a element from a list
    
    Parameters
    ----------
        l: :class:`List`
            The list to get from
        elem: :class:`Any`
            The element that has to be found
        mapping: :class:`function`
            A function that will be applied to the current element that is checked, before comparing it to the target
        default: :class:`Any`
            The element that will be returned if nothing is found; default None

    Returns
    -------
        :returns: The found element
        :type: :class:`Any`


    Example:
    ```py
    any_list = [(1, 2), (2, 3), (3, 4)]
    get(any_list, 4, lambda x: x[1])
    ```
    """
    for x in l:
        if mapping(x) == elem and check(x) is True:
            return x
    return default

def components_to_dict(*components) -> List[dict]:
    """Converts a list of components to a dict that can be used for other extensions
    
    Parameters
    ----------
    components: :class:`*args` | :class:`list`
        A list of components that should be converted.
        
        Example
        
        .. code-block::

            # List of components with component rows (everything in [] defines that it will be in it's own component row)
            components_to_dict(Button(...), [Button(...), Button(...)], SelectMenu(...), LinkButton)
            # or
            components_to_dict([Button(...), [LinkButton(...), Button(...)]])

    Raises
    ------
        :raises: :class:`Exception` : Invalid Data was passed
    
    Returns
    -------
        :returns: The converted data
        :type: List[:class:`dict`]


    """
    wrappers: List[List[Any]] = []
    component_list = []
    if len(components) == 1 and type(components[0]) is list:
        components = components[0]

    if len(components) > 1:
        curWrapper = []
        i = 0
        for component in components:
            if hasattr(component, "items") or type(component) is list:
                if i > 0 and len(curWrapper) > 0:
                    wrappers.append(curWrapper)
                curWrapper = []
                wrappers.append(component.items if hasattr(component, "items") else component)
                continue
                
            # i > 0 => Preventing empty component field when first button wants to newLine 
            if component.component_type == 3:
                if i > 0:
                    wrappers.append(curWrapper)
                curWrapper = []
                wrappers.append(component)
            elif component.component_type == 2:
                if component.new_line and i > 0:
                    wrappers.append(curWrapper)
                    curWrapper = [component]
                else: 
                    curWrapper.append(component)
                    i += 1
        if len(curWrapper) > 0:
            wrappers.append(curWrapper)
    else:
        wrappers = [components]

    for wrap in wrappers:
        if type(wrap) is list and not all(hasattr(x, "to_dict") for x in wrap):
            raise Exception("Components with types [" + ', '.join([str(type(x)) for x in wrap]) + "] are missing to_dict() method")
        component_list.append({"type": 1, "components": [x.to_dict() for x in wrap] if type(wrap) is list else [wrap.to_dict()]})
    return component_list

def setup_logger(name):
    """
    Thx redstone ;)
    https://github.com/RedstoneZockt/rotstein-dc-py/blob/main/rotstein_py/logging.py
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.ERROR)
    
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(f"%(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.ERROR)
    
    logger.addHandler(stream_handler)
    return logger