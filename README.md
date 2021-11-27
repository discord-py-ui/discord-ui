<br />
<p align="center">
    <h2 align="center">discord-ui</h2>
    <p align="center">
        A discord.py extension for using discord ui/interaction features
        <br />
        <a href="https://pypi.org/project/discord-ui/"><b>pip package</b></a>
        ▪ 
        <a href="https://discord-ui.readthedocs.io/en/latest/"><b>read the docs</b></a> 
        ▪ 
        <a href="https://github.com/discord-py-ui/discord-ui/tree/main/examples"><b>examples</b></a>
    </p>
</p>

[![Downloads](https://pepy.tech/badge/discord-ui)](https://pepy.tech/project/discord-ui)
![PyPI](https://img.shields.io/pypi/v/discord-ui)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/discord-ui)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/550953d11c8242b9b7944642a2e292c7)](https://app.codacy.com/gh/discord-py-ui/discord-ui?utm_source=github.com&utm_medium=referral&utm_content=discord-py-ui/discord-ui&utm_campaign=Badge_Grade_Settings)


## Introduction


This is a [discord.py](https://github.com/Rapptz/discord.py) ui extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt)
for using discord's newest ui features like buttons, slash commands and context commands.

[Documentation](https://discord-ui.readthedocs.io/en/latest/)

## Installation


### Windows
```cmd
py -m pip install discord-ui
```

### Linux
```bash
python3 -m pip install discord-ui
```

## License

This project is under MIT License

## Issues

If you find any issues, please report them 

https://github.com/discord-py-ui/discord-ui/issues

## Note

If you want to use slash commands, in the oauth2 invite link generation, 
you have to check both `bot` and `application.commands` fields

![](./docs/source/images/slash/invite_scope.png)

## Example

Example for creating a simple slash command
```py
import discord
from discord.ext import commands
from discord_ui import UI, SlashOption

client = commands.Bot(" ")
ui = UI(client)

@ui.slash.command("hello_world", options=[SlashOption(bool, "cool", "whether this libary is cool", required=False)], guild_ids=[785567635802816595])
async def command(ctx, cool=True):
    """This is a simple slash command"""
    # you can use docstrings for the slash command description too
    await ctx.respond("You said this libary is " + str(cool))

client.run("your_token")
```

Example for creating a user-context command
```py
import discord
from discord.ext import commands
from discurd_ui import UI

client = commands.Bot(" ")
ui = UI(client)

@ui.slash.user_command("avatar", guild_ids=[785567635802816595])
async def avatar(ctx, user: discord.Member):
    """Sends the avatar of a user"""
    await ctx.respond(embed=discord.Embed(description=user.display_name).set_image(url=user.avatar_url))

client.run("your_token")
```

Example for autocompletion of choices

```py
import discord
from discord_ui import UI, SlashOption, AutocompleteInteraction

async def generator(ctx: AutocompleteInteraction):
    available_choices = ["hmm", "this", "is", "a", "an", "test", "testing"]
    return [(x, x) for x in available_choices if x.startswith(ctx.value_query)]

@ui.slash.command("search_word", options=[SlashOption(str, "query", choice_generator=generator)])
async def search_word(ctx, query):
    await ctx.send("got " + query + " for query")

client.run("your_token")
```

Example for sending a button and receiving it

```py
import discord
from discord.ext import commands
from discord_ui import UI, LinkButton, Button

from asyncio import TimeoutError

client = commands.Bot(" ")
ui = UI(client)

@client.listen("on_message")
async def on_message(message: discord.Message):
    if message.content == "!btn":
        msg = await message.channel.send("you", components=[
            [Button("press me", color="green"), LinkButton("https://discord.com", emoji="😁")],
            Button(custom_id="my_custom_id")
        ])
        try:
            btn = await msg.wait_for("button", client, by=message.author, timeout=20)
            await btn.respond("you pressed `" + btn.content + "`")
        except TimeoutError:
            await msg.delete()

client.run("your_token_here")
```

Example for sending Selectmenus and receiving them

```py
import discord
from discord.ext import commands
from discord_ui import UI, SelectMenu, SelectOption

from asyncio import TimeoutError

client = commands.Bot(" ")
ui = UI(client)

@client.listen("on_message")
async def on_message(message: discord.Message):
    if message.content == "!sel":
        msg = await message.channel.send("you", components=[SelectMenu(options=[
            SelectOption("my_value", label="test", description="this is a test"),
            SelectOption("my_other_value", emoji="🤗", description="this is a test too")
        ], "custom_id", max_values=2)])
        try:
            sel = await msg.wait_for("select", client, by=message.author, timeout=20)
            await sel.respond("you selected `" + str([x.content for x in sel.selected_options]) + "`")
        except TimeoutError:
            await msg.delete()

client.run("your_token_here")
```

Example for cogs
```py
from discord.ext import commands
from discord_ui import UI
from discord_ui.cogs import slash_command, subslash_command, listening_component

bot = commands.Bot(" ")
ui = UI(bot)

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @slash_command(name="example", guild_ids=[785567635802816595])
    async def example(self, ctx):
        await ctx.respond("gotchu")

    @subslash_command(base_names="example", name="command"):
    async def example_command(self, ctx):
        await ctx.respond("okayy")
    
bot.add_cog(Example(bot))
bot.run("your token")
```

You can find more (and better) examples [here](https://github.com/discord-py-ui/discord-ui/tree/main/examples)



## Contact

You can contact us on discord

- [**Redstone**](https://discord.com/users/355333222596476930)
- [**kuso**](https://discord.com/users/539459006847254542)
- [**discord server**](https://discord.gg/bDJCGD994p)


# Changelog

-   <details>
    <summary>5.1.0</summary>
    
    ## **Breaking changes**
    - Component custom ids are now optional, if no custom id is passed, a 100 characters long random string will be used and because of that the order of Component init params changed
    - The order of SelectMenus init params changed, `custom_id` comes now after `options`
    ```py
    SelectMenu("my_custom_id", [options...here])
    # is now
    SelectMenu([options...here], "my_custom_id")
    ```
    - Same for Buttons
    ```py
    Button("my_custom_id", "label")
    # is now
    Button("label", "my_custom_id")
    ```
    - ButtonStyles is now ButtonStyle
    - renamed cog decorators, the old ones still work but they will show a deprecation warning: `slash_command` -> `slash_command`, `subslash_command` -> `subslash_command`, `context_cog` -> `context_command`, `listening_component` -> `listening_component`
    - Removed `Slash.edit_command` and `Slash.edit_subcommand`, "moved" to `Command.edit`
    - `SlashedCommand` is now `SlashInteraction`, `SlashedSubCommand` is now `SubSlashInteraction` and `SlashedContext` is now `ContextInteraction`
    - The command attributes of CommandInteractions (SlashedCommand, ...) are now moved to `Interaction.command.` (the `.command` attribute is a reference to the real command, if you change properties of the command they will be updated)
    - The component attributes of an interaction are now moved to `.component`
    - ContextCommands `.param` attribute is now `.target`

    ## **Changed**
    - `argument_type` in SlashOption is now `type`
    - `ButtonStyle` value names changed: color names are now capitalized and `Danger` is now `Destructive`
    - `Listener.target_user` is now `Listener.target_users` and can take users, members and ids as the value
    - `BaseCommand.options` and `SlashOption.options` is now of type `SlashOptionCollection`, which allows you to acces options by index and name
    ```py
    my_command.options["option name"]
    # or
    my_command.options[0]
    ```
    You can also use some methods like `.get`, `.set` (which will return itself after it set something, so `SlashOption.set(key, value).set(key, value)` would work) and ``SlashOption.options + SlashOption.option`` will add both SlashOptions together
    - If an invalid guild id was passed to a slashcommand, no exception will be raised anymore, it will just be printed into the console and ignored `logging.error()`
    - Moved the `discord_ui.ext.py` module into a folder
    - `on_button_press` and `on_menu_select` is now `on_button` and `on_select`. The old event names will still work but will be removed in the next release

    ## **Fixed**
    - disable_action_row
    - `ActionRow.disable`
    - no interaction events being dispatched because subclasses of dpy2 `commands.Bot` instances wouldn't get overriden which lead to not enabling needed debug events
    - when no matching component listener in `Listener` could be found, the events for components events wouldn't be dispatched
    - `delete_after` keyword in message send override not working
    - mentionable type in slashoptions not being parsed to objects
    - `@discord.ext.commands.Cooldown` not working on cog slashcommands

    ## **Added**
    - `**fields` to all functions that edit the message components (like `.disable_components`, `.disable_component`, ...). The `**fields` parameter can be used to edit other properties of the message without using `.edit` again and send a "useless" request
    - `@Lister.on_error` and `@Listener.wrong_user` decorators for handling Exceptions in Listeners
    - When no keyword was passed to `@Listener.button` or `@Listener.select`, the function will be called on every button/slect
    - `channel_type` to SlashOption, list of `discord.ChannelType`. This will restrict the shown channels for channel slash options to this list.
    - support for nextcord. Other libs **should** work too, but they are not tested. 
    - `Mentionable` type for SlashOptions
    - description for short slashoptions. If you set the options for a slash command via callback params, you can add a description (and a type) to them with your docstring. There are 3 different styles you can use:
    ```py
    # style 1
    @ui.slash.command()
    async def my_command(ctx, my_option, my_other_option):
        """This is my command description

        my_option: `int`:
            This is the description for the my_option parameter
        my_other_option: `str`:
            This is the description for another option
        """
        ...
    
    # style 2
    @ui.slash.command()
    async def my_command(ctx, my_option: int, my_other_option: str):
        """This is my command description

        my_option: This is the description for the my_option parameter
        my_other_option: This is the description for another option
        """
        ...

    # style 3
    @ui.slash.command()
    async def my_command(ctx, my_option, my_other_option: str):
        """This is my command description


        `int`: This is the description for the my_option parameter

        This is the description for another option
        """
        ...
    ```
    Note: You don't have to use `` `type` ``, you can just use `type`
    - Empty descriptions for slashcommands and slashoptions. The default description value is now `\u200b` which is an "empty" char
    - Modifying slashcommand options is now WWAAYYYY easier. You can just do `.options[name or index].name = "new name"` and the option will be updated
    - You can set the autocomplete choice generator with a decorator now
    ```py
    ui.slash.command(options=[SlashOption(str, "my_option")])
    async def my_command(ctx, my_option):
        ...


    @my_command.options["my_option"].autocomplete_function
    async def my_generator(ctx):
        ...
    # or
    @my_command.options[0].autocomplete_function
    async def my_generator(ctx):
        ...
    ```
    - All apllication command decorators will now return the created Command
    ```py
    @ui.slash.command(...)
    async my_command(ctx):
        ...
    type(my_command) # SlashCommand
    ```
    - Added edit and delete method to slashcommand. You can use this for editing or deleting the command later
    ```py
    # edit
    await my_command.edit(name="test")
    # delete
    await my_command.delete()
    ```
    - `id` to SlashCommand
    - `commands_synced` event which will be dispatched when all commands where synced with the api (`UI.Slash.sync_commands`)
    - `BaseCommmand.update` method which updates the api command with the lcoal changes
    - `SlashSubCommand.base`, which will be shared among all subslashcommands with the same base


    ## **Removed**
    - `discord.ext.commands.Bot` override for enabling the debug event, this will be enabled when creating a UI instance from the bot

    </details>

-   <details>
    <summary>5.0.1</summary>

    ## **Fixed**
    - Choices not working

    </details>

-   <details>
    <summary>5.0.0</summary>

    ## **Fixed**
    - Roles not being parsed correctly

    ## **Changed**
    - default_permission
    > default_permission can now be of type `discord.Permissions` but the api doesn't support that yet.
    - slash http
    > some code changes to slash-http features

    ## **Added**
    - ChoiceGeneratorContext
    > Context class for choice generation
    - SlashOption
    > `choice_generator` keyword and `autocomplete` keyword. 
    > `autocomplete` is not needed if you pass choice_generator
    - File sending
    > You are now able to send hidden files

    </details>

-   <details>
    <summary>4.3.8</summary>
    
    ## **Fixed**
    - Issue with SlashOptions
    > required is now false by default again
    
    </details>

-   <details>
    <summary>4.3.7</summary>

    ## **Changed**
    - SlashOption
    > Required is now ``True`` by default

    ## **Fixed**
    - `AttributeError: 'LinkButton' object has no attribute 'component_type'`

    ## **Removed**
    - decompressing
    > The lib now doesn't decompress byte data anymore, which means everything before the dpy commit `848d752` doesn't work with this lib.
    >
    > [message reference](https://discord.com/channels/336642139381301249/381965829857738772/879980113742143548) in discordpy discord server

    </details>

-   <details>
    <summary>4.3.6</summary>

    ## **Fixed**
    - Slashcommand comparing
    - Ephemeralmessage keyerror exception


    </details>

-   <details>
    <summary>4.3.5</summary>

    ## **Fixed**
    - send function issues

    </details>

-   <details>
    <summary>4.3.4</summary>

    ## Fixed
    - SlashOption not accepting tuple

    </details>

-   <details>
    <summary>4.3.3</summary>

    ## **Fixed**
    - fixed `TypeError: 'NoneType' object is not iterable`

    </details>

-   <details>
    <summary>4.3.2</summary>

    ## **Fixed**
    - `Could not find a matching option type for parameter '<class 'NoneType'>'`

    </details>

-   <details>
    <summary>4.3.1</summary>

    ## **Removed**
    - unused parameter

    </details>

-   <details>
    <summary>4.3.0</summary>

    ## **Fixed**
    - `Message.wait_for`
    > by keyword doesn't work properly

    ## **Removed**
    - Hash
    > Removed the hash property from Buttons and SelectMenus due to the removal of it from the api
    
    ## **Added**
    - `discord_ui.ext`
    > A module with useful tools and decorators to use [more information](https://discord-ui.readthedocs.io/en/latest/ext.html)
    
    - BaseCommand
    > BaseCommand (the superclass for all applicationcommands) has now some extra properties:
        
        - is_chat_input
        > Whether this command is a slash command
        
        - is_message_context
        > Whether this command is a message context command
        
        - is_user_context
        > Whether this command is a user context command
    
    - SlashedCommand
    > Added properties:
        
        - is_alias
        > Whether the invoked command is an alias or not
        
        - aliases
        > All the available aliases for the command
    
    - Listeners
    > Listeners are something that you can use for a better processing of received components.
    > You could see them as a cog to the message components
    > [more information](https://discord-ui.readthedocs.io/en/latest/listeners.html)

    ## **Changed**
    - SelectInteraction
    > `SelectInteraction.selected_values` are not the raw values that were selected, `SelectMenu.selected_options` are the options of type `SlashOption` that were selected
    - MISSING => None
    > All instance values that were `MISSING` by default are now `None`



    </details>

-   <details>
    <summary>4.2.15</summary>

    # Fixed
    - #97

    </details>

-   <details>
    <summary>4.2.14</summary>

    ## **Fixed**
    - small SelectOption issues
    - context commands

    ## **Changed**
    - allow context commands to have names with spaces

    </details>

-   <details>
    <summary>4.2.13</summary>

    ## **Fixed**
    - `TypeError: 'EMPTY' is not a callable object` in context commands

    </details>

-   <details>
    <summary>4.2.12</summary>

    ## **Fixed**
    - context commands

    </details>

-   <details>
    <summary>4.2.11</summary>

    ## **Fixed**
    - cog context commands returned wrong type

    </details>

-   <details>
    <summary>4.2.10</summary>

    ## **Fixed**
    - cog context commands typo with `guild_permission` keyword

    </details>

-   <details>
    <summary>4.2.8</summary>
    
    ## **Added**

    - edit_subcomand

    ## **Fixed**

    - print statements

    ## **Fixed**

    - #94 (again 💀)
    - received subcommands
    > The base_names and the name will be now set to the right value

    </details>

-   <details>
    <summary>4.2.7</summary>

    ## **Added**
    - `on_component`
    > There is now an event with the name `component` that will be dispatched whenever a component was received
    > If you use `Message.wait_for`, there is now a new event choice with the name `component` (`message.wait_for("component", client)`)

    ## **Fixed**
    - #94
    > DM issue with deleting messages

    ## **Changed**
    - `edit`
    > Edit now takes "content" as not positional (`.edit("the content")` works now)
    - component lenght
    > You are now able to set component values with the right max lenght

    </details>

-   <details>
    <summary>4.2.6</summary>

    ## **Fixed**

    - emebds
    > there was an issue with sending embeds

    </details>

-   <details>
    <summary>4.2.5</summary>

    ## **Fixed**

    - listening_components
    > There was an issue with listening components that they needed two parameters but only one was passed
    > Another issue was `TypeError: __init__() missing 1 required positional argument: 'custom_id'`?

    - emebds
    > there was an issue with sending embeds

    </details>

-   <details>
    <summary>4.2.2</summary>

    ## **Changed**

    - sync_commands
    > the `delete_unused` keyword is now optional, if you don't pass a parameter, `slash.delete_unused` will be used (from the `__init__` function)

    </details>

-   <details>
    <summary>4.2.1</summary>

    ## **Fixed**
    
    - `cannot import name 'InteractionResponseType' from 'discord.enums'`

    </details>

-   <details>
    <summary>4.2.0</summary>

    ## **Added**

    - cog_remove sync
    > when you remove a cog the slash commands will now get deleted if you set `delete_unused` to True and set `sync_on_cog` to True
    - alternativ slash options
    > you don't have to specify options in one of the slash decorators anymore. Instead, you can set them in your callback function
    > Example
    ```py
    @ui.slash.command()
    async def greet(ctx, user):                         # This will add an required option with the name "user" of type "user"
        """Greets a user
        
        You can use multiline docstrings, because only the first line will be used for the description
        """
        ...
    
    @ui.slash.command()
    async def tag(ctx, target: discord.User = None):    # This will add an optional option with the name "target" of type "user"
                                                        # Note: you could also use target: "user" = None or anything else you would use in SlashOption for the type
        ...

    ```

    ## **Fixed**

    - sync_commands
    > if you would sync the commands after the first sync, it threw an error

    </details>

-   <details>
    <summary>4.1.4</summary>

    ## **Fixed**

    - slashcommands in forbidden guilds
    > when trying to get slash commands in a guild with no `appication.commands` permission, it won't throw an exepction anymore

    </details>

-   <details>
    <summary>4.1.2</summary>

    ## **Fixed**

    - Subcommands editing
    > subcommand checks were wrong and this would result in errors like `In options.0.options.2: Option name 'name' is already used in these options`

    </details>

-   <details>
    <summary>4.1.1</summary>

    ## **Fixed**

    - Interaction.author.voice
    > For some reason the voice property of the creator or the interaction would be set

    - Global slashcommands
    > They wouldn't be registered to the api

    </details>

-   <details>
    <summary>4.1.0</summary>

    ## **Added**

    - py 3.6 < support
    > You should be able to use this package with python 3.6 or newer

    ## **Fixed**

    - print
    > Forgot to remove print statements💀

    </details>

-   <details>
    <summary>4.0.4</summary>

    ## **Fixed**

    - slashcommand
    > when a user was passed in an option, its guild was always None
    - context commands
    > if no name passed, the context command wouldn't take the callback name as the name of the command

    </details>

-   <details>
    <summary>4.0.3</summary>

    ## **Fixed**

    - Message.wait_for

    </details>

-   <details>
    <summary>4.0.2</summary>

    ## **Fixed**

    - Issue with receiving context commands

    </details>

-   <details>
    <summary>4.0.1</summary>
    
    ## **Fixed**

    - discord.ext import error

    </details>

-   <details>
    <summary>4.0.0</summary>

    ## **Added**

    **You now have much more control over your slash commands!**
    - Permissions
    > You can update your permissions with the `Slash.update_permissions` function
    - Creating commands
    > You can now create slash commands without the decorator in a much more eaisier way! Check out the `Slash.add_command` function
    - Edit commands
    > You can edit commands in code with the `Slash.edit_command` function

    - Listening components
    > You can add and remove listening components now with the `Components.add_listening_component`, `Components.remove_listening_component` and `Components.remove_listening_components` functions

    - Cogs
    > You can now use cog decorators like `slash_command`, `subslash_command` and `listening_component`

    ## **Fixed**

    - SlashCommand
    > Slash commands wouldn't be updated if only `default_permission` was changed

    ## **Changed**

    - wait_for
    > Message.wait_for now takes `by` and `check` as parameters and `event_name` and `client` switched place (`wait_for(client, "event_name")` is now `wait_for("event_name", client)`)
    - listening components
    > You can specify listening_components now more presicely, you can add messages, users, and a check to filter
    - Interaction.member
    > `Interaction.member` is now `Interaction.author`
    - listening comonents
    > Listening component callback functions now only take one parameter, the used component
    - `on_button_press` and `on_menu_select`
    > These events now take a sole parameter, the used component. If you want to acces to message, use `passed_component.message`

    ## **Removed**

    - ResponseMessage
    > Removed ResponseMessage
    </details>

-   <details>
    <summary>3.3.5</summary>
    
    ## **Fixed**

    - SelectMenu
    > SelectMenu issue when creating it from data

    </details>

-   <details>
    <summary>3.3.4</summary>

    ## **Changed**

    - edit
    > `Message.edit` now takes a `embed` parameter

    ## **Fixed**

    - print
    > Forgot to remove some `print` statements 

    </details>

-   <details>
    <summary>3.3.3</summary>

    ## **Added**

    - class representation
    > classes have now a `__repr__` function
    - UI(override_dpy)
    > You can now choose whether you want to override some of dpy objects and functions (default is True) (see [the override module](https://github.com/discord-py-ui/discord-ui/blob/main/discord_ui/override.py) for more information)
    > This also appeals to the `Components` class (Components(override_dpy))
    > note: if you don't want to create a `UI` object, you can instead override dpy with the `override_dpy` method
    ```py
    from discord_ui import override_dpy

    override_dpy()
    ```

    ## **Fixed**

    - dpy2
    > discord.py v2 now auto-decompresses socket data and passes a string instead of the uncompressed data.
    - override dpy message
    > when overriding dpy message object, the components would mix

    </details>

-   <details>
    <summary>3.3.2</summary>

    ## **Added**

    - EphemeralResponseMessage
    > You can now edit a ephemeral message which was created from an interaction (ex. when a button in a hidden message was pressed)

    </details>

-   <details>
    <summary>3.3.1</summary>

    ## **Added**

    - interaction
    > `Interaction.channel` and `Interaction.guild`

    </details>

-   <details>
    <summary>3.3.0</summary>

    ## **Fixed**

    - interaction usage in dms

    </details>

-   <details>
    <summary>3.2.9</summary>
    
    ## **Added**

    - ratelimit fix
    > The lib will now retry after the ratelimit reset and doesn't throw an HTTPException anymore

    ## **Fixed**

    - sync_commands
    > Got `KeyError` exception while syncing commands

    </details>

-   <details>
    <summary>3.2.8</summary>

    ## **Fixed**

    - hidden responding
    > When a hidden response was about to be send without defering the interaction it would thrown an error

    </details>

-   <details>
    <summary>3.2.7</summary>

    ## **Added**

    - warnings
        - When a guild_permission with an invalid guild id is passed, it will throw an exception when syncing the commands
        - When the value of a guild_permission is not of type `SlashPermission` it will throw an exception
    - context-commands
    > You can now have context commands with the same name as a normal slash command
    - slashcommand description
    > You can use docstrings `"""docstring"""` for setting the description of a slash commmand by setting the dosctring for the callback function

    ## **Changed**

    - auto_defer
    > auto_defer is now disabled by default
    - slash sync
    > You can now disable auto_sync for slash commmands and sync them by yourself with `Slash.sync_commands(delete_unused)`
    - Interacion.defer
    > `Interaction._deferred` is not `Interaction.deferred` and `Interaction.defer()` doesn't throw an exception anymore, it will just log the error with `logging.error()`

    ## **Fixed**

    - try
    > There was a try/catch in the `Interaction.respond` function that would allow the code to continue when an exception occured while responding with ninja_mode
    - context commands
    > There was an issue adding context-commands
    - Command checking
    > Now, the libary only edits commands when changes were made 


    </details>

-   <details>
    <summary>3.2.6</summary>

    ## **Added**

    - auto ninja_mode
    > If you use `.respond()`, the function will try to use ninja_mode automatically

    ## **Changed**

    - project
    > Moved git-project to https://github.com/discord-py-ui/discord-ui

    ## **Fixed**

    - ninja_mode response
    > responding with ninja_mode would end up in an exception

    - file sending
    > fixed another file sending issue with slash commands

    </details>

-   <details>
    <summary>3.2.5</summary>

    ## **Fixed**

    - #89 (thanks for reporting)

    </details>

-   <details>
    <summary>3.2.4</summary>

    - Fixed version issues with the package

    </details>

-   <details>
    <summary>3.2.2</summary>

    ## **Fixed**

    - #85: `AttributeError: module 'discord' has no attribute '_Components__version'`

    </details>

-   <details>
    <summary>3.2.0</summary>

    ## **Fixed**

    I'm really sorry for all the issues this libary got, if you still find issues, please report them in https://github.com/discord-py-ui/discord-ui/issues

    - SelectOpion
    > There was an issue with emojis not being set in SelectOptions

    -  LinkButton
    > There was an issue with setting the url not being set

    - SlashCommands
    > There was an issue with creating commands that don't already exist

    ## **Changed**

    - SelectInteraction
    > `.values` is not `.selected_values`

    ## **Added**

    -  Interaction
    > Buttons and SelectMenus have a `.message` property for the message where their interaction was creted
    > ResponseMessages have a `.interaction` property for the received interaction
    
    - Events
    > We added a `interaction_received` event for all interactions that are received

    

    </details>

-   <details>
    <summary>3.1.0</summary>

    ## **Added**

    - discordpy 2 support
    > We added support for discord.py v2, so you can stay loyal to our libary and use it together with discord.py v2!
    
    - Exceptions
    > Added own Exceptions for errors
    
    - ParseMethod
    > You can change the way the extension parses interaction data. You can choose between [different Methods](https://discord-ui.rtfd.io/en/latest/ui.html#id1)
    
    - Auto-defer
    > The libary will autodefer all interactions public. If you want to change that, take a look at [the documentation for this feature](https://discord-ui.rtfd.io/en/latest/ui.html#id2)
    
    - slashcommand edit check
    > Slash commands will only be edited if there were some changes, so you won't get a `invalid interaction` error in discord after starting the bot
    > If only permissions were changed, just the permissions will be edited and not the whole command like before

    ## **Fixed**

    - slash commands
    > I finally fixed the damn slashcommand system, it should work now

    - Parsing
    > The resolving, fetching and pulling from the cache methods should all work

    </details>

-   <details>
    <summary>3.0.1</summary>
    
    ## **Fixed**

    - small project issues

    </details>

-   <details>
    <summary>3.0.0</summary>

    ## **Added**

    - context commands
    > Context commands are now available

    ## **Changed**

    - Project name
    > The project's name was changed from `discord-message-components` to `discord-ui`

    - ``Extension`` is now ``UI``

    </details>

-   <details>
    <summary>2.1.0</summary>

    ## **Added**

    - Webhook support
    > You are now able to use webhooks together with message components, to send a webhook message with the components, use the `Components.send_webhook` function.
    > The standart webhook function is also overriden with the new component function

    - Float type
    > You can now use `float` as the argument type for a slash command option

    - Auto empty names
    > Buttons, LinkButtons and SelectOptions labels are now by default `\u200b`, which is an "empty" char 

    ## **Changed**

    - Code documentation to more be more informative

    ## **Fixed**

    - Fixed small code issues (they were already fixed in previous versions, but I just wanna list this here)

    - Docs are now working

    </details>

-   <details>
    <summary>2.0.2</summary>

    ## **Fixed**

    - SelectOption
    > Select option threw an exception if it was smaller than 1 or higher than 100

    </details>

-   <details>
    <summary>2.0.0</summary>
    
    ## **Added**

    - Slashcomamnd support
        - `Slash` class for slash commands
        - `Slash.command`, `Slash.subcommand` and `Slash.subcommand_groups` are available for creating slash commands
        - `SlashedCommand` and `SlashedSubCommand` are there for used slash commands 
    
    - ``Message``
        - disable_action_row(row_numbers: `int` | `range`, disable: `bool`)
        > disables (enables) component row(s) in the message
        
        - disable_components(disable: `bool`)
        > disables (enables) all componentss
    
    - overrides
        - `Messageable.send` returns Message instead of discord.Message and takes components parameter
        - `override_client` function added
    
    - `interaction.send`, creates followup messages which can be hidden
    
    - `Component.listening_component`
    > A listening component with a callback function that will always be executed whenever a component with the specified custom_id 
    was used


    ## **Changed**
    - Message
        
        - All Message objects don't use the client object anymore
        - Message.wait_for now needs the client as the first parameter

    ## **Fixed**
    - Interaction
    > All interaction responses work now
    - A lot of issues I fogor💀

    </details>

-   <details>
    <summary>1.2.2</summary>

    ## **Fixed**

    - Docs fixed

    </details>

-   <details>
    <summary>1.2.1</summary>

    ## **Fixed**

    - Small code fixes

    </details>

-   <details>
    <summary>1.2.0</summary>

    ## **Added**

    - Complete message component suppport
    - Select menus
    - [documentation](https://discord-ui.readthedocs.io/en/latest/)
    
    </details>

-   <details>
    <summary>1.1.2</summary>

    ## **Fixed**

    - Small code fixes

    </details>

-   <details>
    <summary>1.1.1</summary>

    ## **Added**

    - Message.edit()
        > You can now edit messages with button support

    </details>


-   <details>
    <summary>1.1.0</summary>

    ## **Changed**

    - Major changes to request code, now using the client's request
    - `ResponseMessage.acknowledge()` -> `ResponseMessage.defer()`
        > Changed the name of the function + changed `ResponseMessage.acknowledged` -> `ResponseMessage.deferred`
    - `ResponseMessage.defer()` => `await ResponseMessage.defer()`
        > `defer` (`acknowledge`) is now async and needs to be awaited

    ## **Added**
    
    - hidden responses
        > You can now send responses only visible to the user
    

    ## **Fixed**
    
    - `ResponseMessage.respond()`
        > Now doesn't show a failed interaction
 

    </details>

-   <details>
    <summary>1.0.5</summary>
    
    ## **Fixed**

    - `ResponseMessage.respond()`
        > responding now doesn't fail after sending the message, it will now defer the interaction by it self if not already deferred and then send the message

-   <details>
    <summary>1.0.4</summary>
    
    ## **Added**

    - `ResponseMessage.acknowledged`
        > Whether the message was acknowledged with the `ResponseMessage.acknowledged()` function

    ## **Changed**

    - `ResponseMessage.respond()` => `await ResponseMessage.respond()`
        > respond() function is now async and needs to be awaited

    - `ResponseMessage.respond() -> None` => `ResponseMessage.respond() -> Message or None`
        > respond() now returns the sent message or None if ninja_mode is true 

    </details>

-   <details>
    <summary>1.0.3</summary>

    ## **Added**

    - `Button.hash`
        > Buttons have now a custom hash property, generated by the discord api 
    
    </details>
