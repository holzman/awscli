#!/usr/bin/env python

import botocore
import boto3
from optparse import OptionParser
import sys
import time

ec2 = boto3.resource('ec2', region_name='us-west-2')
client = boto3.client('ec2', region_name='us-west-2')

filters = [{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']},
           {'Name':'tag:user', 'Values':['burt']},
           {'Name':'tag:type', 'Values':['cms-ml']},
           {'Name':'tag:Name', 'Values':['burt']}
           ]
instances = ec2.instances.filter(Filters=filters )

for instance in instances:
    print "Terminating instance %s (%s)" % (instance.id, instance.state.get('Name'))
    instance.terminate()
