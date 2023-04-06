import discord, os, math
from discord.ext import commands

class Errors(commands.Cog):
    """ Error class to handle command errors """
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        
        error = getattr(error, "orignal", error)
        
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(f"This command is on cooldown. Please retry in {round(error.retry_after, 2)}s.")
            return
        
        elif isinstance(error, commands.DisabledCommand):
            await ctx.reply("This command is currently disabled.")
            return
        
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ""
            for perm in error.missing_permissions:
                perms = perm + "\n"
            await ctx.reply("I am currently missing the following permissions to complete this command:\n" + perms)
            return
        
        elif isinstance(error, commands.MissingPermissions):
            perms = ""
            for perm in error.missing_permissions:
                perms = perm + "\n"
            await ctx.reply("You are currently missing the following permissions to use this command:\n" + perms)
            return
        
        else:
            print(f"Unhandled error in command {ctx.command}. Error: {error}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        print('error_handling.py online.')
        
async def setup(bot):
    await bot.add_cog(Errors(bot))
    print("error_handling cog successfully loaded")