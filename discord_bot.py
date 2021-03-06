import asyncio
import json
import os
import random
import sys
from collections import defaultdict
from typing import Dict

import discord
from discord.ext import commands
from dotenv import load_dotenv

from discord_classes.discord_guild import DiscordGuild
from mysql_connector.basic_connector import BasicConnector

# TODO Implement class style (entirely OO) version of bot
class DiscordBot:

    def __init__(self):
        self.guild_tables_to_build = None

        self.init_bot()

    def init_bot(self):
        pass

    def verify_env_existence(self):
        if not os.path.exists('./config/.env'):
            if not os.path.exists('./config'):
                os.mkdir('./config')
            with open('./config/.env', 'w') as dotenv_file:
                dotenv_file.write('DISCORD_TOKEN=\nDISCORD_GUILD=')
            print('Enter .env variables in "./config/.env"', file=sys.stderr, flush=True)
            exit(1)

    def load_initial_env_variables(self):
        load_dotenv(dotenv_path='./config/.env')
        TOKEN = os.getenv('DISCORD_TOKEN')
        GUILD_NAMES = json.loads(os.getenv('DISCORD_GUILD'))

    async def build_tables(self, guild_id, tables=None):
        if not tables:
            return

        guild = discord.utils.get(bot.guilds, id=guild_id)

        for table_name in tables:
            table_build = implemented_table_builders[table_name]
            if not table_build:
                continue
            await table_build.builder_func(served_guilds[guild_id].mysql_conn,
                                           served_guilds[guild_id].build_custom_db_name(table_build.db_name),
                                           *table_build.get_static_build_params(),
                                           await table_build.get_channel_history(guild, limit=None))


guild_tables_to_build = {
    266837146717913088: ['kanan', 'quotes'],  # 4dpolytopes
    647244068706975763: [''],  # vinnyputty
}


class TableBuild:

    def __init__(self, builder_func, db_name, tb_name, tb_cols_init, tb_cols, channel_name):
        self.builder_func = builder_func
        self.db_name = db_name
        self.tb_name = tb_name
        self.tb_cols_init = tb_cols_init
        self.tb_cols = tb_cols
        self.channel_name = channel_name

    def get_static_build_params(self):
        return self.tb_name, self.tb_cols_init, self.tb_cols

    async def get_channel_history(self, guild, *, limit=200):
        channel = discord.utils.get(guild.text_channels, name=self.channel_name)
        channel_history = None
        if channel:
            channel = guild.get_channel(channel.id)
            channel_history = channel.history(limit=limit)
        return channel_history


implemented_table_builders: Dict[str, TableBuild] = defaultdict(lambda: None)

served_guilds: Dict[int, DiscordGuild] = {}
served_guilds_lock = asyncio.Lock()

# client = discord.Client()

bot = commands.Bot(command_prefix='^')


# region Commands
@bot.command(name='randomquote', aliases=['rq', 'randquote'], help='Responds with a random quote from corn')
async def random_quote(ctx, *args):
    # print(f'Message seen: "{ctx.message.content}" in channel: "{ctx.message.channel}"')
    # _, args = parse_command(ctx.message.content)
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
    response = \
    discord_guild.mysql_conn.get_random_row('$'.join((os.getenv('KANAN_DB_NAME'), str(ctx.guild.id))), args[0],
                                            os.getenv('KANAN_TB_COLS'))[0]
    if not response:
        await ctx.send(content='No kanan available. :(')
    else:
        # await ctx.send(response)
        await ctx.send(
            embed=discord.Embed(title='Here, have some Kanan <:kananayaya:696804621095796777>').set_image(url=response))


# TODO split into scramble and unscramble and add option to scramble for specified amount of time
@bot.command(name='togglescramble', aliases=['ts'], help='Toggles the message scrambler state for the selected member')
async def toggle_scramble(ctx, *args):
    if len(args) < 1:
        await ctx.send('You must specify a member to scramble/stop scrambling.')
        return
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

async def check_scramble_message(message, in_place=False):
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
    if in_place:
        return await scramble_message_in_place(message)
    else:
        return await scramble_message_bot_overwrite(message)


async def scramble_message_bot_overwrite(message):
    message_content = message.content
    await message.delete()
    scrambled_message = await clean_scramble_string(message_content)
    response = f'{message.author.mention}: {scrambled_message}'
    await message.channel.send(response)
    return True


async def scramble_message_in_place(message):
    # Currently impossible because user is only allowed to edit messages that they have sent
    return False


async def clean_scramble_string(orig_string):
    orig_string = ''.join(filter(lambda s: s == ' ' or str.isalpha(s), orig_string))
    orig_string = list(orig_string.lower())
    random.shuffle(orig_string)
    scrambled_string = ''.join(orig_string)
    return scrambled_string


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
            await build_tables(guild.id, guild_tables_to_build[guild.id])
            served_guilds_lock.release()
            print(f'\n------')
            print(f'{bot.user} is connected to the following guild: {guild.name} (id: {guild.id})')
            print(f'First {MEMBERS_TO_PRINT} members:')
            members = '\n - '.join([member.name for member in guild.members[:20]])
            print(f' - {members}')
            print(f'------\n')




@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f'Message seen: "{message.content}" in channel: "{message.channel}"')
    if str(message.channel) not in ['home', 'gaming', 'news']:
        if len(message.content):
            await bot.process_commands(message)
            await check_scramble_message(message)
    return

    if message.content == 'raise-exception':
        raise discord.DiscordException


# endregion


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

    implemented_table_builders['quotes'] = TableBuild(BasicConnector.build_table, os.getenv('QUOTES_DB_NAME'), 'corn',
                                                      os.getenv('QUOTES_TB_COLS_INIT'),
                                                      os.getenv('QUOTES_TB_COLS'),
                                                      os.getenv('QUOTES_CHANNEL'))
    implemented_table_builders['kanan'] = TableBuild(BasicConnector.build_kanan_table, os.getenv('KANAN_DB_NAME'),
                                                     'kanan',
                                                     os.getenv('KANAN_TB_COLS_INIT'),
                                                     os.getenv('KANAN_TB_COLS'),
                                                     os.getenv('KANAN_CHANNEL'))

    bot.run(TOKEN)


if __name__ == '__main__':
    main()
