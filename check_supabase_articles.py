#!/usr/bin/env python3
"""
Verificar artículos en Supabase
"""

import json  # noqa: F401

import requests

# URL y key de Supabase
SUPABASE_URL = "https://xmymdivqydldspqmzowr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhteW1kaXZxeWRsZHNwcW16b3dyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzEwODcxMDAsImV4cCI6MjA0NjY2MzEwMH0.VFST4ESMPx_bfrRe4JCOAorU_I1HRVCqKGYlv7VOpXY"

# Headers
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# Consultar artículos
url = f"{SUPABASE_URL}/rest/v1/ArticulosPeriodisticos?select=articulo_id,url,titular&limit=5"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    articles = response.json()
    print(f"Artículos en la base de datos: {len(articles)}")
    for art in articles:
        print(
            f"  - ID: {art['articulo_id']}, URL: {art['url'][:50] if art['url'] else 'None'}..., Titular: {art['titular'][:50] if art['titular'] else 'None'}..."
        )
else:
    print(f"Error al consultar: {response.status_code}")
    print(response.text)
