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
        <a href="https://github.com/KusoRedsto/discord-ui/tree/main/examples"><b>examples</b></a>
    </p>
</p>

## Introduction

This is a [discord.py](https://github.com/Rapptz/discord.py) ui extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt)
for using discord's newest ui features like buttons, slash commands and context commands (we got dpy2 supported if you want to keep using our libary)

Our libary overrides some of the functions in dpy, so this lib is easier to use.
The `Messageable.send` function and the `Webhook.send` are 
both overriden with our own custom method. 
`discord.ext.commands.Bot` is overriden too, but only if you use dpy 2
in order for our lib to work, so if you (somewhy) wanna check the type of the client, you need to 
use `isinstance(your_client, discord.ext.commands.Bot)`, because `type(your_client)` will be of type `OverridenV2Bot`

For more information about overriding, take a look at the [override module](https://github.com/KusoRedsto/discord-ui/blob/main/discord_ui/override.py)



## Installation

```cmd
# windows
py -m install discord-ui

# linux
python3 -m pip install discord-ui
```

## Docs

You can read the docs [here](https://discord-ui.readthedocs.io/)

> The docs can include some typos or issues, if so, plz let me know

## License

This project is under MIT License

## Note

If you want to use slash commands, in the oauth2 invite link generation, 
you have to check both `bot` and `application.commands` fields

![](./docs/source/images/slash/invite_scope.png)

## Example

This is an example with a slash command, that can create a link button with parameters, a function that will automatically respond to every button and menu with the value they pressed and a command that will send a button example 

```py
import discord
from discord.ext import commands
from discord_ui import *

client = commands.Bot(" ")
ui = UI(client)

@ui.slash.subcommand_group(base_names=["generate", "link"], name="button", description="sends a button and a linkbutton", options=[
        SlashOption(str, "message content", "the content of the message"), 
        SlashOption(str, "name", "the name of the button"), 
        SlashOption(str, "link", "the link for the button"), 
        SlashOption(str, "emoji", "a emoji appearing before the text")
    ], guild_ids=["785567635802816595"])
async def command(ctx, message_content="cool, right?", name="click me", link="https://github.com/KusoRedsto/discord-ui", emoji=None):
    if not link.startswith("http://") and not link.startswith("https://"):
        return await ctx.respond("The link has to start with `http://` or `https://`", hidden=True)        
    await ctx.respond(content=message_content, components=[LinkButton(link, label=name, emoji=emoji)])

@client.listen("on_ready")
async def on_ready():
    print("ready")

@client.listen("on_message"):
async def on_message(message: Message):
    if message.content = "!test":
        await message.channel.send("hello", components=[
                [Button("custom", "hello"), Button("custom_2", "world", "green")]
                Button("custom", "yeahhh", "red")
            ])

@client.listen('on_button_press')
async def on_button(btn: PressedButton, msg: ResponseMessage):
    await msg.respond(btn.member.mention + ", you pressed on " + btn.content + " with the custom id of " + btn.custom_id)
@client.listen('on_menu_select')
async def on_select(menu: SelectedMenu, msg: ResponseMessage):
    await msg.respond(menu.member.mention + ", you selected " + ', '.join([x.content for x in menu.values]) + " on the menu with the custom id " + menu.custom_id)

client.run(token)
```

You can find more (and better) examples [here](https://github.com/KusoRedsto/discord-ui/tree/main/examples)

# Changelog

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
