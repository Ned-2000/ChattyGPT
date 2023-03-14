import discord, openai, asyncio
from discord.ext import commands

class Img(commands.Cog):
    """ Image generation using OpenAI, returns link to prompt """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('image_generation.py online.')
    
    @commands.command()
    async def image(self, ctx):
        if ctx.message.content.replace("!image", "") == "":
            await ctx.reply("The '!image' command is used for image generation.")
            return
        
        print("\nAuthor: " + str(ctx.author))
        print("\nimage prompt: " + str(ctx.message.content))
        
        response_message = await ctx.reply("Generating image...")
        
        try:
            response = openai.Image.create(
            prompt=ctx.message.content.replace("!image", ""),
            n=1,
            size="1024x1024"
            )
            image_url = response['data'][0]['url']
            await response_message.edit(content="Here's your generated image link! It will last for one hour before expiry!\n" + str(image_url),delete_after=3600)
            print("\nimage generated:\n\n" + str(image_url))
                
        except openai.error.OpenAIError as e:
            print(str(e.error))
            await response_message.edit(content="Sorry, your image could not be generated due to this error:\n\n"+ str(e.error.message))
            
        except Exception as e:
            print(str(e))
            await response_message.edit(content="Sorry, your image could not be generated due to this error:\n\n"+ str(e))

async def setup(bot):
    await bot.add_cog(Img(bot))
    print("image_generation cog successfully loaded.")
