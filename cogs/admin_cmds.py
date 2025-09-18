# cogs/admin_cmds.py → Admin commands 👑
import discord
from discord import app_commands
from discord.ext import commands
import json
import asyncio

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
    
    def load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def save_config(self):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def is_admin(self, user_id):
        return str(user_id) in self.config.get('admins', [])
    
    # --- Admin Slash Commands ---
    
    @app_commands.command(name="createvps", description="🛠️ Assign VPS to user (choose plane or custom specs)")
    @app_commands.describe(user="The user to assign VPS to", plane="Plane number (1-5) or 'custom'")
    async def createvps(self, interaction: discord.Interaction, user: discord.User, plane: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        # Placeholder logic
        hostname = f"{user.name.lower()[:15]}-vps"
        
        # Log to channel
        log_channel = self.bot.get_channel(int(self.config['log_channel']))
        if log_channel:
            embed = discord.Embed(
                title="🆕 VPS Created",
                color=0x2ECC71,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="User", value=f"{user.mention} (`{user.id}`)", inline=False)
            embed.add_field(name="Plane", value=plane, inline=True)
            embed.add_field(name="Hostname", value=f"`{hostname}`", inline=True)
            await log_channel.send(embed=embed)
        
        await interaction.response.send_message(f"✅ VPS created for {user.mention} with plane `{plane}` and hostname `{hostname}`!", ephemeral=True)
    
    @app_commands.command(name="delvps", description="🗑️ Delete VPS by user or hostname")
    @app_commands.describe(identifier="User mention or hostname")
    async def delvps(self, interaction: discord.Interaction, identifier: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        # Placeholder
        await interaction.response.send_message(f"🗑️ VPS `{identifier}` has been scheduled for deletion.", ephemeral=True)
        
        # Log
        log_channel = self.bot.get_channel(int(self.config['log_channel']))
        if log_channel:
            embed = discord.Embed(
                title="🗑️ VPS Deleted",
                color=0xE74C3C,
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="Deleted By", value=interaction.user.mention, inline=False)
            embed.add_field(name="Target", value=identifier, inline=False)
            await log_channel.send(embed=embed)
    
    @app_commands.command(name="add_admin", description="👑 Add an admin by ID")
    @app_commands.describe(user_id="Discord User ID")
    async def add_admin(self, interaction: discord.Interaction, user_id: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        if user_id not in self.config['admins']:
            self.config['admins'].append(user_id)
            self.save_config()
            await interaction.response.send_message(f"✅ Added <@{user_id}> as admin!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ User is already an admin!", ephemeral=True)
    
    @app_commands.command(name="remove_admin", description="🚫 Remove an admin")
    @app_commands.describe(user_id="Discord User ID")
    async def remove_admin(self, interaction: discord.Interaction, user_id: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        if user_id in self.config['admins']:
            self.config['admins'].remove(user_id)
            self.save_config()
            await interaction.response.send_message(f"✅ Removed <@{user_id}> from admins.", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ User is not an admin!", ephemeral=True)
    
    @app_commands.command(name="setlogchannel", description="📜 Set channel for VPS logs")
    @app_commands.describe(channel="The channel to set as log channel")
    async def setlogchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        self.config['log_channel'] = str(channel.id)
        self.save_config()
        await interaction.response.send_message(f"✅ Log channel set to {channel.mention}", ephemeral=True)
    
    @app_commands.command(name="logs", description="🕵️ Show last VPS actions")
    async def logs(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        # Placeholder - implement actual log reading
        embed = discord.Embed(
            title="🕵️ Recent VPS Actions",
            description="Last 5 actions (placeholder data)",
            color=0x3498DB
        )
        for i in range(5):
            embed.add_field(
                name=f"Action #{i+1}",
                value=f"User: `User{i}`\nAction: `createvps`\nTime: `2 hours ago`",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="editplane", description="✏️ Edit an existing VPS plane")
    @app_commands.describe(plane_id="Plane number", cpu="CPU cores", ram="RAM (e.g., 2GB)", disk="Disk space (e.g., 20GB)")
    async def editplane(self, interaction: discord.Interaction, plane_id: str, cpu: int, ram: str, disk: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        if plane_id in self.config['planes']:
            self.config['planes'][plane_id] = {"cpu": cpu, "ram": ram, "disk": disk}
            self.save_config()
            await interaction.response.send_message(f"✅ Plane {plane_id} updated!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Plane not found!", ephemeral=True)
    
    @app_commands.command(name="addplane", description="➕ Add a new VPS plane dynamically")
    @app_commands.describe(plane_id="New plane ID", cpu="CPU cores", ram="RAM (e.g., 2GB)", disk="Disk space (e.g., 20GB)")
    async def addplane(self, interaction: discord.Interaction, plane_id: str, cpu: int, ram: str, disk: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        self.config['planes'][plane_id] = {"cpu": cpu, "ram": ram, "disk": disk}
        self.save_config()
        await interaction.response.send_message(f"✅ New plane {plane_id} added!", ephemeral=True)
    
    @app_commands.command(name="delplane", description="➖ Remove a VPS plane")
    @app_commands.describe(plane_id="Plane ID to remove")
    async def delplane(self, interaction: discord.Interaction, plane_id: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        if plane_id in self.config['planes']:
            del self.config['planes'][plane_id]
            self.save_config()
            await interaction.response.send_message(f"✅ Plane {plane_id} removed!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Plane not found!", ephemeral=True)
    
    @app_commands.command(name="broadcast", description="📢 Send message to all users")
    @app_commands.describe(message="Message to broadcast")
    async def broadcast(self, interaction: discord.Interaction, message: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        await interaction.response.send_message("📢 Broadcasting message...", ephemeral=True)
        # Placeholder - implement DM broadcasting to users with VPS
        await interaction.followup.send("✅ Broadcast sent to 0 users (placeholder).", ephemeral=True)
    
    @app_commands.command(name="clearinvites", description="♻️ Reset user invites (anti-abuse)")
    @app_commands.describe(user="User to reset invites for")
    async def clearinvites(self, interaction: discord.Interaction, user: discord.User):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        # Placeholder
        await interaction.response.send_message(f"♻️ Invites for {user.mention} have been reset.", ephemeral=True)
    
    @app_commands.command(name="monitor", description="📡 Real-time VPS monitoring")
    async def monitor(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="📡 Real-time VPS Monitor",
            description="Live monitoring dashboard (placeholder)",
            color=0x2ECC71
        )
        embed.add_field(name="Total VPS", value="0", inline=True)
        embed.add_field(name="Active", value="0", inline=True)
        embed.add_field(name="Suspended", value="0", inline=True)
        embed.add_field(name="System Load", value="🟢 0.15", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="suspend", description="⏸️ Suspend VPS temporarily")
    @app_commands.describe(hostname="VPS hostname to suspend")
    async def suspend(self, interaction: discord.Interaction, hostname: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        await interaction.response.send_message(f"⏸️ VPS `{hostname}` suspended successfully.", ephemeral=True)
    
    @app_commands.command(name="resume", description="▶️ Resume suspended VPS")
    @app_commands.describe(hostname="VPS hostname to resume")
    async def resume(self, interaction: discord.Interaction, hostname: str):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        await interaction.response.send_message(f"▶️ VPS `{hostname}` resumed successfully.", ephemeral=True)
    
    @app_commands.command(name="forcebackup", description="🧩 Force backup of all VPS")
    async def forcebackup(self, interaction: discord.Interaction):
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message("👑 Only admins can use this command!", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        await asyncio.sleep(3)  # Simulate backup process
        await interaction.followup.send("✅ Forced backup completed for all VPS instances!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))
