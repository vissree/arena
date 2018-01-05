from botocore.exceptions import ClientError
import boto3
import ipaddress

REGIONS = ['us-east-1', 'us-west-1', 'eu-west-1', 'eu-central-1', 'ap-southeast-1', 'ap-northeast-1']

class EC2AWSClient(object):

    def __init__(self, aws_secret_access_key=None, aws_access_key_id=None):
        self.connection = {}
        for region in REGIONS:
            try:
                self.connection_pool[region] = boto3.client('ec2', region_name=region, aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
            except ClientError as e:
                print("Error getting a connection for {region}".format(region=region))
                print("{error}".format(error=e))

    def search_instance_by_ip(self, ip, verbose=False):
        filter_key = 'private-ip-address' if ipaddress.ip_address(ip).is_private else 'ip-address'
        reservation = None
        found = False
        for region in self.connection:
            response = self.connection[region].describe_instances(
                        Filters=[{
                            'Name': filter_key,
                            'Values': [ip]
                            }]
                        )

            if len(response['Reservations'] > 0):
                found = True
                reservation = response['Reservations'][0] # Assuming that the reservation will be unique
                break

        if verbose and found:
            instance_id = reservation['Instances'][0]['InstanceId']
            instance_name = None

            for tag in reservation['Instances'][0]['Tags']:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                    break

            output = {'region': region, 'instance_id': instance_id, 'name': instance_name}
            return output
        else:
            return found
