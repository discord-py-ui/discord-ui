import discord
import requests


from typing import List
from .buttons import Button

url = "https://discord.com/api/v8"


def POST(token, URL, data):
    """POST request with the Bot token in the Authorization Header"""
    return requests.post(URL, json=data, headers={"Authorization": f"Bot {token}"})


def GET(token, URL):
    """GET request with the Bot token in the Authorization Header"""
    return requests.get(URL, headers={"Authorization": f"Bot {token}"})


def DELETE(token, URL):
    """DELETE request with the Bot token in the Authorization Header"""
    return requests.delete(URL, headers={"Authorization": f"Bot {token}"})


def jsonifyMessage(
    content=None,
    *,
    tts=False,
    embed: discord.Embed = None,
    file: discord.File = None,
    files: List[discord.File] = None,
    nonce: int = None,
    allowed_mentions: discord.AllowedMentions = None,
    reference: discord.MessageReference = None,
    mention_author: bool = None,
    buttons: List[Button] = None,
    state=None,
):
    """Turns parameters from the `discord.TextChannel.send` function into json for requests"""
    payload = {"tts": tts}

    if content is not None:
        payload["content"] = content

    if nonce is not None:
        payload["nonce"] = nonce

    if file is not None and files is not None:
        raise discord.InvalidArgument("cannot pass files and file parameter")

    if file is not None:
        if type(file) is not discord.File:
            raise TypeError("file must be of type discord.File")
        raise Exception(
            "sending file is not supportet in this version, instead try using the normal discord.TextChannel.send(file=yourFile) function until this is completed"
        )
    if files is not None:
        if type(file) is not discord.File:
            raise TypeError("file must be of type discord.File")
        raise Exception(
            "sending files is not supportet in this version, instead try using the normal discord.TextChannel.send(files=[yourFiles...]) function until this is completed"
        )

    if embed is not None:
        if type(embed) is not discord.Embed:
            raise TypeError("embed must be of type discord.Embed")
        payload["embed"] = embed.to_dict()

    if reference is not None:
        if type(reference) is not discord.MessageReference:
            raise TypeError("Reference must be of type discord.MessageReference")
        payload["message_reference"] = reference.to_dict()

    if allowed_mentions is not None:
        if state.allowed_mentions is not None:
            payload["allowed_mentions"] = state.allowed_mentions.merge(
                allowed_mentions
            ).to_dict()
        else:
            payload["allowed_mentions"] = allowed_mentions.to_dict()
    if mention_author is not None:
        allowed_mentions = (
            payload["allowed_mentions"]
            if "allowed_mentions" in payload
            else discord.AllowedMentions().to_dict()
        )
        allowed_mentions["replied_user"] = bool(mention_author)
        payload["allowed_mentions"] = allowed_mentions

    # region buttons
    if buttons:
        componentsJSON = {"components": []}

        wrapperButtons = []
        currentLineButtons = []

        if len(buttons) > 1:
            for btn in buttons:
                if len(currentLineButtons) > 5:
                    raise Exception("Limit exceeded: max. 5 Buttons in a row")
                if btn.inline:
                    currentLineButtons.append(btn)
                else:
                    if len(currentLineButtons) > 0:
                        wrapperButtons.append(currentLineButtons)
                    wrapperButtons.append([btn])
                    currentLineButtons = []
            if len(currentLineButtons) > 0:
                wrapperButtons.append(currentLineButtons)
        else:
            wrapperButtons.append([buttons[0]])

        for lineButtons in wrapperButtons:
            componentsJSON["components"].append(
                {"type": 1, "components": [x.to_dict() for x in lineButtons]}
            )

        payload |= componentsJSON
    # endregion buttons

    return payload
