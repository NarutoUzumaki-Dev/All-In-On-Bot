import discord
from discord.ext import commands
import os, json
import google.generativeai as genai
from datetime import timedelta

# --- SETUP FROM PELLA VARIABLES ---
TOKEN = os.getenv("TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
gemini_model = genai.GenerativeModel("gemini-1.5-flash")

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

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"Altron is online as {bot.user}!")
    await bot.change_presence(activity=discord.Game(name="!help | Altron AI"))

# --- MODERATION COMMANDS ---
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="No reason"):
    data = load_w()
    uid = str(member.id)
    if uid not in data: data[uid] = []
    data[uid].append(reason)
    save_w(data)
    await ctx.send(f"⚠️ {member.mention} warned for: {reason} | Total warns: {len(data[uid])}")