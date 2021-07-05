import json
import discord

from discord.http import Route
from typing import Any, List

url = "https://discord.com/api/v8"

MISSING = None

class V8Route(Route):
    BASE = "https://discord.com/api/v8"

async def send_files(route, files, payload, http):
    form = []
    form.append({'name': 'payload_json', 'value': json.dumps(payload, separators=(',', ':'), ensure_ascii=True)})

    if len(files) == 1:
        file = files[0]
        form.append({
            'name': 'file',
            'value': file.fp,
            'filename': file.filename,
            'content_type': 'application/octet-stream'
        })
    else:
        for index, file in enumerate(files):
            form.append({
                'name': 'file%s' % index,
                'value': file.fp,
                'filename': file.filename,
                'content_type': 'application/octet-stream'
            })

    r = await http.request(route, form=form, files=files)
    print(r)

def jsonifyMessage(content = MISSING, tts=False,
                embed: discord.Embed = MISSING, embeds: List[discord.Embed] = MISSING, nonce: int = MISSING,
                allowed_mentions: discord.AllowedMentions = MISSING, reference: discord.MessageReference = MISSING, mention_author: bool = MISSING, components: list = MISSING, suppress: bool = MISSING, flags = MISSING):
    """Turns parameters from the `discord.TextChannel.send` function into json for requests"""
    
    payload = { "tts": tts }

    if content is not MISSING:
        payload["content"] = content

    if suppress is not MISSING:
        flags = discord.MessageFlags._from_value(flags or discord.MessageFlags.DEFAULT_VALUE)
        flags.suppress_embeds = suppress
        payload['flags'] = flags.value
    
    if nonce is not MISSING:
        payload["nonce"] = nonce
    
    if embed is not MISSING and embeds is not MISSING:
        raise discord.InvalidArgument("cannot pass both 'embed' and 'embeds' Parameters")

    if embed is not MISSING:
        if type(embed) is not discord.Embed:
            raise TypeError("embed must be of type 'discord.Embed', not " + str(type(embed)))
        payload["embeds"] = [ embed.to_dict() ]
    if embeds is not MISSING:
        if type(embeds) is not list:
            raise TypeError("embeds must be of type 'list', not " + str(type(embeds)))
        payload["embeds"] = [em.to_dict() for em in embeds]

    if reference is not MISSING:
        if type(reference) not in [discord.MessageReference, discord.Message] and not issubclass(type(reference), discord.Message):
            raise TypeError("Reference must be of type 'discord.MessageReference' or 'discord.Message', not " + str(type(reference)))
        if type(reference) is discord.MessageReference:
            payload["message_reference"] = reference.to_dict()
        elif type(reference) is discord.Message:
            payload["message_reference"] = discord.MessageReference.from_message(reference).to_dict()

    if allowed_mentions is not MISSING:
        payload["allowed_mentions"] = allowed_mentions.to_dict()
    if mention_author is not MISSING:
        allowed_mentions = payload["allowed_mentions"] if "allowed_mentions" in payload else discord.AllowedMentions().to_dict()
        allowed_mentions['replied_user'] = mention_author
        payload["allowed_mentions"] = allowed_mentions

    if components is not MISSING:
        componentsList = []
        wrappers: List[List[Any]] = []

        if len(components) > 1:
            curWrapper = []
            i = 0
            for component in components:
                # i > 0         => Preventing empty component field when first button wants to newLine 
                if component.component_type == 3:
                    if i > 0:
                        wrappers.append(curWrapper)
                    curWrapper = [component]
                    wrappers.append(curWrapper)
                    curWrapper = []
                elif component.component_type == 2:
                    if component.new_line and i > 0:
                        wrappers.append(curWrapper)
                        curWrapper = [component]
                    else: 
                        curWrapper.append(component)
                        i += 1
            if len(curWrapper) > 0:
                wrappers.append(curWrapper)
        else:
            wrappers = [components]

        for wrap in wrappers:
            componentsList.append({"type": 1, "components": [x.to_dict() for x in wrap]})
        
        payload["components"] = componentsList 

    return payload