# Example by 404kuso
# https://github.com/KusoRedsto/discord-ui/tree/main/examples/context_commands.py
#
#       This example will use the two new ui context commands,
#       one will quote the message and one will send their avatar
# Note:
#       If you want to test this, replace '785567635802816595' in guild_ids=[] with a guild id of
#       your choice, because guild slash commands are way faster than globals

import discord
from discord.ext import commands
from discord_ui import UI

# The main bot client
client = commands.Bot(" ")
# Initialize the extension
ui = UI(client)


# Create the command
@ui.slash.message_command("quote", ["785567635802816595"])
# register the callback
async def quote(ctx, message):
    # respond to the interaction so no error will show up
    await ctx.respond("aight", hidden=True)
    # Create a webhook with the same name as the message author
    webhook = await ctx.channel.create_webhook(name=message.author.display_name)
    # Send the message content
    await webhook.send(message.content)
    # delete the webhook
    await webhook.delete()


# Create the command
@ui.slash.user_command("avatar", ["785567635802816595"])
# register the callback
async def avatar(ctx, user):
    # send a embed with the user's avatar
    await ctx.respond(
        embed=discord.Embed(description=user.display_name).set_image(
            url=user._user.avatar_url
        )
    )


# Start the bot with the token, replace token_here with your bot token generated at https://discord.com/developers/applications
client.run("token_here")
