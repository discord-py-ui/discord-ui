# Discord UI

## 5.0.2
### Fixed
- Removed print statements

## 5.0.1
### Fixed
- Choices not working

## 5.0
### Fixed
- Roles not being parsed correctly
### Changed
- default_permission
    > default_permission can now be of type `discord.Permissions` but the api doesn't support that yet.
- slash http
    > some code changes to slash-http features
### New
- ChoiceGeneratorContext
    > Context class for choice generation
- SlashOption
    > `choice_generator` keyword and `autocomplete` keyword. 
    > `autocomplete` is not needed if you pass choice_generator
- File sending
    > You are now able to send hidden files

## (The others comming soon)

## 4.0
### New
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

### Fixed
- SlashCommand
    > Slash commands wouldn't be updated if only `default_permission` was changed

### Changed
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

### Removed
- ResponseMessage
    > Removed ResponseMessage

## 3.3.5
### Fixed
- SelectMenu
    > SelectMenu issue when creating it from data


## 3.3.4
### Changed
- edit
    > `Message.edit` now takes a `embed` parameter

### Fixed
- print
    > Forgot to remove some `print` statements 


## 3.3.3
### New
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
### Fixed
- dpy2
    > discord.py v2 now auto-decompresses socket data and passes a string instead of the uncompressed data.
- override dpy message
    > when overriding dpy message object, the components would m
## 3.3.2
### New
- EphemeralResponseMessage
    > You can now edit a ephemeral message which was created from an interaction (ex. when a button in a hidden message was pressed)

## 3.3.1
### New
- interaction
    > `Interaction.channel` and `Interaction.guild`

## 3.3.0
### Fixed
- interaction usage in dms

## 3.2.9
### New
- ratelimit fix
    > The lib will now retry after the ratelimit reset and doesn't throw an HTTPException anymore
### Fixed

- sync_commands
    > Got `KeyError` exception while syncing commands

## 3.2.8
### Fixed
- hidden responding
    > When a hidden response was about to be send without defering the interaction it would thrown an error
## 3.2.7
### New 
- warnings
    - When a guild_permission with an invalid guild id is passed, it will throw an exception when syncing the commands
    - When the value of a guild_permission is not of type `SlashPermission` it will throw an exception
- context-commands
    > You can now have context commands with the same name as a normal slash command
- slashcommand description
    > You can use docstrings `"""docstring"""` for setting the description of a slash commmand by setting the dosctring for the callback function

### Changed

- auto_defer
    > auto_defer is now disabled by default
- slash sync
    > You can now disable auto_sync for slash commmands and sync them by yourself with `Slash.sync_commands(delete_unused)`
- Interacion.defer
    > `Interaction._deferred` is not `Interaction.deferred` and `Interaction.defer()` doesn't throw an exception anymore, it will just log the error with `logging.error()`

### Fixed
- try
    > There was a try/catch in the `Interaction.respond` function that would allow the code to continue when an exception occured while responding with ninja_mode
- context commands
    > There was an issue adding context-commands
- Command checking
    > Now, the libary only edits commands when changes were made 
## 3.2.6
### New
- auto ``ninja_mode``
    > If you use `.respond()`, the function will try to use ninja_mode automatically
### Fixed
- ninja_mode response
    > responding with ninja_mode would end up in an exception

- file sending
    > fixed another file sending issue with slash commands
### Changed
- project
    > Moved git-project to https://github.com/discord-py-ui/discord-ui

## 3.2.5

### Fixed
- #89 (thanks for reporting)

## 3.2.4
### Fixed
- version issues with the package

## 3.2.2

### Fixed
- #85: `AttributeError: module 'discord' has no attribute '_Components__version'`

## 3.2.0
### New
-  Interaction
    > Buttons and SelectMenus have a `.message` property for the message where their interaction was creted
    > ResponseMessages have a `.interaction` property for the received interaction
    
- Events
    > We added a `interaction_received` event for all interactions that are received
### Fixed
I'm really sorry for all the issues this libary got, if you still find issues, please report them in https://github.com/discord-py-ui/discord-ui/issues

- SelectOpion
    > There was an issue with emojis not being set in SelectOptions

-  LinkButton
    > There was an issue with setting the url not being set

- SlashCommands
    > There was an issue with creating commands that don't already exist

### Changed
- SelectedMenu
    > `.values` is not `.selected_values`

## 3.1.0
### New
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
### Fixed
- slash commands
    > I finally fixed the damn slashcommand system, it should work now

- Parsing
    > The resolving, fetching and pulling from the cache methods should all work

## 3.0.1
### Fixed
- small project issues

## 3.0
### New
- context commands
    > Context commands are now available

### Changed
- Project name
    > The project's name was changed from `discord-message-components` to `discord-ui`

- ``Extension`` is now ``UI``

## 2.1.0
### New
- Webhook support
    > You are now able to use webhooks together with message components, to send a webhook message with the components, use the `Components.send_webhook` function.
    > The standart webhook function is also overriden with the new component function

- Float type
    > You can now use `float` as the argument type for a slash command option

- Auto empty names
    > Buttons, LinkButtons and SelectOptions labels are now by default `\u200b`, which is an "empty" char 


### Changed
- Code documentation to more be more informative

### Fixed
-  Fixed small code issues (they were already fixed in previous versions, but I just wanna list this here)

- Docs are now working

## 2.0.2
### Fixed
- SelectOption
    > Select option threw an exception if it was smaller than 1 or higher than 100

## 2.0
### New
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


### Changed
 - ``Message``   
    - All Message objects don't use the client object anymore
    - Message.wait_for now needs the client as the first parameter

### Fixed
- Interaction
> All interaction responses work now
- A lot of issues I fogor💀

## 1.2.2
### Fixed
- Docs fixed

## 1.2.1
### Fixed
- Small code fixes

## 1.2.0
### New
- Complete message component suppport
- Select menus
- [documentation](https://discord-ui.readthedocs.io/en/latest/)


## 1.1.2
### Fixed
- Small code fixes

## 1.1.1

### New
- Message.edit()
    > You can now edit messages with button support

## 1.1.0

### Changed
- Major changes to request code, now using the client's request
    - `ResponseMessage.acknowledge()` -> `ResponseMessage.defer()`
        > Changed the name of the function + changed `ResponseMessage.acknowledged` -> `ResponseMessage.deferred`
    - `ResponseMessage.defer()` => `await ResponseMessage.defer()`
        > `defer` (`acknowledge`) is now async and needs to be awaited
### New
- hidden responses
    > You can now send responses only visible to the user
### Fixed
- `ResponseMessage.respond()`
    > Now doesn't show a failed interaction

## 1.0.5
### Fixed
- `ResponseMessage.respond()`
    > responding now doesn't fail after sending the message, it will now defer the interaction by it self if not already deferred and then send the message

## 1.0.4
### New

- `ResponseMessage.acknowledged`
    > Whether the message was acknowledged with the `ResponseMessage.acknowledged()` function

### Changed

- `ResponseMessage.respond()` => `await ResponseMessage.respond()`
    > respond() function is now async and needs to be awaited

- `ResponseMessage.respond() -> None` => `ResponseMessage.respond() -> Message or None`
    > respond() now returns the sent message or None if ninja_mode is true 

## 1.0.3

### New

- `Button.hash`
    >Buttons have now a custom hash property, generated by the discord api