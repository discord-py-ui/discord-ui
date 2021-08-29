# Example by 404kuso
# https://github.com/discord-py-ui/discord-ui/tree/main/examples/role_picker.py
# 
#       This example will use a slash subcommand and will send a select menu only visible to the user,
#       where the user can choose between roles to get
#
# Note: For this example to work, the bot has to have the MANAGE_ROLES permission and the bot role
#       has to be higher than the roles.
#       Also, if you want to test this, replace '785567635802816595' in guild_ids=[] with a guild id of 
#       your choice, because guild slash commands are way faster than globals
# 
#       Replace '867715564155568158', '867715628504186911', '867715582903582743' and '867715674386071602'
#       with roles you want to give the user 

import asyncio
from discord.ext import commands
from discord_ui import UI, SlashedCommand, SelectMenu, SelectOption

# The main bot client
client = commands.Bot(" ")
# initialize the extension
ui = UI(client, slash_options={"wait_sync": 2, "delete_unused": True})

# Create a slash command
@ui.slash.command(name="role-picker", description="let's you pick roles", guild_ids=["785567635802816595"])
async def command(ctx: SlashedCommand):

    # The role picker component
    role_picker = SelectMenu("role_picker", options=[
            SelectOption("javascript", "867715564155568158", "I'm a javascript programmer"),
            SelectOption("java", "867715628504186911", "I'm a java programmer"),
            SelectOption("python", "867715582903582743", "I'm a python programmer"),
            SelectOption("ruby", "867715674386071602", "I'm a ruby programmer")
        ], placeholder="Select your programming language", max_values=4)
    
    # Send the select menu, only visble to the user
    msg = await ctx.send("pick your roles", components=[role_picker], hidden=True)
    try:
        # Wait for a selection on a select menu with the custom_id 
        # 'role_picker' by the user who used the slash command, 
        # with a timeout of 20 seconds
        menu = await msg.wait_for(client, "select", timeout=20)
        # Get all roles in the current guild
        roles = await ctx.channel.guild.fetch_roles()
        given_roles = []
        # Defer the interaction, in case we need more than 3 seconds
        await menu.defer(hidden=True)
        # For every value of the selectmenu selection
        for role in menu.selected_values:
            # For every role in the guild's roles
            for _r in roles:
                # If the id of the current guild role is the same as the value of the current selected value 
                # (in our case the value is the id of the role the user should get) 
                if str(_r.id) == str(role.value):
                    # Add the role to the user
                    await menu.author.add_roles(_r)
                    # Add the current role name to an array where all the given roles are
                    given_roles.append(_r.name)

        # Send which roles the user got, only visible to the user
        await menu.respond("I gave you following roles: `" + ', `'.join(given_roles) + "`", hidden=True)
    # When 20 seconds without input have passed (we set the timeout to 20 seconds)
    except asyncio.TimeoutError:
        # Send a hidden message saying that the user took to long to choose
        await ctx.send(content="you took too long to choose", hidden=True)

# Run the bot (replace 'token_here' with your bot token)
client.run("token_here")
