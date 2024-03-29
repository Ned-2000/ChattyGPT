import discord, openai, os, random, datetime, time, asyncio, aiohttp, json, motor.motor_asyncio, tiktoken
from discord.ext import commands
from discord.ext.commands import BucketType, cooldown

with open('./config.json', 'r') as f:
    config = json.load(f)

mongo_url = config["mongo_url"]

mclient = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
users = mclient["chattygpt"]["users"]

encoding = tiktoken.encoding_for_model("text-davinci-003")

class Gen(commands.Cog):
    """ Prompt generation using OpenAI, replies to user command, edits reply live """

    def __init__(self, bot):
        self.bot = bot
        self.moderation = bool(config["moderation"])
                    
    @commands.Cog.listener()
    async def on_ready(self):
        print('prompt_generation.py online.')
    
    async def create_user(self, id: int):
        new_user = {"id": id, "token_limit": 8000, "token_usage": 0}
        await users.insert_one(new_user)
    
    async def reset_user_tokens(self, id: int):
        if id is not None:
            await users.update_one({"id": id}, {"$set": {"token_usage": 0}})
    
    async def update_user_tokens(self, id: int, all_messages: list[str]):
        if id is not None:
            message_tokens = encoding.encode_batch(all_messages, allowed_special="all")
            tokens = sum(len(token) for token in message_tokens)
            await users.update_one({"id": id}, {"$inc": {"token_usage": +tokens}})
    
    async def update_user_messages(self, id: int, prompt_text: str, all_messages: list[str]):
        if id is not None:
            date = str(datetime.datetime.now())
            prompt_encoded = encoding.encode(prompt_text)
            messages_encoded = encoding.encode_batch(all_messages, allowed_special="all")
            flat_messages = [token for sublist in messages_encoded for token in sublist]
            encoded = [date, prompt_encoded, flat_messages]
            await users.update_one({"id": id}, {"$push": {"messages": encoded}})
    
    @commands.command()
    @cooldown(1, 60, BucketType.user)
    async def reset(self, ctx, member: discord.Member):
        
        if member.bot:
            await ctx.reply("Can't reset tokens of a bot.")
            return
        
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply("Only server administrators can use this command.")
            return
        
        try:
            target = await users.find_one({"id": member.id})
            
            if target is None:
                await self.create_user(member.id)
                target = await users.find_one({"id": member.id})
                await ctx.reply(f"{member}'s token usage has been reset.")
                return
            
            else:
                await self.reset_user_tokens(member.id)
                await ctx.reply(f"{member}'s token usage has been reset.")
                
        except Exception as e:
            print(e)
            error_response = await ctx.reply("Sorry, an unexpected error occurred while processing your request:\n\n" + str(e))
    
    @commands.command()
    @cooldown(1, 5, BucketType.user)
    async def tokens(self, ctx):
        try:
            user = await users.find_one({"id": ctx.author.id})
            
            if user is None:
                await self.create_user(ctx.author.id)
                user = await users.find_one({"id": ctx.author.id})
            
            tokens = user["token_usage"]
            limit = user["token_limit"]
            
            await ctx.reply(f"You have used {tokens} tokens out of your {limit} limit.")
        
        except Exception as e:
            print(e)
            error_response = await ctx.reply("Sorry, an unexpected error occurred while processing your request:\n\n" + str(e))    
    
    @commands.command()
    @cooldown(1, 10, BucketType.user)
    async def prompt(self, ctx):
    
        prompt_text = ctx.message.content[8:]
        
        await ctx.typing()
    
        if not prompt_text:
            await ctx.reply("The '!prompt' command is used for text generation.")
            return
        
        # config JSON file dictates if the message will be moderated for inappropriate content
        if self.moderation:
            try:
                check_prompt = openai.Moderation.create(input=prompt_text)
                
            except Exception as e:
                print(e)
                error_response = await ctx.reply("Sorry, an unexpected error occurred while processing your prompt:\n\n" + str(e))
                error_string = "Sorry, an unexpected error occurred while processing your prompt:\n\n" + str(e)
                await self.update_user_messages(ctx.author.id, prompt_text, [error_string])
                return
            
            if check_prompt.flagged:
                error_string = "Sorry, your message has been flagged as inappropriate and cannot be processed."
                await ctx.reply(error_string)
                await self.update_user_messages(ctx.author.id, prompt_text, [error_string])
                return
        
        all_messages = [] #list representation of the total completions
        curr_messages = [] #current message list representation of completions
        response_message = None
        curr_message = ""
        
        print(f"\nAuthor: {ctx.author}")
        print(f"\nMessage prompt: {ctx.message.content}")

        try:
            
            user = await users.find_one({"id": ctx.author.id})
            
            if user is None:
                await self.create_user(ctx.author.id)
                user = await users.find_one({"id": ctx.author.id})
            
            while ("<EOP>" not in curr_message) and ("<EOL>" not in curr_message):
                async with aiohttp.ClientSession() as session:
                    response = await exponential_wait(ctx, prompt_text)
                
                if not response.choices[0].text:
                    break
                
                new_message = response.choices[0].text.strip()
                print(str(new_message))
                
                curr_message, response_message = handle_character_limit(curr_message, new_message, response_message, curr_messages, all_messages)
                
                curr_messages.append(new_message)
                all_messages.append(new_message)
                
                if not response_message:
                    response_message = await ctx.reply(new_message)
                else:
                    await response_message.edit(content=curr_message)
                
                prompt_text = curr_message
                
                # If the message length is below the limit, update the current message
                if curr_message and (len(curr_messages) < 2000):
                    await response_message.edit(content="".join(curr_messages))

        except Exception as e:
            print(e)
            error_response = await ctx.reply("Sorry, an unexpected error occurred while processing your prompt:\n\n" + str(e))
            error_string = "Sorry, an unexpected error occurred while processing your prompt: " + str(e)
            all_messages.append(error_string)
            
        finally:
            curr_message = curr_message[:2000]
            if response_message:
                await response_message.edit(content=curr_message)
            if all_messages:
                await self.update_user_tokens(ctx.author.id, all_messages)
                await self.update_user_messages(ctx.author.id, prompt_text, all_messages)

