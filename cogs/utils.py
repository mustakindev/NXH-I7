# cogs/utils.py → Shared helpers 🛠️
import discord
import json
import os

def load_config():
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config):
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def is_admin(user_id, config):
    return str(user_id) in config.get('admins', [])

def generate_hostname(username):
    clean_name = ''.join(c for c in username if c.isalnum() or c in '-_').lower()[:15]
    return f"{clean_name}-vps" if clean_name else "user-vps"

# Embed templates
def success_embed(title, description=""):
    return discord.Embed(title=title, description=description, color=0x2ECC71)

def error_embed(title, description=""):
    return discord.Embed(title=title, description=description, color=0xE74C3C)

def info_embed(title, description=""):
    return discord.Embed(title=title, description=description, color=0x3498DB)
