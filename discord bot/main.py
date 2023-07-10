import subprocess
import io
import asyncio
import contextlib
import discord
import time
from discord.ext import commands

bot = commands.Bot(command_prefix='.', intents=discord.Intents.all())

automod_enabled = True
ignored_users = []

def is_bot_owner(ctx):
    return ctx.author.id == 719081819521417217

@bot.event
async def on_ready():
    print(f'Connected as {bot.user.name}')
    print(f'Latency: {bot.latency * 1000:.2f}ms')
    owner = await bot.fetch_user(719081819521417217)
    if owner:
        await owner.send('Bot has been successfully rebooted.')

@bot.event
async def on_message(message):
    global automod_enabled
    global ignored_users

    if automod_enabled and message.guild is not None:
        if message.author.id == bot.user.id:
            return

        if message.author.id == message.guild.owner_id or message.author.id in ignored_users:
            return

    await bot.process_commands(message)

async def handle_automod_features(message):
    await handle_anticaps(message)
    await handle_antiinvites(message)
    await handle_antilinks(message)
    await handle_antimentions(message)
    await handle_antispam(message)

async def handle_anticaps(message):
    if message.content.isupper():
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please avoid using excessive capitalization.")

async def handle_antiinvites(message):
    if "discord.gg/" in message.content:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, sharing invite links is not allowed.")

async def handle_antilinks(message):
    if "http://" in message.content or "https://" in message.content:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, posting links is not allowed.")

async def handle_antimentions(message):
    if len(message.mentions) >= 5:
        await message.delete()
        await message.channel.send(f"{message.author.mention}, please avoid excessive mentions.")

async def handle_antispam(message):
    last_messages = await message.channel.history(limit=5).flatten()
    # Implement your antispam logic here

@bot.command()
async def automod(ctx, option=None, user: discord.User = None):
    global automod_enabled
    global ignored_users

    if option == 'enable':
        automod_enabled = True
        await ctx.send("Automod enabled.")
    elif option == 'disable':
        automod_enabled = False
        await ctx.send("Automod disabled.")
    elif option == 'ignore':
        if user is not None:
            ignored_users.append(user.id)
            await ctx.send(f"{user.mention} is now ignored by Automod.")
        else:
            await ctx.send("Please mention a user to ignore.")
    else:
        await ctx.send("Invalid option. Use `enable`, `disable`, or `ignore`.")

@bot.command()
@commands.dm_only()
@commands.check(is_bot_owner)
async def reboot(ctx):
    await ctx.send('Rebooting...')
    subprocess.Popen('python main.py', shell=True)
    await bot.close()

@reboot.error
async def reboot_error(ctx, error):
    if isinstance(error, commands.PrivateMessageOnly):
        await ctx.send('This command can only be executed in DMs.')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('Only the bot owner can execute this command.')

@bot.event
async def on_disconnect():
    owner = await bot.fetch_user(719081819521417217)
    if owner:
        await owner.send('Bot has been rebooted.')

@bot.command()
async def latency(ctx):
    # Calculate message latency
    message_latency = round(bot.latency * 1000)

    # Calculate message round trip latency
    before = time.monotonic()
    message = await ctx.send("Calculating...")
    after = time.monotonic()
    round_trip_latency = round((after - before) * 1000)

    # Calculate shard latency
    shard_latency = round(bot.latency * 1000)

    # Create and send the latency embed
    embed = discord.Embed(title="Latency", color=discord.Color.blue())
    embed.add_field(name="Message Latency", value=f"{message_latency}ms")
    embed.add_field(name="Message Round Trip", value=f"{round_trip_latency}ms")
    embed.add_field(name="Shard Latency", value=f"{shard_latency}ms")

    await message.edit(content=None, embed=embed)

@bot.command()
@commands.check(is_bot_owner)
async def evaluate(ctx, *, code):
    try:
        stdout = io.StringIO()  # Create a StringIO object to capture the output
        with contextlib.redirect_stdout(stdout):  # Redirect the standard output to the StringIO object
            exec(code)  # Use exec() instead of eval() for statements that don't return a value
        output = stdout.getvalue()  # Get the captured output
        if output:
            await ctx.send(f"```\n{output}\n```")
        else:
            await ctx.send("No output.")
    except Exception as e:
        await ctx.send(f"Error: {type(e).__name__} - {e}")

@evaluate.error
async def evaluate_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Only the bot owner can execute this command.')

async def start():
    await bot.start('token_no')

async def close():
    await bot.close()

@bot.event
async def on_connect():
    print('Bot connected to Discord.')

@bot.event
async def on_disconnect():
    print('Bot disconnected from Discord.')

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user.name}')
    print('------')

    # Load extensions
    try:
        await bot.wait_until_ready()
        await bot.load_extension('command_handler')
        print('Extensions loaded successfully')
    except Exception as e:
        print(f'Failed to load extensions: {e}')

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        loop.run_until_complete(close())
    finally:
        loop.close()


