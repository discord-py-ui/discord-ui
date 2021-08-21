# Example by 404kuso
# https://github.com/discord-py-ui/discord-ui/tree/main/examples/generate_linkbutton.py
# 
#       This example will use a slash subcommand group and will generate a 
#       linkbutton with a name, link and emoji which the user can specify
# Note:
#       If you want to test this, replace '785567635802816595' in guild_ids=[] with a guild id of 
#       your choice, because guild slash commands are way faster than globals

from discord.ext import commands
from discord_ui import SlashOption, UI, LinkButton

# The main bot client
client = commands.Bot(" ")
# Initialize the extension
ui = UI(client)

# Creating the command
@ui.slash.subcommand_group(base_names=["generate", "link"], 
name="button", description="sends a button and a linkbutton", options=[
        # The user can specify the message content
        SlashOption(str, "message content", "the content of the message"),
        # The name of the linkbutton
        SlashOption(str, "name", "the name of the button"), 
        # The link of the linkbutton
        SlashOption(str, "link", "the link for the button"), 
        # The eomji of the linkbutton
        SlashOption(str, "emoji", "a emoji appearing before the text")
    ], 
    # If you want to test the command, use guild_ids, because this is way faster than global commands
    guild_ids=["785567635802816595"])
async def command(ctx, message_content="cool, right?", name="click me", link="https://github.com/discord-py-ui/discord-ui", emoji=None):
    # Check if the link is valid
    if not link.startswith("http://") and not link.startswith("https://"):
        # send hidden response that the link is invalid
        return await ctx.respond("The link has to start with `http://` or `https://`", hidden=True)
        
    # Send a link button with the link, name and emoji argument
    await ctx.respond(content=message_content, components=[LinkButton(link, label=name, emoji=emoji)])


# Start the bot with the token, replace token_here with your bot token generated at https://discord.com/developers/applications
client.run("token_here")
