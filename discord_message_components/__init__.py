from .client import Components, Slash
from .components import ActionRow, Button, LinkButton, SelectMenu, SelectOption, Colors
from .slash.types import OptionTypes, SlashPermission, SlashOption
from .receive import ResponseMessage, Message, PressedButton, SelectedMenu, SlashedCommand, SlashedSubCommand

class Extension():
    """The main extension for the package to use slash commands and message components
        
        Parameters
        ----------
            client: :class:`discord.ext.commands.Bot`
                The discord bot client

            slash_settings: :class:`dict`, optional
                Settings for the slash command part; Default `{resolve_options: False, delete_unused: False, wait_sync: 1}`
                
                ``resolve_options``: :class:`bool`, optional
                    Whether the received options should be read by the received slash command data. If ``False``, the data will be fetched by the id; Default ``False``

                    .. warning::

                        The resolved data will miss some attributes  

                ``delete_unused``: :class:`bool`, optional
                    Whether the commands that are not registered by this slash extension should be deleted in the api; Default ``False``
        
                ``wait_sync``: :class:`float`, optional
                    How many seconds will be waited until the commands are going to be synchronized; Default ``1``


    """
    def __init__(self, client, slash_settings = {"resolve_options": False, "delete_unused": False, "wait_sync": 1}) -> None:
        self.components = Components(client)
        """For using message components
        
        :type: :class:`~Components`
        """
        self.slash = Slash(client, **slash_settings)
        """For using slash commands
        
        :type: :class:`~Slash`
        """

__version__ = "2.0.0"
