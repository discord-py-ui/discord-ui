https://pypi.org/project/discord-message-components/


## Introduction

This is a [discord.py](https://github.com/Rapptz/discord.py) message component extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt), which you can use until discord.py v2.0 is out

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


## Example


Here is a small example, that will respond to the pressed button with the content of it or will respond with the content and value of the selected element in an select menu

```py
import discord
from discord.ext import commands
from discord_message_components import *

client = commands.Bot(" ")
client.components = Components(client)

@client.listen("ready")
async def on_ready():
    print("ready")

@client.listen('on_message')
async def on_message(message):
    if message.content == "!btn":
        await client.components.send(message.channel, "Ayo this is really cool, right?", components=[
            Button(custom_id="yes", label="yes!", color="green", emoji="😁"), 
            Button(custom_id="no", label="no", emoji="😐", new_line=True)]
        )
    elif message.content == "!sel":
        await client.components.send(message.channel, "This is really cool too, right?", components=[
            SelectMenu(custom_id="select_menus_cool", options=[
                SelectMenuOption(label="yes", value=1, description="I think this is really cool"),
                SelectMenuOption(label="no", value=2, description="Nah this is really boring"),
                SelectMenuOption(label="i don't really know", value=3, emoji="😐")
            ], max_values = 3, default=2)
        ])
    elif message.content == "!mix":
        print("mix")
        await client.components.send(message.channel, 
            content="You can even mix things", 
            embed=discord.Embed(description="nice!"), 
            components=[
                LinkButton("https://discord.com", "discord is really nice"),
                SelectMenu(custom_id="custom_ids", options=[
                    SelectMenuOption("yeess", 4),
                    SelectMenuOption("hello_there", 5, "I really love it")
                ], min_values=1, placeholder="I like everything"),
                Button("again_a_custom_id", "niceu diceu"),
                Button("cool", "lookin good", color="green", new_line=True),
                Button("hehe", "here too", color="red")
        ])

@client.listen('on_button_press')
async def on_button(btn: PressedButton, msg: ResponseMessage):
    await msg.respond(btn.member.mention + ", you pressed on " + btn.content + " with the custom id of " + btn.custom_id)
@client.listen('on_menu_select')
async def on_select(menu: SelectedMenu, msg: ResponseMessage):
    await msg.respond(menu.member.mention + ", you selected " + ', '.join([x.content for x in menu.values]) + " on the menu with the custom id " + menu.custom_id)

client.run(token)
```

# Changelog

-   <details>
    <summary>1.2.2</summary>

    ### **Fixed**
    - Doc fixed

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
        > respond() now returns the sent message or None if ninjaMode is true 

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