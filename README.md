<br />
<p align="center">
    <h2 align="center">discord-ui</h2>
    <p align="center">
        A discord.py user-interface extension
        <br />
        <a href="https://pypi.org/project/discord-ui/"><b>pip package</b></a>
        ▪ 
        <a href="https://discord-ui.readthedocs.io/en/latest/"><b>read the docs</b></a> 
        ▪ 
        <a href="https://github.com/discord-py-ui/discord-ui/tree/main/examples"><b>examples</b></a>
    </p>
</p>

[![Downloads](https://pepy.tech/badge/discord-ui)](https://pepy.tech/project/discord-ui)

## Introduction

This is a [discord.py](https://github.com/Rapptz/discord.py) ui extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt)
for using discord's newest ui features like buttons, slash commands and context commands (we got dpy2 supported if you want to keep using our libary)

## Installation

```cmd
# windows
py -m install discord-ui

# linux
python3 -m pip install discord-ui
```

## Docs

You can read the docs [here](https://discord-ui.rtfd.io/)

> The docs can include some typos or issues, if so, plz let me know

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

@ui.slash.command("hello_world", options=[SlashOption(bool, "cool", "whether this libary is cool", required=False)], guild_ids=["785567635802816595"])
async def command(ctx, cool=True):
    """This is a simple slash command"""
    # you can use docstrings for the slash command description too
    await ctx.respond("You said this libary is " + str(cool))

await client.run("your_token")
```

Example for creating a user-context command
```py
import discord
from discord.ext import commands
from discurd_ui import UI

client = commands.Bot(" ")
ui = UI(client)

@ui.slash.user_command("avatar", guild_ids=["785567635802816595"])
async def avatar(ctx, user: discord.Member):
    """Sends the avatar of a user"""
    await ctx.respond(embed=discord.Embed(description=user.display_name).set_image(url=user.avatar_url))
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
            [Button("custom_id", "press me", color="green"), LinkButton("https://discord.com", emoji="😁")],
            Button("my_custom_id")
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
        msg = await message.channel.send("you", components=[SelectMenu("custom_id", options=[
            SelectOption("my_value", label="test", description="this is a test"),
            SelectOption("my_other_value", emoji="🤗", description="this is a test too")
        ], max_values=2)])
        try:
            sel = await msg.wait_for("select", client, by=message.author, timeout=20)
            await sel.respond("you selected `" + str([x.content for x in sel.selected_values]) + "`")
        except TimeoutError:
            await msg.delete()

client.run("your_token_here")
```

Example for cogs
```py
from discord.ext import commands
from discord_ui import UI
from discord_ui.cogs import slash_cog, subslash_cog, listening_component_cog

bot = commands.Bot(" ")
ui = UI(bot)

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @slash_cog(name="example", guild_ids=[785567635802816595])
    async def example(self, ctx):
        await ctx.respond("gotchu")

    @subslash_cog(base_names="example", name="command"):
    async def example_command(sef, ctx):
        await ctx.respond("okayy")
    
bot.add_cog(Example(bot))
bot.run("your token")
```

You can find more (and better) examples [here](https://github.com/discord-py-ui/discord-ui/tree/main/examples)

# Changelog

-   <details>
    <summary>4.1.1</summary>

    ## **Fixed**
    - Interaction.author.voice
    > For some reason the voice property of the creator or the interaction would be set

    - Global slashcommands
    > They wouldn't be registered to the api

    - Subcommands editing
    * not fixed yet
    > subcommand checks were wrong and this would result in errors like `In options.0.options.2: Option name 'name' is already used in these options`

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
    > You can now use cog decorators like `slash_cog`, `subslash_cog` and `listening_component_cog`

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

    - LinkButton
    > There was an issue with setting the url not being set

    - SlashCommands
    > There was an issue with creating commands that don't already exist

    ## **Changed**
    - SelectedMenu
    > `.values` is not `.selected_values`

    ## **Added**
    - Interaction
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
    The standart webhook function is also overriden with the new component function

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
    
    ### **Added**
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

    ### **Fixed**
    - Docs fixed

    </details>

-   <details>
    <summary>1.2.1</summary>

    ### **Fixed**
    - Small code fixes

    </details>

-   <details>
    <summary>1.2.0</summary>

    ### **Added**
    - Complete message component suppport
    - Select menus
    - [documentation](https://discord-ui.readthedocs.io/en/latest/)
    
    </details>

-   <details>
    <summary>1.1.2</summary>

    ### **Fixed**
    - Small code fixes

    </details>

-   <details>
    <summary>1.1.1</summary>

    ### **Added**
    - Message.edit()
        > You can now edit messages with button support

    </details>


-   <details>
    <summary>1.1.0</summary>

    ### **Changed**
    - Major changes to request code, now using the client's request
    - `ResponseMessage.acknowledge()` -> `ResponseMessage.defer()`
        > Changed the name of the function + changed `ResponseMessage.acknowledged` -> `ResponseMessage.deferred`
    - `ResponseMessage.defer()` => `await ResponseMessage.defer()`
        > `defer` (`acknowledge`) is now async and needs to be awaited

    ### **Added**
    - hidden responses
        > You can now send responses only visible to the user
    

    ### **Fixed**
    - `ResponseMessage.respond()`
        > Now doesn't show a failed interaction
 

    </details>

-   <details>
    <summary>1.0.5</summary>
    
    ### **Fixed**
    - `ResponseMessage.respond()`
        > responding now doesn't fail after sending the message, it will now defer the interaction by it self if not already deferred and then send the message

-   <details>
    <summary>1.0.4</summary>
    
    ### **Added**
    - `ResponseMessage.acknowledged`
        > Whether the message was acknowledged with the `ResponseMessage.acknowledged()` function

    ### **Changed**

    - `ResponseMessage.respond()` => `await ResponseMessage.respond()`
        > respond() function is now async and needs to be awaited

    - `ResponseMessage.respond() -> None` => `ResponseMessage.respond() -> Message or None`
        > respond() now returns the sent message or None if ninja_mode is true 

    </details>

-   <details>
    <summary>1.0.3</summary>

    ### **Added**
    - `Button.hash`
        > Buttons have now a custom hash property, generated by the discord api 
    
    </details>


## Contact

You can contact us on discord

- `RedstoneZockt#2510`
- `! ♥UwU kuso-kun UwU 💕#6969`
- [a shitty support server](https://discord.gg/bDJCGD994p)
