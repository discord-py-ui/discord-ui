from typing import Any

MISSING = None

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
    i = 0
    for x in l: 
        if mapping(x) == elem: 
            return i
        i += 1
    return default

def get(l: list, elem: Any, mapping = lambda x: x, default: Any = None):
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
        if mapping(x) == elem: return x
    return default
