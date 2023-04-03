import asyncio, os
from ChattyGPT import ChattyGPT
from dotenv import load_dotenv

load_dotenv()
ChattyGPT = ChattyGPT()

async def main():
    async with ChattyGPT.bot:
        await ChattyGPT.bot.start(os.getenv(str('DISCORD_TOKEN')))

if __name__ == '__main__':
    asyncio.run(main())
