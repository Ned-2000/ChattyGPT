import discord, openai, os, datetime, asyncio
from dotenv import load_dotenv
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
intents.typing = True

load_dotenv()
openai.api_key = os.getenv(str('OPENAI_TOKEN'))

class ChattyGPT:
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.typing = True
        
        self.bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)
        self.bot.remove_command('help')
        discord.utils.setup_logging()
        
        self.bot.ChattyGPT = self
        self.bot.on_ready = self.on_ready

    async def on_ready(self):
        start_date = str(datetime.datetime.now())
        print('We have logged in as {0} at {1}'.format(self.bot.user, start_date))
        await self.load_cogs()

    async def load_cogs(self):
        for cogfile in os.listdir('./cogs'):
            await self.load_cog(cogfile)
                    
    async def load_cog(self, cogfile):
        if cogfile.endswith('.py'):
                try:
                    cogname = cogfile.replace(".py", "")
                    await self.bot.load_extension(f'cogs.{cogname}')
                except Exception as e:
                    print(f'{cogfile} could not be loaded')
                    raise e
