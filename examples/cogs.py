# Example by 404kuso
# https://github.com/discord-py-ui/discord-ui/tree/main/examples/cpgs.py
#
#       This is just a simple cog command example for application commands
# Note:
#       If you want to test this, replace '785567635802816595' in guild_ids=[] with a guild id of 
#       your choice, because guild slash commands are way faster than globals

# import discord package
import discord
# import commands extention
from discord.ext import commands
from discord_ui import (
    UI, cogs, SlashOption,
    # interaction types for type hinting 
    SlashInteraction, AutocompleteInteraction, ContextInteraction,
    # overridden message object for type hinting
    Message
)

# initialize bot
bot = commands.Bot(" ")


# create the cog
class ExampleCog(commands.Cog):
    # add slashcommand to cog
    @cogs.slash_command("my_command", "this is an example cog command", guild_ids=[785567635802816595])
    # callback for the command
    async def my_command(self, ctx: SlashInteraction):
        ...


    # method that generates choices for the 'hello world' command
    async def my_generator(self, ctx: AutocompleteInteraction):
        return [("hello", "1"), ("world", "2")]

    # add subslash command to the cog
    @cogs.subslash_command("hello", "world", "example subcommand", [
        # simple option that uses autocompletion
        SlashOption(str, "argument", "option that autogenerates somethning", choice_generator=my_generator)
    ])
    # callback for the commmand
    async def my_subcommand(self, ctx: SlashInteraction, argument: str):
        ...


    # add message command to cog
    @cogs.message_command("message", guild_ids=[785567635802816595])
    # callbackfor the command
    async def my_message_command(self, ctx: ContextInteraction, message: Message):
        ...


    # add user command to cog
    @cogs.user_command("user", guild_ids=[785567635802816595])
    # callback for the command
    async def my_user_command(self, ctx: ContextInteraction, member: discord.Member):
        ...


# add the cog to the bot
bot.add_cog(ExampleCog())

# login
bot.run("your token")