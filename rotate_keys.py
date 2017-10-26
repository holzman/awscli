#!/usr/bin/env python

import botocore
import boto3
import os
import stat
import sys
import ConfigParser as cp

iam = boto3.client('iam')

profile = os.getenv('AWS_PROFILE', 'default')
config_file = '%s/.aws/credentials' % os.path.expanduser('~')
s = os.stat(config_file).st_mode
if (s & stat.S_IROTH) or (s & stat.S_IRGRP):
    print "Error: %s must be readable only by owner" % config_file
    sys.exit(1)
config = cp.RawConfigParser()
config.read(config_file)

username = iam.get_user()['User']['UserName']
response = iam.create_access_key(UserName=username)
new_access_key_id = response['AccessKey']['AccessKeyId']
new_secret_key_id = response['AccessKey']['SecretAccessKey']

old_access_key_id  = config.get(profile, 'aws_access_key_id')
config.set(profile, 'aws_access_key_id', new_access_key_id)
config.set(profile, 'aws_secret_access_key', new_secret_key_id)

f = open(config_file, 'w')
config.write(f)

iam.delete_access_key(AccessKeyId=old_access_key_id, UserName=username)
