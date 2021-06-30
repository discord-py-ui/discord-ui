# discord.py button docs

https://pypi.org/project/discord-buttons/



This is a [discord.py](https://github.com/Rapptz/discord.py) button extension made by [404kuso](https://github.com/404kuso) and [RedstoneZockt](https://github.com/RedstoneZockt)

- [Initializing](#Get-started)
- [Client Events](#Events)
- [Sending Butttons](#Sending)
- [Receiving a button press](#Receiving)
- [Complete example](#Example)
- [Code docs](#Code-docs)
- [Changelog](#Changelog)

- - - -

# Get started

First things first, the installation for this package

```cmd
py -m pip install discord_py_buttons 
```

Then you need a `discord.ext.commands.Bot` client in your code

```py
import discord
from discord.ext import commands

client = commands.Bot(" ")
```

To initialize the button extension, you need to import the `Buttons` class

```py
from discord_py_buttons import Buttons

client.buttons = Buttons(client)

```

This will add a listener to button presses and will grant you acces to the button tools

- - - -

# Events

These events can be received trought `client.listen('eventName')` or can be awaited with `client.wait_for('eventName', filter)`

<details>
<summary>on_button_press</summary>

This event will be dispatched if a user pressed a button (a new interaction was created)

The parameters passed to your function will be

- `PressedButton`
    > The Button which was pressed

- `Message`
    > The message on which the button was pressed

If you want to listen to it, your function should look something like this
```py
@client.listen('on_button_press')
async def on_button(btn: PressedButton, message: ResponseMessage)
    # code goes here
```

If you want to await this event, use
```py
btn, msg = await client.wait_for('on_button_press', lambda btn, msg: check here)
```

</details>

- - - -

# Sending

To send a button message, you need the `send` function from a `Buttons` instance

Example:
```py
from discord_py_buttons import Button

@client.listen('on_message')
async def on_message(message: discord.Message):
    if message.content == "!btn":
        await client.buttons.send(message.channel, "here you go", buttons=[Button("myID", "Press me", emoji="😀")])
```

- - - -

# Receiving

If you want to receive a button press, you need to listen to the `on_button_press` event with `client.listen('on_button_press')`


There will be two parameters which will be passed to your function

- `PressedButton`
    > The button which was pressed

- `ResponseMessage`
    > The message on which the button was pressed

To respond to the interaction, you should use `msg.respond()`

Example:
```py
@client.listen('on_button_press')
async def on_button(btn: PressedButton, msg: ResponseMsg):
    await btn.respond("You pressed " + btn.content)
```

- - - -

# Example

Here is an example code, which sends a button everytime a user sends a message with the content `!btn` and replies to every button press with the content of the button

```py
import discord
from discord.ext import commands
from discord_py_buttons import Buttons, Button, PressedButton, ResponseMessage

client.buttons = Buttons(client)

@client.listen('on_message')
async def on_message(message: discord.Message):
    if message.content == "!btn":
        await client.buttons.send("Here ya go!", buttons=[Button("custom_id", "PRESS ME")])
    
@client.listen('on_button_press')
async def on_button(btn: PressedButton, msg: ResponseMessage):
    await msg.respond("You pressed on " + btn.content + " with the customID " + btn.custom_id)

client.run("Your secret token")
```

Here is another example code which uses `client.wait_for`
It will send a question in which the message author decides if they like cats or dogs more

Example
```py
import discord
from discord.ext import commands
from discord_py_buttons import Button, Buttons

client = commands.Bot(" ")

@client.listen('on_message')
async def on_message(message: discord.Message):
    if message.content == "!q":
        # This will send the buttons to the textchannel
        question = await client.buttons.send(message.channel, "What do you like the most?", buttons=[Button("cats", label="I like cats", emoji="🐱"), Button("dogs", label="I like dogs", emoji="🐶")])
        # This will wait for a new button press and only continue if the user who pressed the button is the message author and the messageID on which the button was pressed is the same ID as the message we sent (question)
        btn, msg = await client.wait_for("button_press", check=lambda btn, msg: btn.member.id == message.author.id and msg.id == question.id)

        if btn.custom_id == "cats":
            await msg.respond("yay, cats!")
        elif btn.custom_id == "dogs":
            await msg.respond("yay, dogs")
```

- - - -

- - - -

- - - -

# Code docs


## Buttons: `class`

A button instance for using buttons

<details>
<summary><b>Initialization</b></summary>

```py
Buttons(client: discord.ext.commands.client)
```

- client: `discord.ext.commands.client`
    > The bot client
    
</details>


<details>
<summary><b>Methods</b></summary>

-   <details>
    <summary><b>send</b></summary>

    ```py
    async def send(channel, content=None, *, tts=False, embed=None,
                embeds=None, file=None, files = None, delete_after = None, nonce = None,
                allowed_mentions=None, reference=None, mention_author=None, buttons=None
            ) -> Message:
    ```

    _| coroutine |_

    #### **Parameters**

    - channel: `discord.TextChannel`
        > The textchannel where the message should be sent

    - content: `str`
        > The text content of the message

    - tts: `bool`
        > If the message should be text-to-speech

    - embed: `discord.Embed`
        > The embed included in the message

    - embeds: `List[discord.Embed]`
        > The embeds included in the message

    - file: `discord.File`
        > A file that will be sent as an attachment to the message

    - file: `List[discord.File]`
        > A list of files which will be sent as an attachment

    - delete_after: `float`
        > The numbers of seconds after which the message will be deleted in the background

    - nonce: `int`
        > The nonce to use for sending this message

    - allowed_mentions: `discord.Allowed_mentions`
        > Mentions allowed in this message

    - reference: `discord.MessageReference or discord.Message`
        > The message to which the message replies

    - mention_author: `bool`
        > Whether the author should be mentioned

    - buttons: `List[Button]`
        > A list of buttons in this message


    #### **Returns**
    - `Message`
        > The sent message
    </details>
</details>

- - - -

## Button: `class`

Represents a message component button

<details>
<summary><b>Initialization</b></summary>

```py
Button(custom_id, label = None, color = None, emoji = None, new_line = False, disabled = True)
```

- custom_id: `str`
    > A customID for identifying the button, max _100_ characters

- label: `str`
    > The text that appears on the button, max _80_ characters

- color: `str or int`
    > The color of the button, one of:
    >
    > `[("blurple", "primary", 1), ("gray", "secondary", 2), ("green", "succes", 3), ("red", "danger", 4)]`
    >
    > _Things in () are the same color_

- emoji: `discord.Emoji or str`
    > A emoji appearing before the label

- new_line: `bool`
    > Whether a new line should be added before the button

- disabled: `bool`
    > Whether the button should be clickable (disabled = False) or not (disabled=True)

</details>

<details>
<summary><b>Attributes</b></summary>

- content: `str`
    > The content of the button (emoji + " " + label)

- custom_id: `str`
    > The customID of the button

- label: `str`
    > The text that appears on the button

- color: `str or int`
    > The color of the button

- emoji: `discord.Emoji or str`
    > The emoji appearing before the label

- new_line: `bool`
    > Whether a new line was added before the button

- disabled: `bool`
    > Whether the button is disabled

- hash: `str`
    > The unique hash for the button
</details>

<details>
<summary><b>Methods</b></summary>

-   <details>
    <summary>to_dict: <code>function -> dict</code></summary>
    
    ```py
    def to_dict() -> dict:
    ```
    Converts the button to a python dictionary

    </details>
</details>

- - - -

## LinkButton: `class`

Represents a message component button that will open a link on click

This type of button will not trigger the `on_button_press` event


<details>
<summary><b>Initialization</b></summary>

```py
LinkButton(url: str, label: str, emoji: discord.Emoji or str, new_line: bool, disabled: bool)
```

- url: `str`
    > The url which will be opened when clicking the button

- label: `str`
    > A text that appears on the button, max _80_ characters

- emoji: `discord.Emoji or str`
    > A emoji appearing before the label

- new_line: `bool`
    > Whether a new line should be added before the button

- disabled: `bool`
    > Whether the button should be clickable (disabled = False) or not (disabled=True)

</details>

<details>
<summary><b>Attributes</b></summary>

- content: `str`
    > The content of the button (emoji + " " + label)

- url: `str`
    > The link which will be opened when clicking the button

- label: `str`
    > The text that appears on the button, max _80_ characters

- color: `str or int`
    > The color of the button
    >
    > This will always be `5` (_linkButton_)

- emoji: `discord.Emoji or str`
    > The emoji appearing before the label

- new_line: `bool`
    > Whether a new line was added before the button

- disabled: `bool`
    > Whether the button is disabled

</details>


<details>
<summary><b>Methods</b></summary>

-   <details>
    <summary>to_dict: <code>function -> dict</code></summary>

    ```py
    def to_dict() -> dict:
    ```
    Converts the button to a python dictionary
    
    </details>
</details>

- - - -

## PressedButton: `class`

Represents an Object of a Button which was pressed, including its interaction

<details>
<summary><b>Attributes</b></summary>

- member: `discord.Member`
    > The member who pressed the button

- interaction: `dict`
    > The most important stuff for the interaction which was received
    
    <details>
    <summary>Values</summary>

    - id: `str`
        > The interaction ID
    - token: `str`
        > The interaction token

    </details>

- content: `str`
    > The content of the button (emoji + " " + label)

- url: `str`
    > The link which will be opened when clicking the button

- label: `str`
    > The text that appears on the button, max _80_ characters

- color: `str or int`
    > The color of the button
    >
    > This will always be `5` (_linkButton_)

- emoji: `discord.Emoji or str`
    > The emoji appearing before the label

- new_line: `bool`
    > Whether a new line was added before the button

- disabled: `bool`
    > Whether the button is disabled
    > 
    > Always `True`

- hash: `str`
    > The unique hash for the button

</details>

- - - -

## Message: `class`

Extends the `discord.Message` object


<details>
<summary><b>Attributes</b></summary>

- buttons: `List[Button or LinkButton]`
    > A list of buttons included in the message
</details>

<details>
<summary><b>Methods</b></summary>

-   <details>
    <summary>edit*: <code>function</code></summary>
    
    _* Modified original function_

    Edits the message

    ```py
    async def edit(*, content = None, embed = None, embeds = None, attachments = None, suppress = None, delete_after = None, allowed_mentions = None, buttons = None):
    ```

    

    _| coroutine |_


    #### **Parameters**

    - content: `str`
        > The new text content of the message

    - embed: `discord.Embed`
        > The new embed included in the message

    - embeds: `List[discord.Embed]`
        > The new embeds included in the message
    
    - attachments: `discord.Attachments`
        > A list of discord attachments included in the message
    
    - supress: `bool`
        > Whether the embeds in the message should be shown (False) or not (True)

    - delete_after: `float`
        > The numbers of seconds after which the message will be deleted in the background

    - allowed_mentions: `discord.Allowed_mentions`
        > Mentions allowed in this message

    - buttons: `List[Button]`
        > A list of buttons in this message

</details>

<details>
<summary><b>Super</b></summary>
    
> [discord.Message properties](https://discordpy.readthedocs.io/en/stable/api.html?highlight=message#discord.Message)

</details>

<br>

## ResponseMessage: `class`

A class for responding to a (interaction) message

Extends the `Message` object

<details>
<summary><b>Attributes</b></summary>

- pressedButton: `Button`
    > The button which was pressed

- deferred: `bool`
    > Whether the message was deferred

</details>

<details>
<summary><b>Methods</b></summary>

-   <details>
    <summary>defer: <code>function</code></summary>
    
    defers the interaction

    ```py
    async def defer(hidden = False):
    ```

    _| coroutine |_

    #### **Parameters**

    - hidden
        > Whether the loading thing will be shown only to the user

    > This function should be used if your client needs more than 15 seconds to responod

    </details>

-   <details>
    <summary>respond: <code>function</code></summary>
    Responds to the interaction

    ```py
    async def respond(content=None, *, tts=False,
            embed = None, embeds=None, file=None, files=None, nonce=None,
            allowed_mentions=None, mention_author=None, buttons=None, hidden=False,
        ninjaMode = False) -> Message or None:
    ```

    _| coroutine |_

    #### **Parameters**

    - content: `str`
        > The text content of the message

    - tts: `bool`
        > If the message should be text-to-speech

    - embed: `discord.Embed`
        > The embed included in the message

    - embeds: `List[discord.Embed]`
        > The embeds included in the message

    - file: `discord.File`
        > A file which will be sent as an attachment to the message

    - files: `List[discord.File]`
        > A list of files that will be sent as attachment to the message

    - nonce: `int`
        > The nonce to use for sending this message
    
    - allowed_mentions: `discord.Allowed_mentions`
        > Mentions allowed in this message

    - mention_author: `bool`
        > Whether the author should be mentioned

    - buttons: `List[Button]`
        > A list of buttons in this message
    
    - hidden: `bool`
        > Whether the message should be only visible to the user

    - ninjaMode: `bool`
        > Whether the client should respond silent like a ninja to the interaction
        >
        > (User will see nothing)

    #### **Returns**
    - `Message or None`
        > The sent message if ninjaMode and hidden are both set to false

    </details>
</details>

<details>
<summary><b>Super</b></summary>

> [Message properties](#-message-class)

</details>

- - - -


## Events

Added events for `client.wait_for` and `client.listen`

-   <details>
    <summary>on_button_press</summary>

    ```py
    async def on_button(btn: PressedButton, msg: ResponseMessage):
    ```

    ```py
    def check(btn: PressedButton, msg: ResponseMessage):
    ```

    This event will be dispatched whenever a button was pressed

    Two parameters are passed to the listening function

    [`PressedButton`](##-pressed-class)
    > The button which was pressed

    [`ResponseMessage`](##-responsemessage-class)
    > The message with the interaction on which the button was pressed

    </details>

# Changelog

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
