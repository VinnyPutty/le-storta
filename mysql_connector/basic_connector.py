import os, random

import discord
import mysql.connector
from dotenv import load_dotenv


class BasicConnector:

    def __init__(self, host=None, user=None, passwd=None, *, guild, bot=None):
        # Parameters
        self.host = host
        self.user = user
        self.passwd = passwd
        self.guild = guild
        self.bot = bot

        # Non-parameters members
        self.mysql_client = None
        self.mysql_cursor = None
        self.mysql_db_client = None
        self.mysql_db_cursor = None

        load_dotenv(dotenv_path='../config/.env')

        self.init_setup()

    def init_setup(self):
        if not self.host:
            self.host, self.user, self.passwd = os.getenv('MYSQL_LOC'), os.getenv('MYSQL_USER'), os.getenv('MYSQL_PASS')
        self.mysql_client = self.connect_to_mysql()
        # if self.host:
        #     self.mysql_client = self.connect_to_mysql()
        # else:
        #     self.mysql_client = self.connect_to_mysql(
        #         host=os.getenv('MYSQL_LOC'),
        #         user=os.getenv('MYSQL_USER'),
        #         passwd=os.getenv('MYSQL_PASS')
        #     )
        self.mysql_cursor = self.mysql_client.cursor()

    def connect_to_mysql(self, host=None, user=None, passwd=None, database=None):

        if not host:
            host, user, passwd = self.host, self.user, self.passwd
        if not database:
            print(f'Connection to "{user}"@"{host}" using passwd "{None if not passwd else "****"}"')
            mysql_client = mysql.connector.connect(
                host=host,
                user=user,
                passwd=passwd
            )
        else:
            print(f'Connection to "{database}" in "{user}"@"{host}" using passwd "{None if not passwd else "****"}"')
            mysql_client = mysql.connector.connect(
                host=host,
                user=user,
                passwd=passwd,
                database=database
            )

        return mysql_client

    def build_database_list(self):
        self.mysql_cursor.execute('show databases')
        database_list = [database[0] for database in self.mysql_cursor]
        return database_list

    def build_table_list(self):
        self.mysql_db_cursor.execute('show tables')
        table_list = [table[0] for table in self.mysql_db_cursor]
        return table_list

    # Ensure self.mysql_cursor is instantiated and in a usable location (should always be)
    def verify_database_existence(self, db_name, database_list=None):
        if not database_list:
            database_list = self.build_database_list()
        if db_name not in database_list:
            sql_command = f'create database {db_name}'
            print(f'mysql_exec: {sql_command}')
            self.mysql_cursor.execute(sql_command)

    # Ensure self.mysql_db_cursor is instantiated and in the correct database (this must be manually insured)
    # To avoid this, only call build_table externally (it ensures this and results in the same outcome when parameter
    #   channel_history is None
    def verify_table_existence(self, tb_name, tb_cols_init, table_list=None):
        if not table_list:
            table_list = self.build_table_list()
        if tb_name not in table_list:
            sql_command = f'create table {tb_name} {tb_cols_init}'
            print(f'mysql_exec: {sql_command}')
            self.mysql_db_cursor.execute(sql_command)

    def init_table(self, db_name, tb_name, tb_cols_init):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        self.verify_table_existence(tb_name, tb_cols_init)

    async def build_table(self, db_name, tb_name, tb_cols_init, tb_cols=None, channel_history=None):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        self.verify_table_existence(tb_name, tb_cols_init)
        # Has to be moved because of async calls; should be done in calling function and result passed to build_table
        # if guild_channel_name:
        #     guild = discord.utils.get(self.bot.guilds, name=guild_channel_name)
        #     channel = discord.utils.get(guild.text_channels, name=guild_channel_name)
        #     channel_id = channel.id
        #     if limit > 0:
        #         channel_history = self.bot.get_channel(channel_id).history(limit=limit)
        #     else:
        #         channel_history = self.bot.get_channel(channel_id).history()

        if channel_history:
            # TODO: refactor this to handle different types of messages and different parsing and loading methods
            for message in channel_history:
                sql_command = f'insert ignore into {tb_name} {tb_cols} values (%s)'
                sql_values = (message.content,)
                print(f'mysql_exec: {sql_command}, {sql_values}')
                self.mysql_db_cursor.execute(sql_command, sql_values)
            self.mysql_db_client.commit()

    # FIXME this is a purpose-built table builder for testing purposes; needs to be properly integrated into
    #  build_table functionality
    async def build_kanan_table(self, db_name, tb_name, tb_cols_init, tb_cols=None, channel_history=None, *, limit=200):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        self.verify_table_existence(tb_name, tb_cols_init)
        channel = discord.utils.get(self.guild.text_channels, name=os.getenv('KANAN_CHANNEL'))
        if channel:
            channel = self.guild.get_channel(channel.id)
            channel_history = channel.history(limit=limit)
        print(f'Kanan channel history for guild "{self.guild.name}": {channel_history}')
        if channel_history:
            async for message in channel_history:
                attachments = message.attachments
                # FIXME should be checking for image filetype instead of "True"
                # TODO check that link is not broken before adding (if broken, skip adding to database)
                if len(attachments) > 0 and True:
                    sql_command = f'insert ignore into {tb_name} {tb_cols} values (%s)'
                    sql_values = (attachments[0].url,)
                    print(f'mysql_exec: {sql_command % sql_values}')
                    self.mysql_db_cursor.execute(sql_command, sql_values)
            self.mysql_db_client.commit()

    # FIXME this is another purpose-built table builder for testing purposes; needs to be properly integrated into
    #  build_table functionality
    def build_message_scrambler_table(self, db_name, tb_name, tb_cols_init):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        self.verify_table_existence(tb_name, tb_cols_init)

    def print_rows(self, db_name, tb_name, tb_cols_init, tb_cols, guild_channel=None, limit=-1):
        print(f'Printing rows from table "{tb_name}":')
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        self.verify_table_existence(self.mysql_db_cursor, tb_name, tb_cols_init)
        sql_command = f'select * from {tb_name}'
        print(f'mysql_exec: {sql_command}')
        self.mysql_db_cursor.execute(sql_command)
        for row in self.mysql_db_cursor:
            print(row)

    def add_row(self, db_name, tb_name, tb_cols, row_values, *, commit_inserts=True, return_inserted_row=False):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        values_placeholder = ','.join(['%s' for _ in tb_cols.split(' ')])
        sql_command = f'insert ignore into {tb_name} {tb_cols} values ({values_placeholder})'
        sql_values = row_values
        # print(f'mysql_exec: {sql_command % (str(ele) for ele in sql_values)}')
        print(f'mysql_exec: {sql_command}, {sql_values}')
        self.mysql_db_cursor.execute(sql_command, sql_values)
        if commit_inserts:
            self.mysql_db_client.commit()
        if return_inserted_row:
            tb_cols = tb_cols[1:-1]
            sql_command = f'select {tb_cols} from {tb_name} where id={self.mysql_db_cursor.lastrowid}'
            print(f'mysql_exec: {sql_command}')
            self.mysql_db_cursor.execute(sql_command)
            inserted_row = self.mysql_db_cursor.fetchone()
            return inserted_row
        return None

    def update_row(self, db_name, tb_name, tb_cols, *, row_values=None, update_clause='', select_clause='', commit_updates=True, return_updated_row=False):
        if not select_clause:
            return None
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        if row_values:
            set_functions = ', '.join([f'{col}={val}' for (col, val) in zip(tb_cols, update_clause)])
            sql_command = f'update {tb_name} set {set_functions} where {select_clause};'
            sql_values = row_values
            # print(f'mysql_exec: {sql_command % (str(ele) for ele in sql_values)}')
            print(f'mysql_exec: {sql_command}, {sql_values}')
            self.mysql_db_cursor.execute(sql_command, sql_values)
        elif update_clause:
            sql_command = f'update {tb_name} set {update_clause} where {select_clause};'
            print(f'mysql_exec: {sql_command}')
            self.mysql_db_cursor.execute(sql_command)
        else:
            return None
        if commit_updates:
            self.mysql_db_client.commit()
        if return_updated_row:
            tb_cols = tb_cols[1:-1]
            sql_command = f'select {tb_cols} from {tb_name} where id={self.mysql_db_cursor.lastrowid}'
            print(f'mysql_exec: {sql_command}')
            self.mysql_db_cursor.execute(sql_command)
            updated_row = self.mysql_db_cursor.fetchone()
            return updated_row

    # Only selects and returns 1 row (theoretically this means that it will return the first matching row, but this
    #   functionality is not guaranteed)
    def select_row(self, db_name, tb_name, tb_cols='*', *, select_clause=''):
        if not select_clause:
            return None
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        tb_cols = tb_cols[1:-1]
        sql_command = f'select {tb_cols} from {tb_name} where {select_clause}'
        print(f'mysql_exec: {sql_command}')
        self.mysql_db_cursor.execute(sql_command)
        selected_row = self.mysql_db_cursor.fetchone()
        return selected_row if selected_row else None

    def get_random_row(self, db_name, tb_name, tb_cols):
        self.mysql_db_client = self.connect_to_mysql(database=db_name)
        self.mysql_db_cursor = self.mysql_db_client.cursor()
        # This method is more pythonic but requires fetching all the rows
        # sql_command = f'select * from {tb_name}'
        # print(f'mysql_exec: {sql_command}')
        # self.mysql_db_cursor.execute(sql_command)
        # self.mysql_db_cursor.fetchall()
        # print(f'Row count: {self.mysql_db_cursor.rowcount}')
        # for row in self.mysql_db_cursor:
        #     print(row)
        # if self.mysql_db_cursor.rowcount < 1:
        #     return ('No rows in table.',)

        sql_command = f'select count(*) from {tb_name}'
        print(f'mysql_exec: {sql_command}')
        self.mysql_db_cursor.execute(sql_command)
        # for row in self.mysql_db_cursor:
        #     print(row)
        row_count = self.mysql_db_cursor.fetchone()[0]
        print(f'Row count: {row_count}')
        if row_count < 1:
            return ('No rows in table.',)
        random_row_number = random.randint(0, row_count - 1)
        sql_command = f'select {tb_cols} from {tb_name} limit 1 offset {random_row_number}'
        print(f'mysql_exec: {sql_command}')
        self.mysql_db_cursor.execute(sql_command)
        # TODO if returning row with link, check that link is not broken before returning (if broken, remove from
        #  database)
        random_row = list(self.mysql_db_cursor)[0]
        return random_row
