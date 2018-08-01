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
                  help="lifetime of the EC2 instance in minutes [DEFAULT: 120]",
                  default=1440)
parser.add_option("-t", "--type", dest="instance_type", default="t2.micro", help="AWS instance type [DEFAULT: t2.micro]")

# FPGA AMI: ami-0ee61876
# default_ami='ami-296e7850' # AMI Deep Learning 2.2
# default_ami = 'ami-aa19d6d2' # AMI Cuda9 DL 1.0
default_ami='ami-72ed1e0a' # AMI Deep Learning 3.1

parser.add_option("-i", "--image", dest="image_id", default=default_ami, help="AWS AMI id [DEFAULT:%s]" % default_ami)

parser.add_option("-n", "--no-alloc", dest="dontAllocateIP", default=True,
                  action="store_true", help="do not allocate fixed IP")


(options, args) = parser.parse_args()
username = options.username
lifetime = str(options.lifetime)
instance_type = options.instance_type
image_id = options.image_id

if not username:
    parser.error('Missing required parameter: user')

ec2 = boto3.resource('ec2', region_name='us-west-2')
client = boto3.client('ec2', region_name='us-west-2')

key_name = username
iam_instance_profile = 'S3_ReadOnly_CMS'

if instance_type == 't2.2xlarge' or instance_type == 'f1.2xlarge':
    # assume this is for FPGA development and not ML
    iam_instance_profile = 'CMS_S3_AFI_ReadWrite'

iisb = 'stop'

# tiny image for BH testing
#image_id = 'ami-aa5ebdd2'
#instance_type = 't2.nano'

# less tiny image for ML testing
#image_id = 'ami-296e7850'
#instance_type = 't2.micro'

filters = [{'Name': 'instance-state-name', 'Values': ['running', 'stopped', 'stopping', 'pending']},
           {'Name':'tag:user', 'Values':['burt']},
           {'Name':'tag:Name', 'Values':[username]}
           ]
instances = ec2.instances.filter(Filters=filters )

for instance in instances:
    print "Warning: instance %s for %s already exists and is %s!" % (instance.id, username, instance.state.get('Name'))


startup_cmd = '''#!/bin/bash
pip install Keras --upgrade --no-deps
aws s3 cp s3://cms-sc17/s3fs /usr/local/bin/s3fs
chmod 755 /usr/local/bin/s3fs
yum -y install fuse fuse-devel emacs-nox
mkdir /cms-sc17
chown ec2-user /cms-sc17
echo 's3fs#cms-sc17 /cms-sc17         fuse _netdev,allow_other,uid=500,iam_role=auto,endpoint=us-west-2,umask=333 0 0' >> /etc/fstab
mount /cms-sc17
mkdir -p ~ec2-user/.config/matplotlib
echo "backend:Agg" > ~ec2-user/.config/matplotlib/matplotlibrc
chown -R ec2-user ~ec2-user/.config
echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsS2eIutvUVEnIWw7Z28EzCcmBBYgDB3Pzkgvdxnn47VUxhE7DxSIoNZyDkShBnItfHoZVWlMc86FZMYTX/L4Qg63lgT9lYxLf991L6/zWT2DFs/xTe1kX8p08jB38VBGmROVmBFCfkYCRx0VgJL2REI+UKjQmZYvzBJ7BnRMdCgsfnQT8wI+AymTuCHUdKYBRlCPaZCee8v+s9qpbO2bhIzCiB/ufmzaguxu9AzLGt2GXm9eETpWl9Gs7BeDQzl03xXj6wQaB6BsnLdJ+9GGQIqEcoOPp0wntwV+TxI1ze0iAclqkTlDzCkwP25e/vU76hoSbndkHGi9YIg79ouDKQ== burt" >> ~ec2-user/.ssh/authorized_keys
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
