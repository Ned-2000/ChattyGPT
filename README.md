# ChattyGPT
A Discord bot built in Python using OpenAI's API.
## Current Features:
  - Generate texts, showing live editing as the text is being completed
  - Generate images, which are given as links which expire within an hour
  - Optional moderation for appropriate prompting
  - Goes beyond Discord's 2000-character limit for extended responses with a chain of replies
## Future Implementations:
  - Custom configuration for modifying parameters of text generation
  - Implement recently released gpt-3.5-turbo for continuous conversation
  - Edit cog to edit existing text
  - Permission to use bot at moderator's discretion
  - Tokenizer per user to ration usage / prevent spamming
 ## Requirements:
  - Python 3.8 ++
  - asyncio
  - python-dotenv
  - discord.py
  - openai
  - OpenAI API key
  - Discord bot key
