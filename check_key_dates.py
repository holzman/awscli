#!/usr/bin/env python

import botocore
import boto3
import datetime
import pytz

iam = boto3.client('iam')

group = iam.get_group(GroupName='AWS-ML')
usernames = [x['UserName'] for x in group.get('Users')]

while group['IsTruncated']:
    marker = group['Marker']
    group = iam.get_group(GroupName='AWS-ML', Marker=marker)
    usernames += [x['UserName'] for x in group.get('Users')]

now = datetime.datetime.now()

for user in usernames:
    akeys = iam.list_access_keys(UserName=user)  ['AccessKeyMetadata']
    for akey in akeys:
        then = akey['CreateDate']
        diff = now.replace(tzinfo=pytz.timezone('US/Central')) - then.replace(tzinfo=pytz.UTC)

        print "%7s days\t%8s\t%10s\t%s" % (diff.days, akey['Status'], user, akey['AccessKeyId'])

