from botocore.exceptions import ClientError
from botocore.exceptions import ParamValidationError 
import boto3
import sqlite3
import argparse

DEBUG = True

class R53AWSClient(object):

    def __init__(self, hosted_zone_id, aws_access_key_id=None, aws_secret_access_key=None):
        try:
            self.rc = boto3.client('route53', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        except ClientError as e:
            print('Failed to connect to Route53')
            print("{error}".format(error=e))
            self.rc = None

        self.hosted_zone_id = hosted_zone_id
        self.resource_records = []

    def _get_remaining_record_set(self, next_record_name=None, next_record_type=None):
        """http://boto3.readthedocs.io/en/latest/reference/services/route53.html#Route53.Client.list_resource_record_sets"""
        if self.rc:
            try:
                if next_record_type and next_record_name:
                    response = self.rc.list_resource_record_sets(
                            HostedZoneId = self.hosted_zone_id,
                            StartRecordName = next_record_name,
                            StartRecordType = next_record_type,
                            MaxItems = '100'
                            )
                else:
                    response = self.rc.list_resource_record_sets(
                            HostedZoneId = self.hosted_zone_id,
                            MaxItems = '100'
                            )
            except ClientError as e:
                print('Failed to get resource record list')
                print("{error}".format(error=e))
                response = None

            except ParamValidationError as e:
                print('Invalid inputs to list resource records')
                print("{error}".format(error=e))
                response = None
        else:
            response = None

        return response

    def _format_resource_record_set(self, resource_record_set):
        for record in resource_record_set:
            if DEBUG:
                print(record)

            alias = 0 # Boolean represented as 0 and 1 in sqlite
            weighted = 0
            weight = -1
            ttl = 0
            name = record['Name']
            rtype = record['Type']
            values = []

            if 'Weight' in record.keys():
                weighted = 1
                weight = record['Weight']

            if 'AliasTarget' in record.keys():
                alias = 1
                values.append(record['AliasTarget']['DNSName'])
            else:
                ttl = record['TTL']
                for r in record['ResourceRecords']:
                    values.append(r['Value'].strip('"'))

            # Append data to resource_records
            for value in values:
                row = {
                    'alias': alias,
                    'weighted': weighted,
                    'weight': weight,
                    'name': name,
                    'value': value,
                    'ttl': ttl,
                    'type': rtype
                    }

                if DEBUG:
                    print(row)

                self.resource_records.append(row)

    def get_all_resource_records(self):
        is_truncated = True
        next_record_name = None
        next_record_type = None

        while is_truncated:
            if DEBUG:
                print("{0}, {1}, {2}".format(is_truncated, next_record_name, next_record_type))

            response = self._get_remaining_record_set(next_record_name, next_record_type)

            if response:
                self._format_resource_record_set(response['ResourceRecordSets'])
                is_truncated = response['IsTruncated']

                if is_truncated:
                    next_record_name = response['NextRecordName']
                    next_record_type = response['NextRecordType']
            else:
                is_truncated = False


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a simple database of Route53 records')
    parser.add_argument('--access-key-id', '-a', dest='access_key_id', required=False, default=None, help='AWS Access Key Id')
    parser.add_argument('--secret-access-key', '-k', dest='secret_access_key', required=False, default=None, help='AWS Secret Access Key')
    parser.add_argument('--hosted-zone-id', '-z', dest='hosted_zone_id', required=True, help='Route53 hosted zone ID')
    args = parser.parse_args()

    if DEBUG:
        print("Access key: {0}\nSecret key: {1}\nHosted zone id: {2}".format(args.access_key_id, args.secret_access_key, args.hosted_zone_id))

    r53 = R53AWSClient(args.hosted_zone_id, aws_access_key_id=args.access_key_id, aws_secret_access_key=args.secret_access_key)
    
    r53.get_all_resource_records()

    r53_db = R53SQLDatabase(args.hosted_zone_id)
    r53_db.initialize_database()

    r53_db.upload_resource_records(r53.resource_records)
    r53_db.close_connection()
