"""
title: n8n Pipe Function
author: Cole Medin
author_url: https://www.youtube.com/@ColeMedin
version: 0.2.0

This module defines a Pipe class that utilizes N8N for an Agent
"""

from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import os
import time
import requests
from fastapi.responses import HTMLResponse


def extract_event_info(event_emitter) -> tuple[Optional[str], Optional[str]]:
    if not event_emitter or not event_emitter.__closure__:
        return None, None
    for cell in event_emitter.__closure__:
        if isinstance(request_info := cell.cell_contents, dict):
            chat_id = request_info.get("chat_id")
            message_id = request_info.get("message_id")
            return chat_id, message_id
    return None, None


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(default="http://192.168.199.153:5678/webhook/pico-maps")
        n8n_bearer_token: str = Field(default="...")
        input_field: str = Field(default="chatInput")
        response_field: str = Field(default="output")
        response_result_field: str = Field(default="result")
        google_maps_api_key: str = Field(default="")
        emit_interval: float = Field(
            default=2.0, description="Interval in seconds between status emissions"
        )
        enable_status_indicator: bool = Field(
            default=True, description="Enable or disable status indicator emissions"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "n8n_pipe"
        self.name = "N8N Pipe"
        self.valves = self.Valves()
        self.last_emit_time = 0
        pass

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        current_time = time.time()
        if (
            __event_emitter__
            and self.valves.enable_status_indicator
            and (
                current_time - self.last_emit_time >= self.valves.emit_interval or done
            )
        ):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )
            self.last_emit_time = current_time

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
        __event_call__: Callable[[dict], Awaitable[dict]] = None,
    ) -> Optional[dict]:
        await self.emit_status(
            __event_emitter__, "info", "/Calling N8N Workflow...", False
        )
        chat_id, _ = extract_event_info(__event_emitter__)
        messages = body.get("messages", [])
        if messages:
            question = messages[-1]["content"]
            try:
                # Invoke N8N workflow
                headers = {
                    "Authorization": f"Bearer {self.valves.n8n_bearer_token}",
                    "Content-Type": "application/json",
                }
                payload = {"sessionId": f"{chat_id}"}
                payload[self.valves.input_field] = question
                response = requests.post(
                    self.valves.n8n_url, json=payload, headers=headers, timeout=5000
                )
                print("Almost there..")
                if response.status_code == 200:

                    n8n_response = response.json()[self.valves.response_field]
                    name = response.json()[self.valves.response_result_field]["name"]
                    address = response.json()[self.valves.response_result_field][
                        "formatted_address"
                    ]
                    place_id = response.json()[self.valves.response_result_field][
                        "place_id"
                    ]
                    lat = response.json()[self.valves.response_result_field][
                        "geometry"
                    ]["location"]["lat"]
                    lng = response.json()[self.valves.response_result_field][
                        "geometry"
                    ]["location"]["lng"]

                    navigation_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={place_id}"
                    embed_url = (
                        f"https://www.google.com/maps/embed/v1/place?key={self.valves.google_maps_api_key}"
                        f"&q=place_id:{place_id}"
                    )
                    html_content = f"""
                            <div style="font-family: inherit; color: inherit; line-height: 1.5;">
                                <h3 style="margin: 0 0 5px 0; color: inherit;">{name}</h3>
                                <div style="margin-bottom: 10px;">📍 {address}</div>
                                
                                <iframe 
                                    width="100%" 
                                    height="350" 
                                    src="{embed_url}" 
                                    style="border: 1px solid rgba(0,0,0,0.1); border-radius: 12px; background-color: transparent;" 
                                    allowfullscreen 
                                    loading="lazy">
                                </iframe>
                                
                                <div style="margin-top: 10px;">
                                    <a href="{navigation_url}" target="_blank" style="color: #1a73e8; text-decoration: none; font-weight: bold;">
                                        ➤ Buka Navigasi Google Maps
                                    </a>
                                </div>
                                <div style="margin-top: 10px;">
                                    {n8n_response}
                                </div>
                            </div>
                            """
                    output = (
                        f"### {name}\n\n"
                        f"📍 **Alamat:** {address}\n\n"
                        f'<iframe width="100%" height="350" style="border:0; border-radius:12px;" src="{embed_url}" allowfullscreen  title="Map"></iframe>\n\n'
                        f"{n8n_response}\n\n"
                        f"**[➤ Buka di Google Maps]({navigation_url})**"
                    )
                    # output = f"### {name}📍 **Alamat:** {address}\n\n{n8n_response}\n\n**[➤ Buka di Google Maps]({navigation_url})**"
                    body["messages"].append(
                        {
                            "role": "assistant",
                            "content": output,
                        }
                    )
                    await self.emit_status(__event_emitter__, "info", "Complete", True)

                    return output
                else:
                    raise Exception(f"Error: {response.status_code} - {response.text}")

                # Set assitant message with chain reply
                body["messages"].append({"role": "assistant", "content": n8n_response})
            except Exception as e:
                await self.emit_status(
                    __event_emitter__,
                    "error",
                    f"Error during sequence execution: {str(e)}",
                    True,
                )
                return {"error": str(e)}
        # If no message is available alert user
        else:
            await self.emit_status(
                __event_emitter__,
                "error",
                "No messages found in the request body",
                True,
            )
            body["messages"].append(
                {
                    "role": "assistant",
                    "content": "No messages found in the request body",
                }
            )
        await self.emit_status(__event_emitter__, "info", "Complete", True)

        return n8n_response
