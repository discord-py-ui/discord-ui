# from .receive import Interaction
# from .components import Button, Component
# from .cogs import ListeningComponent
# from .tools import MISSING

# from typing import List
# from inspect import getmembers

# .send(..., component_list=ComponentList(client))


# class _ListeningComp():
#     pass

# class ListeningButton(ListeningComponent, Button):
#     def __init__(self, callback, custom_id, label="\u200b", color="blurple", emoji=MISSING, new_line=False, disabled=False) -> None:
#         # for instance checking
#         _ListeningComp.__init__()
#         ListeningComponent.__init__(self, callback, component_type="button")
#         Button.__init__(self, custom_id, label, color, emoji, new_line, disabled)

# def button(custom_id, *, label="\u200b", color="blurple", emoji=MISSING, new_line=False, disabled=False):
#     def wraper(callback):
#         return ListeningButton(callback, custom_id, label, color, emoji, new_line, disabled)
#     return wraper

# class ComponentList():
#     def __init__(self, client):
#         self.bot = client
#         self.components: List[Component] = []

#     def callback(self, ctx: Interaction):
#         """The callback for any component that was recieved"""
#         pass

#     def add_component(self, component):
#         self.components.append(component)
#     def remove_component(self, component):
#         self.components.remove(component)
#     def get_components(self):
#         return getmembers(self, predicate=lambda x: isinstance(x[1], _ListeningComp))