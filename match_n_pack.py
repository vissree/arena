#!/usr/bin/env python
#
# Author: vishnu@binaries.sg
# Purpose: Upload rotated log files to S3 bucket

import os
import fnmatch
import logging
import datetime
import argparse

from boto.s3.connection import S3Connection
from boto.s3.key import Key

#Parse the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("-b", help="S3 bucket name")
parser.add_argument("-d", help="Domainname")
parser.add_argument("-s", help="AWS Secret Key")
parser.add_argument("-a", help="AWS Access Key ID")
args = parser.parse_args()

s3_bucket = args.b
AWS_ACCESS_KEY_ID = args.a
AWS_SECRET_ACCESS_KEY = args.s
log_dir = '/var/log/nginx'
regex = args.d + '.access.log*.gz'

#Enable Logging for testing
log_file = "/tmp/match_n_pack.log"
logging.basicConfig(file_name=log_file, level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%a,%d %b %Y %H:%M:%S')


#Search for files matching regex in given directory and return file list
def create_file_list(log_dir, regex):
    file_list = []
    for file in os.listdir(log_dir):
        if fnmatch.fnmatch(file, regex):
            file_list.append(log_dir+'/'+file)
    return file_list


#Delete file from disk
def del_file_from_disk(file):
        if os.path.isfile(file):
            try:
                os.remove(file)
                logging.info("File %s removed successfully" % file)
            except Exception, e:
                logging.error("Error removing file %s, exception %r" % (file, e))


#Add date tag and upload files in the list to S3 bucket
def tag_n_push(file_list, tag):
    #Create S3 connection
    conn = S3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    #Create key object
    bucket = conn.get_bucket(s3_bucket)
    k = Key(bucket)
    for file in file_list:
        k.key = tag+os.path.basename(file)
        try:
            k.set_contents_from_filename(file)
            logging.info("Uploaded file %s to %s" % (file, k.key))
            del_file_from_disk(file)
        except Exception, e:
            logging.error("Error uploading log file %s, exception %r" % (file, e))
            #Rename file to *.failed
            os.rename(file, file+'.failed')


#Return today's date in required format
def get_date():
    return datetime.date.today().strftime('%Y/%m/%d/')


file_list = create_file_list(log_dir, regex)
tag = get_date()
tag_n_push(file_list, tag)
