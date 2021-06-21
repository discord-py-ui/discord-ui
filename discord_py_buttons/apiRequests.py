from .buttons import Button

import discord

import requests
from typing import List

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
    embeds: List[discord.Embed],
    file: discord.File = None,
    files: List[discord.File] = None,
    nonce: int = None,
    allowed_mentions: discord.AllowedMentions = None,
    reference: discord.MessageReference = None,
    mention_author: bool = None,
    buttons: List[Button] = None,
):
    """Turns parameters from the `discord.TextChannel.send` function into json for requests"""
    payload = {"tts": tts}

    if content is not None:
        payload["content"] = content

    if nonce is not None:
        payload["nonce"] = nonce

    if file is not None and files is not None:
        raise discord.InvalidArgument("cannot pass both 'files' and 'file' parameter")

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

    if embed is not None and embeds is not None:
        raise discord.InvalidArgument("cannot pass both 'embed' and 'embeds' parameter")

    if embed is not None:
        if type(embed) is not discord.Embed:
            raise TypeError(
                "embed must be of type 'discord.Embed', not " + str(type(embed))
            )
        payload["embeds"] = [embed.to_dict()]
    if embeds is not None:
        if type(embeds) is not list:
            raise TypeError("embeds must be of type 'list', not " + str(type(embeds)))
        payload["embeds"] = [em.to_dict() for em in embeds]

    if reference is not None:
        if (
            type(reference)
            not in [
                discord.MessageReference,
                discord.Message,
            ]
            and not issubclass(type(reference), discord.Message)
        ):
            raise TypeError(
                "Reference must be of type 'discord.MessageReference' or 'discord.Message', not "
                + str(type(reference))
            )
        if type(reference) is discord.MessageReference:
            payload["message_reference"] = reference.to_dict()
        elif type(reference) is discord.Message:
            payload["message_reference"] = discord.MessageReference.from_message(
                reference
            ).to_dict()

    if allowed_mentions is not None:
        payload["allowed_mentions"] = allowed_mentions.to_dict()
    if mention_author is not None:
        allowed_mentions = (
            payload["allowed_mentions"]
            if "allowed_mentions" in payload
            else discord.AllowedMentions().to_dict()
        )
        allowed_mentions["replied_user"] = mention_author
        payload["allowed_mentions"] = allowed_mentions

    if buttons:
        componentsJSON = {"components": []}

        wrappers: List[List[Button]] = []

        if len(buttons) > 1:
            curWrapper = []
            i = 0
            for _btn in buttons:
                btn: Button = _btn
                # i > 0         => Preventing empty component field when first button wants to newLine
                if btn.new_line and i > 0:
                    wrappers.append(curWrapper)
                    curWrapper = [btn]
                    continue

                curWrapper.append(btn)
                i += 1
            wrappers.append(curWrapper)
        else:
            wrappers = [buttons]

        for wrap in wrappers:
            componentsJSON["components"].append(
                {"type": 1, "components": [x.to_dict() for x in wrap]}
            )

        payload |= componentsJSON

    return payload
