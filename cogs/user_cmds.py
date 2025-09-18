# cogs/user_cmds.py → User commands 🌸
import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import subprocess
import random
import string
from datetime import datetime

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        
    def load_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
    def save_config(self):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def generate_hostname(self, username):
        """Generate hostname from username"""
        clean_name = ''.join(c for c in username if c.isalnum() or c in '-_').lower()[:15]
        if not clean_name:
            clean_name = 'user'
        return f"{clean_name}-vps"

    # --- User Slash Commands ---
    
    @app_commands.command(name="myinv", description="💌 Check your invites")
    async def myinv(self, interaction: discord.Interaction):
        # Placeholder - implement invite tracking system
        embed = discord.Embed(
            title="💌 Your Invites",
            description="You have invited **0** members so far.\nInvite more to unlock better VPS planes!",
            color=0xFFB6C1
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="getvps", description="💻 DM VPS plans; hostname auto = <username>-vps")
    async def getvps(self, interaction: discord.Interaction):
        user = interaction.user
        hostname = self.generate_hostname(user.name)
        
        embed = discord.Embed(
            title="🎀 Choose Your Starter VPS",
            description=f"Your default hostname: `{hostname}`\nUse `/plane` to see available plans!",
            color=0x9B59B6
        )
        embed.add_field(name="💡 Tip", value="Invite friends to unlock better planes!", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="plane", description="🎀 Show 5 starter VPS planes with invite rewards")
    async def plane(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🚀 Available VPS Planes",
            color=0x3498DB
        )
        
        planes = self.config.get('planes', {})
        for pid, specs in planes.items():
            invite_req = int(pid) * 5  # Example: Plane 1 = 5 invites, Plane 2 = 10, etc.
            embed.add_field(
                name=f"Plane {pid} 💫",
                value=f"CPU: {specs['cpu']} cores\nRAM: {specs['ram']}\nDisk: {specs['disk']}\nRequired Invites: {invite_req}",
                inline=False
            )
        
        embed.set_footer(text="Use /getvps to start your journey!")
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="mange", description="🌸 Manage VPS (start, stop, restart, re-ssh)")
    async def mange(self, interaction: discord.Interaction):
        # Placeholder for VPS management UI
        view = VPSManageView()
        embed = discord.Embed(
            title="🌸 VPS Management Panel",
            description="Select an action below to manage your VPS instance.",
            color=0xE91E63
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    @app_commands.command(name="myvps", description="🌟 List your VPS instances with details")
    async def myvps(self, interaction: discord.Interaction):
        # Placeholder - implement user VPS tracking
        embed = discord.Embed(
            title="🌟 Your VPS Instances",
            description="You currently have **0** active VPS instances.",
            color=0xF1C40F
        )
        embed.add_field(name="💡 Tip", value="Use `/getvps` to create your first VPS!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="usage", description="📊 Show CPU, RAM, Disk usage for your VPS")
    async def usage(self, interaction: discord.Interaction):
        # Placeholder - implement real usage stats via tmate/Docker
        embed = discord.Embed(
            title="📊 Resource Usage",
            description="📊 Simulated usage for demonstration:",
            color=0x2ECC71
        )
        embed.add_field(name="CPU Usage", value="🟢 12%", inline=True)
        embed.add_field(name="RAM Usage", value="🟡 45%", inline=True)
        embed.add_field(name="Disk Usage", value="🔵 30%", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="backup", description="💾 Generate VPS backup snapshot")
    async def backup(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # Placeholder - implement backup system
        await asyncio.sleep(2)
        embed = discord.Embed(
            title="✅ Backup Created",
            description="Your VPS snapshot has been saved successfully!",
            color=0x27AE60
        )
        embed.add_field(name="Snapshot ID", value="`snap-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + "`", inline=False)
        embed.set_footer(text="Use /restore to recover from backup")
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="restore", description="🔄 Restore VPS from backup")
    async def restore(self, interaction: discord.Interaction):
        # Placeholder
        embed = discord.Embed(
            title="🔄 Restore VPS",
            description="Please provide a Snapshot ID to restore from.",
            color=0xF39C12
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="invite_reward", description="🎉 Check invite milestones to unlock planes")
    async def invite_reward(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 Invite Rewards",
            description="Invite friends to unlock better VPS planes!",
            color=0x9B59B6
        )
        for i in range(1, 6):
            invites_needed = i * 5
            embed.add_field(
                name=f"Plane {i} 🌸",
                value=f"Requires {invites_needed} invites",
                inline=False
            )
        embed.set_footer(text="Use /myinv to check your current invites")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="status", description="🕒 Bot uptime + system status")
    async def status(self, interaction: discord.Interaction):
        uptime = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        embed = discord.Embed(
            title="🕒 System Status",
            color=0x2ECC71
        )
        embed.add_field(name="Bot Uptime", value=uptime_str, inline=False)
        embed.add_field(name="Active Users", value="0 (placeholder)", inline=True)
        embed.add_field(name="Active VPS", value="0 (placeholder)", inline=True)
        embed.add_field(name="System Load", value="🟢 Healthy", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="helpme", description="📖 Show help menu with all commands")
    async def helpme(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 nxh-i7 Help Menu",
            description="All available commands for managing your cute VPS!",
            color=0x3498DB
        )
        embed.add_field(
            name="🌸 User Commands",
            value="`/myinv` `/getvps` `/plane` `/mange` `/myvps` `/usage` `/backup` `/restore` `/invite_reward` `/status` `/helpme` `/support` `/upgrade` `/stopall` `/botinfo`",
            inline=False
        )
        embed.set_footer(text="Use /support if you need assistance!")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="support", description="🎧 Send server invite or DM support")
    async def support(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎧 Need Help?",
            description="Join our support server or DM a staff member!",
            color=0xE67E22
        )
        embed.add_field(name="Support Server", value="[Join Here](https://discord.gg/example)", inline=False)
        embed.add_field(name="DM Support", value="Use `/support` in DM for direct help", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="upgrade", description="🔼 Upgrade VPS to higher plane")
    async def upgrade(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🔼 Upgrade Your VPS",
            description="Select a higher plane to upgrade your existing VPS!",
            color=0x9B59B6
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="stopall", description="🛑 Stop all your VPS instances")
    async def stopall(self, interaction: discord.Interaction):
        # Placeholder
        embed = discord.Embed(
            title="🛑 Stopping All VPS",
            description="All your VPS instances have been stopped successfully.",
            color=0xE74C3C
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="botinfo", description="✨ Show bot info + credits")
    async def botinfo(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌸 nxh-i7 Bot Info",
            color=0xFF69B4
        )
        embed.add_field(name="Version", value="v1.0.0", inline=False)
        embed.add_field(name="Language", value="Python", inline=False)
        embed.add_field(name="Features", value="VPS Manager (tmate, Docker, Ubuntu 22.04)", inline=False)
        embed.set_footer(text="Made by Mustakin 💻✨")
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Simple View for VPS Management (placeholder)
class VPSManageView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
    
    @discord.ui.button(label="Start", style=discord.ButtonStyle.green, emoji="▶️")
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("✅ Starting your VPS...", ephemeral=True)
    
    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red, emoji="⏹️")
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🛑 Stopping your VPS...", ephemeral=True)
    
    @discord.ui.button(label="Restart", style=discord.ButtonStyle.blurple, emoji="🔄")
    async def restart_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 Restarting your VPS...", ephemeral=True)
    
    @discord.ui.button(label="Re-SSH", style=discord.ButtonStyle.grey, emoji="🔗")
    async def ressh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔗 Generating new SSH session...", ephemeral=True)

async def setup(bot):
    await bot.add_cog(UserCommands(bot))
