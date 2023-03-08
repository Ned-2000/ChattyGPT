import discord, openai, os, datetime, asyncio
from dotenv import load_dotenv
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)
bot.remove_command('help')

load_dotenv()
openai.api_key = os.getenv(str('OPENAI_TOKEN'))

@bot.event
async def on_ready():
    start_date = str(datetime.datetime.now())
    print('We have logged in as {0} at {1}'.format(bot.user, start_date))
    await load_cogs(bot)
    print("Bot extensions: " + str(bot.extensions))

async def load_cogs(self):
    for cogfile in os.listdir('./cogs'):
        print("cogfile: " + str(cogfile))
        if cogfile.endswith('.py'):
            try:
                cogname = cogfile.replace(".py", "")
                await self.load_extension(f'cogs.{cogname}')
            except Exception as e:
                print(f'{cogfile} could not be loaded')
                raise e

bot.run(os.getenv(str('DISCORD_TOKEN')))