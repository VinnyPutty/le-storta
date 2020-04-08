import os

from dotenv import load_dotenv

from mysql_connector.basic_connector import BasicConnector


class DiscordGuild:

    def __init__(self, *, guild, bot):
        self.guild = guild
        self.bot = bot

        self.mysql_conn: BasicConnector = None
        self.databases = {}

        load_dotenv('../config/.env')

        self.init_setup()

    def init_setup(self):
        print(f'Initial setup for guild "{self.guild.name}"')
        self.mysql_conn = BasicConnector(guild=self.guild, bot=self.bot)
        # mysql_basic_connector.connect_to_mysql()
        # mysql_client = connect_to_mysql()
        # mysql_cursor = mysql_client.cursor()
        database_list = self.mysql_conn.build_database_list()
        print(f'Old database list: {database_list}')
        self.mysql_conn.verify_database_existence(db_name='$'.join((os.getenv('QUOTES_DB_NAME'), str(self.guild.id))),
                                                  database_list=database_list)
        self.mysql_conn.verify_database_existence(db_name='$'.join((os.getenv('KANAN_DB_NAME'), str(self.guild.id))),
                                                  database_list=database_list)
        self.mysql_conn.verify_database_existence(
            db_name=self.build_custom_db_name(os.getenv('MESSAGE_SCRAMBLER_DB_NAME')), database_list=database_list)
        database_list = self.mysql_conn.build_database_list()
        print(f'Updated database list: {database_list}')

        self.mysql_conn.init_table(self.build_custom_db_name(os.getenv('QUOTES_DB_NAME')), 'corn',
                                   os.getenv('QUOTES_TB_COLS_INIT'))
        # mysql_dbclient = connect_to_mysql(database=os.getenv('QUOTES_DB_NAME'))
        # mysql_dbcursor = mysql_dbclient.cursor()
        # verify_table_existence(mysql_dbcursor, 'corn', os.getenv('QUOTES_TB_COLS_INIT'))

        self.mysql_conn.init_table(self.build_custom_db_name(os.getenv('KANAN_DB_NAME')), 'kanan',
                                   os.getenv('KANAN_TB_COLS_INIT'))

        # channel = discord.utils.get(self.guild.text_channels, name=os.getenv('KANAN_CHANNEL'))
        # if channel:
        #     channel_id = channel.id
        #     kanan_channel_history = list(self.guild.get_channel(channel_id).history())

        # self.mysql_conn.build_kanan_table('$'.join((os.getenv('KANAN_DB_NAME'), str(self.guild.id))), 'kanan',
        #                             os.getenv('KANAN_TB_COLS_INIT'), '(link)')

        self.mysql_conn.build_message_scrambler_table(
            self.build_custom_db_name(os.getenv('MESSAGE_SCRAMBLER_DB_NAME')),
            'message_scrambler', os.getenv('MESSAGE_SCRAMBLER_TB_COLS_INIT'))

    async def get_mysql_conn(self):
        return self.mysql_conn

    def build_custom_db_name(self, db_prefix):
        return '$'.join((db_prefix, str(self.guild.id)))
