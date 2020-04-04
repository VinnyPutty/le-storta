# basic_bot.py
import os
import random

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv(dotenv_path='./config/.env')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

# client = discord.Client()

bot = commands.Bot(command_prefix='^')


@bot.command(name='rq', help='Responds with a random quote from corn')
async def random_quote(ctx):
    print(f'Message seen: "{ctx.message.content}" in channel: "{ctx.message.channel}"')
    corn_quotes = [
        'The heck why does everyone need to announce their desire to eat me',
        'well swive me then',
        (
            'Wait why do I look pregnant in that snap\n'
            'Better than her pregnant I guess'
        ),
    ]
    response = random.choice(corn_quotes)
    await ctx.send(response)


@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    if not guild: return
    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})\n'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


@bot.event
async def on_message(message):
    print(f'Message seen: "{message.content}" in channel: "{message.channel}"')
    if str(message.channel) not in ['home', 'gaming', 'news']:
        await bot.process_commands(message)
    return
    if message.author == bot.user:
        return

    if message.content[0] == '^':
        command, args = message[1:].split(' '), []
        if len(command) > 1:
            command, args = command[0], command[1:]
        parse_command(command[0], args)


    corn_quotes = [
        'The heck why does everyone need to announce their desire to eat me',
        'well swive me then',
        (
            'Wait why do I look pregnant in that snap\n'
            'Better than her pregnant I guess'
        ),
    ]

    if message.content == 'iajofiawejfpjapefkaopekfopakewopfk':
        response = random.choice(corn_quotes)
        await message.channel.send(response)
    elif message.content == 'raise-exception':
        raise discord.DiscordException

def parse_command(command, args):
    if command in ['randquote', 'randomquote', 'rq']:
        if args[0] == '@vinnyputty':
            return

def main():
    bot.run(TOKEN)


if __name__ == '__main__':
    main()

