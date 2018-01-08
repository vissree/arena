from r53_sqlite_database import R53SQLDatabase
from ec2_aws_client import EC2AWSClient
import argparse
import re

DEBUG = False

def add_all_parent_records(result, filter_type):
    name, value, rtype, ttl = result
    output = ec2.search_instance(filter_type, value, verbose=True)

    if not output:
        query = "INSERT INTO {table_name} (name, value, type, ttl) VALUES (?, ?, ?, ?);".format(table_name=table_name_to_del)
        if DEBUG:
            print("{0} : {1} : {2}".format(name, rtype, value))
        r53_db.execute_query(query, (name, value, rtype, ttl))

        # Get all parent records
        records_to_delete = r53_db.get_parent_records(name)

        if records_to_delete:
            for name, value, rtype, ttl, weighted, weight in records_to_delete:
                if DEBUG:
                    print("{0} : {1} : {2}".format(name, rtype, value))
                r53_db.execute_query(query, (name, value, rtype, ttl))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a simple database of Route53 records')
    parser.add_argument('--access-key-id', '-a', dest='access_key_id', required=False, default=None, help='AWS Access Key Id')
    parser.add_argument('--secret-access-key', '-k', dest='secret_access_key', required=False, default=None, help='AWS Secret Access Key')
    parser.add_argument('--table', '-t', dest='table_name', required=False, default='records', help='Table name in the database')
    parser.add_argument('--hosted-zone-id', '-z', dest='hosted_zone_id', required=True, help='Route53 hosted zone ID')
    args = parser.parse_args()

    if DEBUG:
        print("Access key: {0}\nSecret key: {1}\nHosted zone id: {2}\nTable Name: {3}".format(args.access_key_id, args.secret_access_key, args.hosted_zone_id, args.table_name))

    table_name = args.table_name
    table_name_to_del = "{0}_to_del".format(table_name)

    # Create all connection objects
    r53_db = R53SQLDatabase(args.hosted_zone_id)
    ec2 = EC2AWSClient(aws_access_key_id=args.access_key_id, aws_secret_access_key=args.secret_access_key)

    r53_db.initialize_delete_db()  # Create records_to_del table

    for rtype in ['A', 'CNAME']:
        query = "SELECT name, value, type, ttl FROM {table_name} WHERE type='{rtype}' and alias=0;".format(table_name=table_name, rtype=rtype)
        results = r53_db.execute_query(query)

        if rtype == 'A':
            for result in results:
                add_all_parent_records(result, 'ip')

        if rtype == 'CNAME':
            for result in results:
                name, value, rtype, ttl = result
                if re.search(r'ec2(-\d{1,3}){4}\.compute-1\.amazonaws\.com\.?', value):
                    add_all_parent_records(result, 'cname')
                elif re.search(r'ip(-\d{1,3}){4}\.ec2\.internal\.?', value):
                    add_all_parent_records(result, 'private_dns')

    r53_db.close_connection()
