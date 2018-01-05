import sqlite3

DEBUG = True

class R53SQLDatabase(object):

    def __init__(self, hosted_zone_id, table_name='records'):
        self.db_name = "{0}.db".format(hosted_zone_id)
        self.connection = sqlite3.connect(self.db_name)
        self.table_name = table_name
        self.table_struct = ['alias', 'weighted', 'weight', 'name', 'value', 'ttl', 'type']

    def close_connection(self):
        self.connection.commit()
        self.connection.close()
        self.connection = None

    def initialize_database(self):
        self._drop_table()
        self._create_table()

    def execute_query(self, query):
        if DEBUG:
            print(query)
        if self.connection:
            c = self.connection.cursor()
            c.execute(query)
            self.connection.commit()
        else:
            print('No connection to database')

    def _drop_table(self):
        query = "DROP TABLE IF EXISTS {table_name};".format(table_name=self.table_name)
        self.execute_query(query)

    def _create_table(self):
        query = "CREATE TABLE {table_name}(id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR, ttl INTEGER, alias BOOLEAN, weighted BOOLEAN, value VARCHAR, weight INTEGER, type VARCHAR)".format(table_name=self.table_name)
        self.execute_query(query)

    def upload_resource_records(self, resource_records):
        if self.connection:
            c = self.connection.cursor()

            for record in resource_records:
                if DEBUG:
                    print(record)

                if set(self.table_struct) == set(record.keys()):
                    query = ("""INSERT INTO {table_name} (alias, weighted, weight, name, value, ttl, type) 
                             VALUES ({alias}, {weighted}, {weight}, "{name}", "{value}", {ttl}, "{rtype}");""".format(
                                 table_name=self.table_name,
                                 alias=record['alias'],
                                 weighted=record['weighted'],
                                 weight=record['weight'],
                                 name=record['name'],
                                 value=record['value'],
                                 ttl=record['ttl'],
                                 rtype=record['type']))
                    if DEBUG:
                        print(query)

                    c.execute(query)
                else:
                    print('Possible malformed input, skipping row')

            self.connection.commit()
        else:
            print('No connection to database')
