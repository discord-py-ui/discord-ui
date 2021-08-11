from typing import Any, List

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
        if mapping(x) == elem: 
            return x
    return default

def component_dict_list(*components):
    """Converts a list of components to a dict that can be used for other extensions etc
    
    Parameters
    ----------
    components: :class:`*args` | :class:`list`
        A list of components that should be converted.
        
        Example
        
        .. code-block::

            # List of components with component rows (everything in [] defines that it will be in it's own component row)
            component_dict_list(Button(...), [Button(...), Button(...)], SelectMenu(...), LinkButton)
            # or
            component_dict_list([Button(...), [LinkButton(...), Button(...)]])

    Raises
    ------
        :raises: :class:`Exception` : Invalid Data was passed
    Returns
    -------
        :returns: The converted data
        :type: :class:`dict`
    
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
        if all(hasattr(x, "to_dict") for x in wrap):
            raise Exception("Components with types " + [str(type(x)) for x in wrap] + "are missing to_dict() method")
        component_list.append({"type": 1, "components": [x.to_dict() for x in wrap]})
    return component_list
