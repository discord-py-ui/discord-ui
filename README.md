https://pypi.org/project/discord-message-components/


## Introduction

This is a [discord.py](https://github.com/Rapptz/discord.py) message component extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt), which you can use until discord.py v2.0 is out

We also added override support for the `discord.ext.commands.Bot` client, so you don't have to initialize everything on your own

To override the standart Bot client, add the following to your code

```py
from discord.ext import commands
from discord_message_components import override_client
override_client()

client = commands.Bot(...)
```
This will add `.components` and `.slash` to the client, and you don't need the 
`extension = Extension(client)` thing anymore

And the standart `TextChannel.send` function is automatically overridden 

> We got some features for you like **send buttons**, **send select menus**, **receive a press or selection** and **edit messages** with buttons and selection menus and everything is compatible with discord.py


## Installation

```cmd
# windows
py -m install discord-message-components

# linux
python3 -m pip install discord-message-components
```

## Docs

You can read the docs [here](https://discord-message-components.readthedocs.io/)

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
from discord_message_components import *

client = commands.Bot(" ")
extension = Extension(client)

@extension.slash.subcommand_group(base_names=["generate", "link"], name="button", description="sends a button and a linkbutton", options=[
        SlashOption(str, "message content", "the content of the message"), 
        SlashOption(str, "name", "the name of the button"), 
        SlashOption(str, "link", "the link for the button"), 
        SlashOption(str, "emoji", "a emoji appearing before the text")
    ], guild_ids=["785567635802816595"])
async def command(ctx, message_content="cool, right?", name="click me", link="https://github.com/KusoRedsto/discord-message-components", emoji=None):
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

You can find more (and better) examples [here](https://github.com/KusoRedsto/discord-message-components/tree/main/examples)

# Changelog

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

    - (Hopefully) the docs

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
    - [documentation](https://discord-message-components.readthedocs.io/en/latest/)
    
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

- RedstoneZockt#2510
- ! DaKuso#4214
- [a shitty support server](https://discord.gg/pwUvz5PbrE)