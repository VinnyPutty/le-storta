# basic_bot.py
import os
import random
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

if not os.path.exists('./config/.env'):
    if not os.path.exists('./config'):
        os.mkdir('./config')
    with open('./config/.env', 'w') as dotenv_file:
        dotenv_file.write('DISCORD_TOKEN=\nDISCORD_GUILD=')
    print('Enter .env variables in "./config/.env"', file=sys.stderr, flush=True)
    exit(1)

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


#region MySQL
def connect_to_mysql(host=None, user=None, passwd=None, database=None):
    if not host:
        host, user, passwd = os.getenv('MYSQL_LOC'), os.getenv('MYSQL_USER'), os.getenv('MYSQL_PASS')
    if not database:
        mysql_client = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd
        )
    else:
        mysql_client = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd,
            database=database
        )
    return mysql_client


def build_database_list(mysql_cursor):
    mysql_cursor.execute('SHOW DATABASES')
    database_list = [database[0] for database in mysql_cursor]
    return database_list


def build_table_list(mysql_dbcursor):
    mysql_dbcursor.execute('SHOW TABLES')
    table_list = [table[0] for table in mysql_dbcursor]
    return table_list


def verify_database_existence(mysql_cursor, db_name, database_list=None):
    if not database_list:
        database_list = build_database_list(mysql_cursor)
    if db_name not in database_list:
        sql_command = f'CREATE DATABASE {db_name}'
        print(f'mysql_exec: {sql_command}')
        mysql_cursor.execute(sql_command)


def verify_table_existence(mysql_dbcursor, tb_name, tb_cols_init, table_list=None):
    if not table_list:
        table_list = build_table_list(mysql_dbcursor)
    if tb_name not in table_list:
        sql_command = f'CREATE TABLE {tb_name} {tb_cols_init}'
        print(f'mysql_exec: {sql_command}')
        mysql_dbcursor.execute(sql_command)


async def build_table(tb_name, tb_cols_init, tb_cols, guild_channel_name=None, limit=-1, mysql_dbcursor=None, db_name=None):
    mysql_dbclient = None
    if not mysql_dbcursor:
        mysql_dbclient = connect_to_mysql(database=db_name)
        mysql_dbcursor = mysql_dbclient.cursor()
    verify_table_existence(mysql_dbcursor, tb_name, tb_cols_init)
    if guild_channel_name:
        guild = discord.utils.get(bot.guilds, name=GUILD)
        channel = discord.utils.get(guild.text_channels, name=guild_channel_name)
        channel_id = channel.id
        if limit > 0:
            channel_history = bot.get_channel(channel_id).history(limit=limit)
        else:
            channel_history = bot.get_channel(channel_id).history()
        async for message in channel_history:
            sql_command = f'INSERT INTO {tb_name} {tb_cols} VALUES (%s)'
            sql_values = (message.content,)
            mysql_dbcursor.execute(sql_command, sql_values)
        mysql_dbclient.commit()


def print_rows(tb_name, tb_cols_init, tb_cols, guild_channel=None, limit=-1, mysql_dbcursor=None, db_name=None):
    print(f'Printing rows from table "{tb_name}":\n')
    mysql_dbclient = None
    if not mysql_dbcursor:
        mysql_dbclient = connect_to_mysql(database=db_name)
        mysql_dbcursor = mysql_dbclient.cursor()
    verify_table_existence(mysql_dbcursor, tb_name, tb_cols_init)
    sql_command = f'SELECT * FROM {tb_name}'
    mysql_dbcursor.execute(sql_command)
    for row in mysql_dbcursor:
        print(row)


def get_random_row(tb_name, tb_cols):
    mysql_dbclient = connect_to_mysql(database=os.getenv('QUOTES_DB_NAME'))
    mysql_dbcursor = mysql_dbclient.cursor()
    sql_command = f'SELECT * FROM {tb_name}'
    print(f'mysql_exec: {sql_command}')
    mysql_dbcursor.execute(sql_command)
    for row in mysql_dbcursor:
        print(row)
    if mysql_dbcursor.rowcount < 1:
        return 'No quotes in table.'
    sql_command = f'SELECT quote FROM {tb_name} WHERE id={random.randint(1, mysql_dbcursor.rowcount)}'
    print(f'mysql_exec: {sql_command}')
    mysql_dbcursor.execute(sql_command)
    quote = list(mysql_dbcursor)[0][0]
    return quote
#endregion

async def print_message_history(channel_name, limit=-1):
    print(f'Printing message history of channel "{channel_name}":\n')
    guild = discord.utils.get(bot.guilds, name=GUILD)
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
    mysql_client = connect_to_mysql()
    mysql_cursor = mysql_client.cursor()
    database_list = build_database_list(mysql_cursor)
    print(f'Old database list: {database_list}')
    verify_database_existence(mysql_cursor, db_name=os.getenv('QUOTES_DB_NAME'), database_list=database_list)
    verify_database_existence(mysql_cursor, db_name=os.getenv('KANAN_DB_NAME'), database_list=database_list)
    database_list = build_database_list(mysql_cursor)
    print(f'Updated database list: {database_list}')

    mysql_dbclient = connect_to_mysql(database=os.getenv('QUOTES_DB_NAME'))
    mysql_dbcursor = mysql_dbclient.cursor()
    verify_table_existence(mysql_dbcursor, 'corn', os.getenv('QUOTES_TB_COLS_INIT'))

    mysql_dbcursor.execute('SELECT * from corn')
    print(mysql_dbcursor.rowcount)








    bot.run(TOKEN)


if __name__ == '__main__':
    main()