async def setup(bot):
    await bot.add_cog(Gen(bot))
    print("prompt cog successfully loaded.")

def generate_response(ctx, prompt_text):
    """
    Function which calls the OpenAI API completion function.
    Returns the next token generated by the API.
    """
    try:
        return openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt_text,
            temperature=1)
    except Exception as e:
        raise e

async def exponential_wait(ctx, p):
        """
        Wrapper function that implements the OpenAI API prompt completion with exponential cooldown when the rate limit is reached.
        Parameters are the discord context (ctx), and the string prompt itself (p).
        Assume p has been cleaned to remove the command invocation.
        If the API request rate is reached, the exception is handled with a random timer.
        Timer increases exponentially with each round until it hits the limit.
        """
        retries = 0
        max_retries = 12
        init_delay = 1
        delay = init_delay
        exp_base = 2
        
        while True:
            try:
                return(generate_response(ctx, p))
                
            except openai.error.RateLimitError as e:
                retries += 1
                
                if retries >= max_retries:
                    raise Exception("Sorry! Maximum amount of rate limit retry cycles of this prompt has been reached. Try again later!")
                    
                delay *= exp_base * (1 + random.random())
                await ctx.reply("Rate limit reached, next try in " + str(round(delay, 3)) + " seconds, " + str(retries) + "/12 allowed retries attempted.",delete_after=(delay+1))
                print("Rate limit reached, next try in " + str(delay) + " seconds, current cycle: " + str(retries))
                await asyncio.sleep(delay)
                
            except Exception as e:
                    raise e
                    
async def handle_character_limit(curr_message, new_message, response_message, curr_messages, all_messages):
    """
    Check if the length of the current message combined with the new message
    exceeds the character limit for a message on Discord. If it does, send the
    current message and start a new one.
    """
    if len(curr_message + new_message) > 2000:
        # If the current message exceeds the limit, send it and reset the message
        curr_message = curr_message[:2000]
        await response_message.edit(content=curr_message)
        all_messages.append(curr_message)
        curr_messages = []
        curr_message = new_message
        new_response_message = await response_message.reply(curr_message)
        response_message = new_response_message
    else:
        curr_message += new_message

    return curr_message, response_message
