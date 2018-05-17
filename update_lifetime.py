#!/usr/bin/env python

import boto3
import datetime
from optparse import OptionParser
import time

parser = OptionParser()
parser.add_option("-i", "--instance-id", dest="instance",
                  help="instance ID")

parser.add_option("-l", "--lifetime", dest="lifetime",
                  help="lifetime of the EC2 instance in minutes")

(options, args) = parser.parse_args()
instance = options.instance
lifetime = str(options.lifetime)

if not instance:
    parser.error('Missing required parameter: instance')

if not lifetime:
    parser.error('Missing required parameter: lifetime')

now = datetime.datetime.utcnow()

ec2 = boto3.client('ec2', region_name='us-west-2')
ec2.create_tags(
    Resources=[instance],
    Tags=[{'Key': 'lifetime-mins','Value': lifetime}]
)
