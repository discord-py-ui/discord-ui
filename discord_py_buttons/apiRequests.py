import discord
import requests
import discord
from typing import List
from .buttons import Button

url = "https://discord.com/api/v8"

<<<<<<< Updated upstream
def POST(token, _url, data):
    return requests.post(_url,
        json=data, headers={"Authorization": f"Bot {token}"})
def GET(token, _url):
    return requests.get(_url,
        headers={"Authorization": f"Bot {token}"})
def DELETE(token, _url):
    return requests.delete(_url,
=======

def POST(token, url, data):
    """POST request with the Bot token in the Authorization Header"""
    return requests.post(url,
        json=data, headers={"Authorization": f"Bot {token}"})
def GET(token, url):
    """GET request with the Bot token in the Authorization Header"""
    return requests.get(url,
        headers={"Authorization": f"Bot {token}"})
def DELETE(token, url):
    """DELETE request with the Bot token in the Authorization Header"""
    return requests.delete(url,
>>>>>>> Stashed changes
        headers={"Authorization": f"Bot {token}"})

def jsonifyMessage(content=None, *, tts=False,
            embed=None, file=None, files=None, nonce=None,
            allowed_mentions=None, reference=None, mention_author=None, buttons=None):
    """Turns parameters from the `discord.TextChannel.send` function into json for requests"""
    json = { }
    if content is not None:
        json |= { "content": content }
    if tts is False:
        json |= { "tts": tts }
    if file is not None:
        json |= { "file": file }
    if files is not None:
        json |= {"files": files}
    if nonce is not None:
        json |= { "nonce": nonce }
    if allowed_mentions is not None:
        json |= { "mentions" }

    #region embed
    if embed is not None:
        embedJSON = {"embed": {"type": "rich"} }

        if embed.title:
            embedJSON["embed"] |= embedJSON["embed"] | {"title": embed.title}
        if embed.description:
            embedJSON["embed"] |= {"description": embed.description}
        if embed.url:
            embedJSON["embed"] |= {"url": embed.url}
        if embed.timestamp:
            embedJSON["embed"] |= {"timestamp": embed._timestamp}
        if embed.color:
            embedJSON["embed"] |= {"color": embed._colour.value}
        if embed.footer:
            embedJSON["embed"] |= {"footer": embed._footer}
        if embed.image:
            embedJSON["embed"] |= {"image": embed._image}
        if embed.thumbnail:
            embedJSON["embed"] |= {"thumbnail": embed._thumbnail} 
        if embed.video:
            embedJSON["embed"] |= {"video": embed.video}
        if embed.provider:
            embedJSON["embed"] |= {"provider": embed.provider}
        if embed.author:
            embedJSON["embed"] |= {"author": embed._author}
        if embed.fields:
            embedJSON["embed"] |= {"fields": embed._fields}
        if embed.thumbnail:
            embedJSON["embed"] |= {"thumbnail": embed._thumbnail}

        json = json | embedJSON
    #endregion
    #region reference
<<<<<<< Updated upstream
    if reference:
        json |= {"message_reference": {"message_id": reference.id if type(reference) is discord.Message else reference}}
=======
    if reference is not None and type(reference) is discord.MessageReference:
        json |= { "message_reference": reference.to_dict() }
>>>>>>> Stashed changes
    #endregion
    #region buttons
    if buttons:
        componentsJSON = {"components": []}
        
        wrapperButtons = []
        currentLineButtons = []

        if len(buttons) > 1:
            for btn in buttons:
                if(len(currentLineButtons) > 5):
                    raise Exception("Limit exceeded: max. 5 Buttons in a row")
                if btn.inline:
                    currentLineButtons.append(btn)
                else:
                    if(len(currentLineButtons) > 0):
                        wrapperButtons.append(currentLineButtons)
                    wrapperButtons.append([btn])
                    currentLineButtons = []
            if(len(currentLineButtons) > 0):
                wrapperButtons.append(currentLineButtons)
        else:
            wrapperButtons.append([buttons[0]])

        for lineButtons in wrapperButtons:
            lineButtons = lineButtons
            componentsJSON["components"].append({"type": 1, "components": [x._json for x in lineButtons]})

        json |= componentsJSON
    #endregion buttons
    #region allowedMentions
    if allowed_mentions is not None:
        json |= { "allowed_mentions": allowed_mentions.to_dict() }
    #endregion
    return json