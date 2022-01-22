from __future__ import annotations

import functools
import logging
import warnings
from typing import TYPE_CHECKING, Any, Callable, List, TypeVar

__all__ = (
    'components_to_dict',
)


class _All():
    def __init__(self) -> None:
        pass
    def __contains__(self, _):
        return True
    def __iter__(self):
        return iter([True])

All = _All()


class _MISSING:
    def __repr__(self) -> str:
        return "..."
    def __bool__(self) -> bool:
        return False
    def __eq__(self, o: object) -> bool:
        return isinstance(o, _MISSING)
    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)
    def __str__(self) -> str:
        return self.__repr__()
    def __sizeof__(self) -> int:
        return 0
    def __len__(self) -> int:
        return 0
    def __contains__(self, value):
        return False
    def get(self, *args):
        return self
class _EMPTY_CHECK():
    """An empty check that will always return True"""
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return True
    def __repr__(self) -> str:
        return "empty_check"

MISSING = _MISSING()
EMPTY_CHECK = _EMPTY_CHECK()

R = TypeVar("R")

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    P = ParamSpec('P')


def deprecated(instead=None) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def wrapper(callback: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(callback)
        def wrapped(*args: P.args, **kwargs: P.kwargs):
            if instead is not None:
                msg = f"{callback.__name__} is deprecated, use {instead} instead!"
            else:
                msg = f"{callback.__name__} is deprecated!"
            # region warning
            # turn filter off
            warnings.simplefilter('always', DeprecationWarning)
            # warn the user, use stacklevel 2
            warnings.warn(msg, stacklevel=2, category=DeprecationWarning)
            # turn filter on again
            warnings.simplefilter('default', DeprecationWarning) 
            # endregion

            return callback(*args, **kwargs)
        return wrapped
    return wrapper


def _raise(ex):
    """Method to raise an exception in a context where the normal `raise` context cant be used"""
    raise ex
def _none(*args, empty_array=False):
    return all(x in [None, MISSING] + [[], [[]]][empty_array is True] for x in args)
def _or(*args, default=None):
    for i, _ in enumerate(args):
        if not _none(args[i]):
            return args[i]
    return default
def _default(default, *args, empty_array=True):
    if _none(*args, empty_array=empty_array):
        return default
    if len(args) == 1:
        return args[0]
    return args
def try_get(value, index, default):
    try:
        return value[index]
    except (IndexError, TypeError):
        return default

def setattribute(object, attribute, value):
    setattr(object, attribute, value)
    return object

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
    :class:`Any`
        The found element
    

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

def get(l: list, elem: Any = True, mapping = lambda x: True, default: Any = None, check=lambda x: True):
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
    :class:`Any`
        The found element


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

def iterable(o):
    try:
        iter(o)
        return True
    except TypeError:
        return False

def components_to_dict(components) -> List[dict]:
    """Converts a list of components to a dict that can be used for other extensions
    
    Parameters
    ----------
    components: :class:`list`
        A list of components that should be converted.
        
    Example
    
    .. code-block::

        components_to_dict([Button(...), [LinkButton(...), Button(...)]])

    Raises
    ------
    :class:`Exception`
        Invalid data was passed
    
    Returns
    -------
    List[:class:`dict`]
        The converted data


    """
    wrappers: List[List[Any]] = []
    component_list = []

    if len(components) > 1:
        curWrapper = []
        i = 0   # 
        for component in components:
            # if its a subarray
            if hasattr(component, "items") or isinstance(component, (list, tuple)):
                # if this isnt the first line
                if i > 0 and len(curWrapper) > 0:
                    wrappers.append(curWrapper)
                curWrapper = []
                
                # ActionRow was used
                if hasattr(component, "items"):
                    wrappers.append(component.items)
                # ComponentStore was used
                elif hasattr(component, "_components"):
                    wrappers.append(component._components) 
                else:
                    # just comepletely append the components to all rappers
                    wrappers.append(component)
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
        if isinstance(wrap, list) and not all(hasattr(x, "to_dict") for x in wrap):
            raise Exception("Components with types [" + ', '.join([str(type(x)) for x in wrap]) + "] are missing to_dict() method")
        component_list.append({"type": 1, "components": [x.to_dict() for x in wrap] if iterable(wrap) else [wrap.to_dict()]})
    return component_list

def setup_logger(name):
    """
    Thx redstone ;)
    https://github.com/RedstoneZockt/rotstein-dc-py/blob/main/rotstein_py/logging.py
    """
    level = logging.ERROR

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter(f"%(levelname)s: %(message)s")
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(level)
    
    logger.addHandler(stream_handler)
    return logger