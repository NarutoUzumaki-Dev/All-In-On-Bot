import discord
from discord.ext import commands
import os, json
import google.generativeai as genai
from datetime import timedelta

intents = discord.Intents.all()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- STORAGE ---
if not os.path.exists("warns.json"):
    with open("warns.json","w") as f: json.dump({}, f)
if not os.path.exists("presets.json"):
    with open("presets.json","w") as f: json.dump({}, f)

def load_w():
    with open("warns.json","r") as f: return json.load(f)
def save_w(d):
    with open("warns.json","w") as f: json.dump(d,f,indent=4)
def load_p():
    with open("presets.json","r") as f: return json.load(f)
def save_p(d):
    with open("presets.json","w") as f: json.dump(d,f,indent=4)

# Setup Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"ONLINE as {bot.user}")

# --- 1. BAN ---
@bot.tree.command(name="ban", description="Ban a user")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.ban_members:
        await interaction.response.send_message("You don't have permission!", ephemeral=True); return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 {member} banned | {reason}")

# --- 2. KICK ---
@bot.tree.command(name="kick", description="Kick a user")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason"):
    if not interaction.user.guild_permissions.kick_members:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👢 {member} kicked | {reason}")

# --- 3. MUTE (Timeout) ---
@bot.tree.command(name="mute", description="Mute a user for minutes")
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "No reason"):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    until = discord.utils.utcnow() + timedelta(minutes=minutes)
    await member.timeout(until, reason=reason)
    await interaction.response.send_message(f"🔇 {member} muted for {minutes}m | {reason}")

@bot.tree.command(name="unmute", description="Unmute a user")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    await member.timeout(None)
    await interaction.response.send_message(f"🔊 {member} unmuted")

# --- 4. WARN ---
@bot.tree.command(name="warn", description="Warn a user")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    data = load_w()
    gid = str(interaction.guild.id); uid = str(member.id)
    if gid not in data: data[gid] = {}
    if uid not in data[gid]: data[gid][uid] = []
    data[gid][uid].append(reason)
    save_w(data)
    await interaction.response.send_message(f"⚠️ {member.mention} warned | {reason} | Total warns: {len(data[gid][uid])}")

# --- 5. CHECK WARN ---
@bot.tree.command(name="check-warn", description="Check warns of a user")
async def check_warn(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    data = load_w()
    gid = str(interaction.guild.id); uid = str(member.id)
    warns = data.get(gid, {}).get(uid, [])
    if not warns:
        await interaction.response.send_message(f"{member} has 0 warns", ephemeral=True); return
    embed = discord.Embed(title=f"Warns for {member}", color=discord.Color.orange())
    for i, w in enumerate(warns, 1):
        embed.add_field(name=f"Warn {i}", value=w, inline=False)
    await interaction.response.send_message(embed=embed)

# --- 6. GIVE ROLES ---
@bot.tree.command(name="give-role", description="Give a role to user")
async def give_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    await member.add_roles(role)
    await interaction.response.send_message(f"✅ {role.name} given to {member}")

@bot.tree.command(name="remove-role", description="Remove a role from user")
async def remove_role(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await member.remove_roles(role)
    await interaction.response.send_message(f"❌ {role.name} removed from {member}")

# --- 7. CREATE ROLES ---
@bot.tree.command(name="create-role", description="Create a new role")
async def create_role(interaction: discord.Interaction, name: str, color: str = "#000000"):
    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    try:
        col = discord.Color.from_str(color)
    except:
        col = discord.Color.default()
    role = await interaction.guild.create_role(name=name, color=col)
    await interaction.response.send_message(f"✅ Role {role.mention} created")

# --- 8. CUSTOMIZABLE PRESET ---
@bot.tree.command(name="preset-save", description="Save a customizable preset message")
async def preset_save(interaction: discord.Interaction, preset_name: str, message: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin only!", ephemeral=True); return
    data = load_p()
    gid = str(interaction.guild.id)
    if gid not in data: data[gid] = {}
    data[gid][preset_name] = message
    save_p(data)
    await interaction.response.send_message(f"Preset `{preset_name}` saved!")

@bot.tree.command(name="preset-use", description="Use a preset")
async def preset_use(interaction: discord.Interaction, preset_name: str):
    data = load_p()
    gid = str(interaction.guild.id)
    msg = data.get(gid, {}).get(preset_name)
    if not msg:
        await interaction.response.send_message("Preset not found!", ephemeral=True); return
    await interaction.response.send_message(msg)

@bot.tree.command(name="preset-list", description="List all presets")
async def preset_list(interaction: discord.Interaction):
    data = load_p()
    gid = str(interaction.guild.id)
    presets = data.get(gid, {})
    if not presets:
        await interaction.response.send_message("No presets saved", ephemeral=True); return
    await interaction.response.send_message("Presets: " + ", ".join(presets.keys()))

# --- 9. CHANGE NICKNAME ---
@bot.tree.command(name="nickname", description="Change nickname of a member")
async def nickname(interaction: discord.Interaction, member: discord.Member, new_nick: str):
    if not interaction.user.guild_permissions.manage_nicknames:
        await interaction.response.send_message("No permission!", ephemeral=True); return
    try:
        await member.edit(nick=new_nick)
        await interaction.response.send_message(f"✏️ {member} nickname changed to {new_nick}")
    except:
        await interaction.response.send_message("I can't change that user (role higher than me)")

# --- 10. AI CHAT BOT!!Gemini ---
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.content.startswith("!!Gemini"):
        prompt = message.content.replace("!!Gemini", "").strip()
        if not prompt:
            await message.channel.send("Use: `!!Gemini help me with...`"); return
        async with message.channel.typing():
            try:
                response = gemini_model.generate_content(prompt)
                # Cut to 2000 chars for discord limit
                text = response.text
                if len(text) > 1900:
                    text = text[:1900] + "..."
                await message.channel.send(text)
            except Exception as e:
                await message.channel.send(f"Gemini Error: {e}")
    await bot.process_commands(message)

bot.run(os.getenv("TOKEN"))