import os
import requests
import urllib.parse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from fastapi.responses import HTMLResponse


class Tools:
    def __init__(self):
        self.valves = self.Valves(
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", "")
        )

    class Valves(BaseModel):
        google_maps_api_key: str = Field(
            default="",
            description="API Key Google Maps (Wajib aktifkan: Places API & Maps Embed API).",
        )

    def search_location(self, query: str) -> str:
        """
        Mencari lokasi dan menampilkan peta interaktif.
        Mendukung pencarian nama tempat, alamat, atau kategori di suatu area.
        :param query: Nama tempat atau deskripsi (misal: 'Kopi Tomohon').
        """
        api_key = self.valves.google_maps_api_key
        if not api_key:
            return "Konfigurasi Error: API Key Google Maps tidak ditemukan."

        clean_query = urllib.parse.quote(query)

        search_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={clean_query}&key={api_key}"

        try:
            response = requests.get(
                search_url, timeout=10
            ) 
            response.raise_for_status()  
            data = response.json()

            if not data.get("results"):
                return f"Lokasi '{query}' tidak dapat ditemukan."

            place = data["results"][0]
            name = place.get("name")
            address = place.get("formatted_address")
            place_id = place.get("place_id")

            lat = place["geometry"]["location"]["lat"]
            lng = place["geometry"]["location"]["lng"]

            embed_url = (
                f"https://www.google.com/maps/embed/v1/place?key={api_key}"
                f"&q=place_id:{place_id}"
            )

            navigation_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={place_id}"

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
                </div>
                """
            headers = {"Content-Disposition": "inline"}
            return HTMLResponse(content=html_content, headers=headers)

        except requests.exceptions.RequestException as e:
            return f"Gagal menghubungi server Google: {str(e)}"
        except Exception as e:
            return f"Terjadi kesalahan: {str(e)}"
