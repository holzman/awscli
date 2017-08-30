#!/usr/bin/env python

import botocore
import boto3
from optparse import OptionParser
import sys
import time

parser = OptionParser()
parser.add_option("-u", "--user", dest="username",
                  help="user of the EC2 instance")
parser.add_option("-l", "--lifetime", dest="lifetime",
                  help="lifetime of the EC2 instance (in minutes) [DEFAULT: 120]",
                  default=1440)
parser.add_option("-n", "--no-alloc", dest="dontAllocateIP", default=False,
                  action="store_true", help="do not allocate fixed IP")

(options, args) = parser.parse_args()
username = options.username
lifetime = str(options.lifetime)

if not username:
    parser.error('Missing required parameter: user')

ec2 = boto3.resource('ec2', region_name='us-west-2')
client = boto3.client('ec2', region_name='us-west-2')

key_name = username
iam_instance_profile = 'S3_ReadOnly_CMS'
iisb = 'stop'

# tiny image for BH testing
image_id = 'ami-aa5ebdd2'
instance_type = 't2.nano'

# less tiny image for ML testing
image_id = 'ami-296e7850'
instance_type = 't2.micro'

filters = [{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']},
           {'Name':'tag:user', 'Values':['burt']},
           {'Name':'tag:Name', 'Values':[username]}
           ]
instances = ec2.instances.filter(Filters=filters )

for instance in instances:
    print "Warning: instance %s for %s already exists and is %s!" % (instance.id, username, instance.state.get('Name'))


startup_cmd = '''#!/bin/bash

echo "bazle" > /etc/foozle
'''

result = ec2.create_instances(ImageId = image_id,
                     InstanceType = instance_type,
                     IamInstanceProfile = {'Name' : iam_instance_profile},
                     KeyName = key_name,
                     UserData = startup_cmd,
                     MinCount = 1,
                     MaxCount = 1,
                     DryRun = False,
                     InstanceInitiatedShutdownBehavior=iisb,
                     TagSpecifications = [ {'ResourceType': 'instance',
                                            'Tags': [ {'Key': 'user', 'Value': 'burt'},
                                                      {'Key': 'type', 'Value': 'cms-ml'},
                                                      {'Key': 'Name', 'Value': username},
                                                      {'Key': 'lifetime-mins', 'Value': lifetime},
                                                      ] } ] )

for instance in result:
    print 'Instance %s created for %s' % (instance.id, username)

if not options.dontAllocateIP:
    address = client.allocate_address()
    if address:
        print 'Associating %s with %s' % (address.get('PublicIp'), instance.id),

        while 1: # sleep while instance starts
            try:
                sys.stdout.write('.')
                sys.stdout.flush()
                resp = client.associate_address(AllocationId=address.get('AllocationId'), InstanceId=instance.id)
                break
            except botocore.exceptions.ClientError: # client in pending state
                time.sleep(.5)
        print " done."
