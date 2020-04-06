# basic_bot.py
import asyncio
import json
import os
import random
import sys
from typing import Dict

import discord
from discord.ext import commands
from dotenv import load_dotenv

from discord_classes.discord_guild import DiscordGuild

if not os.path.exists('./config/.env'):
    if not os.path.exists('./config'):
        os.mkdir('./config')
    with open('./config/.env', 'w') as dotenv_file:
        dotenv_file.write('DISCORD_TOKEN=\nDISCORD_GUILD=')
    print('Enter .env variables in "./config/.env"', file=sys.stderr, flush=True)
    exit(1)

load_dotenv(dotenv_path='./config/.env')
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_NAMES = json.loads(os.getenv('DISCORD_GUILD'))

served_guilds: Dict[int, DiscordGuild] = {}
served_guilds_lock = asyncio.Lock()

# client = discord.Client()

bot = commands.Bot(command_prefix='^')


# region Commands
@bot.command(name='randomquote', aliases=['rq', 'randquote'], help='Responds with a random quote from corn')
async def random_quote(ctx, *args):
    # print(f'Message seen: "{ctx.message.content}" in channel: "{ctx.message.channel}"')
    _, args = parse_command(ctx.message.content)
    if len(args) < 1:
        # return
        args = ['corn']
    if args[0] == '<@!189945609615048704>':
        args[0] = 'corn'
    await served_guilds_lock.acquire()
    discord_guild = served_guilds[ctx.guild.id]
    served_guilds_lock.release()
    response = discord_guild.mysql_conn.get_random_row('$'.join((os.getenv('QUOTES_DB_NAME'), str(ctx.guild.id))),
                                                       args[0], os.getenv('QUOTES_TB_COLS'))[0]
    await ctx.send(response)


@bot.command(name='kanan', aliases=['k', 'kana'], help='Responds with a random picture from kanan-channel')
async def random_kanan(ctx, *args):
    # @bot.group(pass_context=True)
    # async def john(ctx):
    #     if ctx.invoked_subcommand is None:
    #         await bot.say('https://i.imgur.com/rZWO3QB.png'.format(ctx))

    # print(f'Message seen: "{ctx.message.content}" in channel: "{ctx.message.channel}"')
    # _, args = parse_command(ctx.message.content)
    # if len(args) < 1:
    #     # return
    #     args = ['corn']
    # if args[0] == '<@!189945609615048704>':
    #     args[0] = 'corn'
    args = ('kanan',)
    await served_guilds_lock.acquire()
    discord_guild = served_guilds[ctx.guild.id]
    served_guilds_lock.release()
    response = discord_guild.mysql_conn.get_random_row('$'.join((os.getenv('KANAN_DB_NAME'), str(ctx.guild.id))),
                                                       args[0], os.getenv('KANAN_TB_COLS'))[0]
    # await ctx.send(response)
    await ctx.send(embed=discord.Embed(title='Here, have some Kanan :)').set_image(url=response))


# TODO split into scramble and unscramble and add option to scramble for specified amount of time
@bot.command(name='togglescramble', aliases=['ts'], help='Toggles the message scrambler state for the selected member')
async def toggle_scramble(ctx, *args):
    print()
    if len(args) < 1:
        ctx.send('*You must specify a member to scramble/stop scrambling.')
    await served_guilds_lock.acquire()
    discord_guild = served_guilds[ctx.guild.id]
    served_guilds_lock.release()
    member = ctx.guild.get_member(int(args[0][3:-1]))
    if member:
        member_row = discord_guild.mysql_conn.select_row(
            '$'.join((os.getenv('MESSAGE_SCRAMBLER_DB_NAME'), str(ctx.guild.id))),
            'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS'), select_clause=f'member={member.id}')
        if not member_row:
            member_row = discord_guild.mysql_conn.add_row(
                '$'.join((os.getenv('MESSAGE_SCRAMBLER_DB_NAME'), str(ctx.guild.id))),
                'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS'),
                row_values=(member.id, True), return_inserted_row=True)
            member_status = member_row[0]
        else:
            member_status = not member_row[1]
            discord_guild.mysql_conn.update_row(
                discord_guild.build_custom_db_name(os.getenv('MESSAGE_SCRAMBLER_DB_NAME')), 'message_scrambler',
                os.getenv('MESSAGE_SCRAMBLER_TB_COLS'), update_clause=f'status={member_status}',
                select_clause=f'member={member.id}')
        response = f'Message scrambling for {member.mention} turned **{"ON" if member_status else "OFF"}**'
    else:
        response = f'Member doesn\'t exist in the server.'
    await ctx.send(response)


# endregion

