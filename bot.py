from discord.ext import commands, tasks
import discord
import asyncpg
import os
import config
from cogs.help import EmbedHelpCommand


TOKEN = config.token
HOST = config.host
DATABASE = config.database
USER = config.user
PASSWORD = config.password

async def create_db_pool():
    credentials = {"user": USER, "password": PASSWORD, "database": DATABASE, "host": HOST}
    try:
        bot.db = await asyncpg.create_pool(**credentials)
    except KeyboardInterrupt:
        await bot.db.close()

async def close_db():
    await bot.db.close()

# Uses privileged gateway intents of the Discord API. Enable guild members and presence intents in the developer portal before running
# Logically, presence intents need not be enabled, but in Robo VJ, disabling presence inetnts broke some functionality
# Therefore I feel it's better to just opt in for both. Both require whitelisting anyway.
# You can choose to disable presences if you wish. It might still work.
#intents = discord.Intents.default()
#intents.members = True
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', help_command=EmbedHelpCommand(dm_help=None, dm_help_threshold=10),
                   owner_id=411166117084528640, intents=intents)

@tasks.loop(count=1)
async def startup():
    print(f"Logged in as {bot.user}")
    print(f"ID: {bot.user.id}")
    print("---------------")
    bot.owner = bot.get_user(bot.owner_id)

@startup.before_loop
async def before_start():
    await bot.wait_until_ready()

@bot.event
async def on_guild_join(guild):
    embed=discord.Embed(title="Thank you for adding me to your server :blush:", colour=discord.Colour.blurple())
    embed.description = f"""I was built to cater to your weekly quiz needs on request of <@!715954704701718608>.
    I was built hastily, so there might be a few bugs, which you can report on discovery using `$bug` or directly to {bot.owner.mention}.

    Questions and options may be loaded via a .csv file built on the template available [here](https://docs.google.com/spreadsheets/d/1v2KPlZ8fdMqzGRqX9G6dsDAYX_HAxqUeh3TmfSffzRM/edit?usp=sharing). Simply fill out the template, download as .csv and upload it in a channel I can see with the message `$load <static/dynamic> [quiz description]`.

    Reactions once added are removed after recording and cannot be changed.

    Running more than one quiz simultaneously, across all servers, is disallowed. This is because game state cannot be tracked per server without making expensive database calls, since memory is too low to cache. If you wish to run your own instance or contribute to development, I am open source [here](https://github.com/darthshittious/MedQuizBot/)

    Cheers and happy quizzing!"""
    embed.set_author(name=guild.me, icon_url=guild.me.avatar_url)
    embed.set_footer(text=f"Made by {bot.owner}", icon_url=bot.owner.avatar_url)
    try:
        await guild.system_channel.send(embed=embed)
    except:
        # either the channel is invisible, or no permissions to send messages, or no system channel set
        # well, we tried
        pass

bot.load_extension('cogs.med_quiz')

@bot.command(hidden=True)
async def ping(ctx):
    """Return bot latency"""
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

startup.start()
try:
    bot.loop.run_until_complete(create_db_pool())
    bot.loop.run_until_complete(bot.start(TOKEN))
except KeyboardInterrupt:
    bot.loop.run_until_complete(bot.logout())
    bot.loop.run_until_complete(close_db())
finally:
    bot.loop.close()
    #client.run(TOKEN)
    startup.cancel()

        
