from email.policy import default
import os
from typing_extensions import Required
from dotenv import load_dotenv
import interactions

load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')
CHANNEL_ID = os.getenv('CHANNEL_ID')

bot = interactions.Client(token=DISCORD_TOKEN, default_scope=SERVER_ID)

@bot.command(description="Test that the bot is functioning", )
async def ping(ctx: interactions.CommandContext):
    await ctx.send("Pong")

@bot.command(description="echo a statement back")
@interactions.option(str, name="text", description="What you would like to print?", required=True)
async def print(ctx: interactions.CommandContext, text: str):
    await ctx.send(text)

@bot.command()
@interactions.option(str, name="event", description="What event would you like to ready up for?", required=True)
@interactions.option(str, name="time", description="What time frame do you want to request?", required=True)
@interactions.option(int, name="ready_count", description="How many people would you like to wait for?", required=True)
@interactions.option(int, name="cancel_count", description="How many unready replies cancel the event", required=False)
async def ready(ctx : interactions.CommandContext, event : str, time : str,ready_count : int, cancel_count : int = None):
    message = await ctx.send(f"Ready Check for: **{event}** @ `{time}` :white_check_mark:::negative_squared_cross_mark:")
    print('y')

@bot.event
async def on_reaction_add(reaction, user):
    print('x')
    channel = reaction.message.channel
    embed = reaction.embeds[0]
    emoji = reaction.emoji

bot.start()