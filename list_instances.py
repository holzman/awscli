#!/usr/bin/env python

import boto3
import datetime
from optparse import OptionParser
import time

parser = OptionParser()
parser.add_option("-a", "--all", dest="all_users", action="store_true", default=False,
                  help="list instances for all users")
parser.add_option("-r", "--running", dest="running", action="store_true", default=False,
                  help="list only running instances")
parser.add_option("-b", "--bare-ami", dest="bare_ami", action="store_true", default=False,
                  help="list bare AMI instead of aliases")

(options, args) = parser.parse_args()

now = datetime.datetime.utcnow()

ec2 = boto3.resource('ec2', region_name='us-west-2')
iam = boto3.resource('iam')
username = iam.CurrentUser().user_name

states = ['running', 'stopped', 'stopping', 'pending', 'terminating']
if options.running:
    states = ['running']

filters = [
    {'Name': 'instance-state-name', 'Values': states},
           {'Name':'tag:user', 'Values':['burt']},
           {'Name':'tag:type', 'Values':['cms-ml']}
           ]

if username == 'burt':
    options.all_users = True

if not options.all_users:
    filters.append({'Name':'tag:Name', 'Values':[username]})

instances = ec2.instances.filter(Filters=filters)
out1 = ''
out2 = ''

amimap = {'ami-0ee61876': 'FPGA HDK 1.3.3',
          'ami-72ed1e0a': 'DL 3.1  ',
          'ami-296e7850': 'DL 2.2  ',
          'ami-aa19d6d2': 'Cuda9 DL 1.0',
          'ami-c6ac34be': 'FPGA HDK 1.3.4',
          'ami-cfe89eb7': 'FPGA HDK 1.4.0',
          'ami-f275218a': 'DL 11.0 ',
}

if options.bare_ami:
    amimap = {}
for instance in instances:
    az = instance.placement['AvailabilityZone']
    tag_str = ''
    lifetime = '0'
    for tag in instance.tags:
        if tag.get('Key') == 'Name': tag_str = tag.get('Value')
        if tag.get('Key') == 'lifetime-mins': lifetime = tag.get('Value')

    lt = instance.launch_time.replace(tzinfo=None)
    lifetime = datetime.timedelta(minutes=int(lifetime))

    kill = (instance.state.get("Name") == 'running') and (now-lt) > lifetime

    outstr = "%s\t%15s\t%8s\t%s\t%s\t" % (instance.state.get("Name"), instance.public_ip_address, tag_str, instance.id, instance.instance_type)
    outstr += "%s\t" % amimap.get(instance.image_id, instance.image_id)
    outstr += "%s\t" % az
    outstr += "%s  %s\t\n" % (lt, lifetime)
    out1 += outstr



print "%s\t%s\t\t%8s\t%s\t\t\t%s" % ('State', 'IP', 'Owner', 'ID', 'type'),
print "\t\t%10s" % ('AMI'),
print "\t\t%s" % ('AZ'),
print "\t\t%s    %s\t\t\n" % ('Launch_time (UTC)', 'Lifetime')

print out1