async def check_scramble_message(message):
    if message.content[0] == '^':
        return False
    await served_guilds_lock.acquire()
    discord_guild = served_guilds[message.guild.id]
    served_guilds_lock.release()
    member = message.author
    # member_row = discord_guild.mysql_conn.select_row(
    #     '$'.join((os.getenv('MESSAGE_SCRAMBLER_DB_NAME'), str(message.guild.id))),
    #     'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS'), select_clause=f'where member={member.id}')
    member_row = discord_guild.mysql_conn.select_row(
        '$'.join((os.getenv('MESSAGE_SCRAMBLER_DB_NAME'), str(message.guild.id))),
        'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS'), select_clause=f'member={member.id}')
    if not member_row:
        member_row = discord_guild.mysql_conn.add_row(
            '$'.join((os.getenv('MESSAGE_SCRAMBLER_DB_NAME'), str(message.guild.id))),
            'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS'),
            row_values=(member.id, True), return_inserted_row=True)
    member_status = member_row[1]
    if not member_status:
        return False
    message_content = message.content
    await message.delete()
    scrambled_message = await scramble_message(message_content)
    response = f'{member.mention}: {scrambled_message}'
    await message.channel.send(response)
    return True


async def scramble_message(message_content):
    message_content = ''.join(filter(lambda s: str.isalpha(s) or s == ' ', message_content))
    message_content = list(message_content.lower())
    random.shuffle(message_content)
    scrambled_message = ''.join(message_content)
    return scrambled_message


# region Events
@bot.event
async def on_ready():
    MEMBERS_TO_PRINT = os.getenv('MEMBERS_TO_PRINT')
    # FIXME maybe handle "allowed" servers differently (currently non-allowed servers are ignored with prejudice,
    #  notification, or configurability
    for guild_name in GUILD_NAMES:
        guild = discord.utils.get(bot.guilds, name=guild_name)
        if guild:
            await served_guilds_lock.acquire()
            if guild.id in served_guilds:
                served_guilds_lock.release()
                continue
            served_guilds[guild.id] = DiscordGuild(guild=guild, bot=bot)
            # await served_guilds[guild.id].mysql_conn.build_kanan_table(
            #     '$'.join((os.getenv('KANAN_DB_NAME'), str(guild.id))), 'kanan',
            #     os.getenv('KANAN_TB_COLS_INIT'), '(link)', limit=None)
            served_guilds_lock.release()
            print(f'\n------')
            print(f'{bot.user} is connected to the following guild: {guild.name} (id: {guild.id})')
            print(f'First {MEMBERS_TO_PRINT} members:')
            members = '\n - '.join([member.name for member in guild.members[:20]])
            print(f' - {members}')
            print(f'------\n')


@bot.event
async def on_message(message):
    print(f'Message seen: "{message.content}" in channel: "{message.channel}"')
    if str(message.channel) not in ['home', 'gaming', 'news']:
        await bot.process_commands(message)
        await check_scramble_message(message)
    return
    if message.author == bot.user:
        return

    if message.content[0] == '^':
        command, args = message[1:].split(' '), []
        if len(command) > 1:
            command, args = command[0], command[1:]
        parse_command(command[0], args)

    if message.content == 'iajofiawejfpjapefkaopekfopakewopfk':
        response = random.choice(corn_quotes)
        await message.channel.send(response)
    elif message.content == 'raise-exception':
        raise discord.DiscordException
#endregion


def parse_command(command):
    command = command.split(' ')
    command, args = command[0], command[1:]
    return command, args


async def print_message_history(guild_id, channel_name, limit=-1):
    print(f'Printing message history of channel "{channel_name}":\n')
    guild = discord.utils.get(bot.guilds, id=guild_id)
    channel = discord.utils.get(guild.text_channels, name=channel_name)
    channel_id = channel.id
    # print_message_history()
    if limit > 0:
        channel_history = bot.get_channel(channel_id).history(limit=limit)
    else:
        channel_history = bot.get_channel(channel_id).history()
    async for message in channel_history:
        print(message.content)


def main():
    # guild = discord.utils.get(bot.guilds, name=)
    # mysql_basic_connector = BasicConnecter()
    # mysql_basic_connector.connect_to_mysql()
    # mysql_client = connect_to_mysql()
    # mysql_cursor = mysql_client.cursor()
    # database_list = build_database_list(mysql_cursor)
    # print(f'Old database list: {database_list}')
    # verify_database_existence(mysql_cursor, db_name=os.getenv('QUOTES_DB_NAME'), database_list=database_list)
    # verify_database_existence(mysql_cursor, db_name=os.getenv('KANAN_DB_NAME'), database_list=database_list)
    # database_list = build_database_list(mysql_cursor)
    # print(f'Updated database list: {database_list}')
    #
    # mysql_dbclient = connect_to_mysql(database=os.getenv('QUOTES_DB_NAME'))
    # mysql_dbcursor = mysql_dbclient.cursor()
    # verify_table_existence(mysql_dbcursor, 'corn', os.getenv('QUOTES_TB_COLS_INIT'))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
