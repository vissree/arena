from r53_sqlite_database import R53SQLDatabase
from r53_aws_client import R53AWSClient
from ec2_aws_client import EC2AWSClient
import argparse

DEBUG = True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a simple database of Route53 records')
    parser.add_argument('--access-key-id', '-a', dest='access_key_id', required=False, default=None, help='AWS Access Key Id')
    parser.add_argument('--secret-access-key', '-k', dest='secret_access_key', required=False, default=None, help='AWS Secret Access Key')
    parser.add_argument('--hosted-zone-id', '-z', dest='hosted_zone_id', required=True, help='Route53 hosted zone ID')
    args = parser.parse_args()

    if DEBUG:
        print("Access key: {0}\nSecret key: {1}\nHosted zone id: {2}".format(args.access_key_id, args.secret_access_key, args.hosted_zone_id))

    # Create all connection objects
    r53 = R53AWSClient(args.hosted_zone_id, aws_access_key_id=args.access_key_id, aws_secret_access_key=args.secret_access_key)
    r53_db = R53SQLDatabase(args.hosted_zone_id)
    ec2 = EC2AWSClient(aws_access_key_id=args.access_key_id, aws_secret_access_key=args.secret_access_key)

    # Fetch all resource records for the zone
    r53.get_all_resource_records()

    r53_db.initialize_database() # Create records table
    r53_db.initialize_delete_db()  # Create records_to_del table

    # Populate resource records database
    r53_db.upload_resource_records(r53.resource_records)

    # Get all the A records and work backwards
    #
    query = "SELECT name, value FROM records WHERE type='A' and alias=0;"
    results = r53_db.execute_query(query)


    for row in results:
        name, ip = row
        output = ec2.search_instance_by_ip(ip, verbose=True)

        if not output:
            query = "INSERT INTO records_to_del (name, value, type) VALUES (?, ?, ?);"
            r53_db.execute_query(query, (name, ip, 'A'))

            # Get all parent records
            records_to_delete = r53_db.get_parent_records(name)

            for row in records_to_delete:
                name, value, rtype = row 
                if DEBUG:
                    print("{0} : {1} : {2}".format(name, rtype, value))
                    r53_db.execute_query(query, (name, value, rtype))

    r53_db.close_connection()
