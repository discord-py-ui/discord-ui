# Example by 404kuso
# https://github.com/discord-py-ui/discord-ui/tree/main/examples/permissions.py
# 
#       This example will create two slash commands, one that can't be used by default
#       and one that will allow a specific role to use the command
# Note:
#       If you want to test this, replace '785567635802816595' in guild_ids=[] with a guild id of 
#       your choice, because guild slash commands are way faster to register than globals

import discord
from discord.ext import commands
from discord_ui import UI, SlashOption, SlashPermission

client = commands.Bot(" ")
ui = UI(client)

# Create a command that can't be used by default
@ui.slash.command("cool_command", "only cool people can use this command", default_permission=False, guild_ids=[785567635802816595])
async def callback(ctx):
    await ctx.send("you are a mod")

# Create a command for updating the permissions of the "cool_command"
@ui.slash.command("set_cool_people", options=[SlashOption(discord.Role, "role", "the role", True)], guild_ids=[785567635802816595])
# Register the callback
async def callback(ctx, role):
    """Sets the role for the cool people"""
    # Defer the interaction
    await ctx.defer()
    # Update the permissions for the command
    await ui.slash.update_permissions(name="cool_command", typ="slash", guild_id=ctx.guild.id, permissions=SlashPermission({role.id: SlashPermission.Role}))
    # Send a response
    await ctx.send("the cool role was set to " + role.name)


# Start the bot with the token, replace "your_token_here" with your token
client.run("your_token_here")