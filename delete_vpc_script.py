from __future__ import print_function
import boto3
import sys
import json


VERBOSE = 1
# Create session using your current creds
account_number=665879447504
boto_sts=boto3.client('sts')

stsresponse = boto_sts.assume_role(
    RoleArn= f"arn:aws:iam::{account_number}:role/AWSControlTowerExecution",
    RoleSessionName='newsession'
)

# Save the details from assumed role into vars
newsession_id = stsresponse["Credentials"]["AccessKeyId"]
newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
newsession_token = stsresponse["Credentials"]["SessionToken"]

ec2_assumed_client = boto3.client(
    'ec2',
    aws_access_key_id=newsession_id,
    aws_secret_access_key=newsession_key,
    aws_session_token=newsession_token
)
ec2_assumed_resource = boto3.resource(
    'ec2',
    aws_access_key_id=newsession_id,
    aws_secret_access_key=newsession_key,
    aws_session_token=newsession_token
)

def get_regions(ec2_assumed_client):
    reg_list = []
    regions = ec2_assumed_client.describe_regions()
    data_str = json.dumps(regions)
    resp = json.loads(data_str)
    region_str = json.dumps(resp['Regions'])
    region = json.loads(region_str)
    for reg in region:
        reg_list.append(reg['RegionName'])
    return reg_list

def get_default_vpcs(ec2_assumed_client):
    vpc_list = []
    vpcs = ec2_assumed_client.describe_vpcs(
        Filters=[
            {
                'Name': 'isDefault',
                'Values': [
                    'true',
                ],
            },
        ]
    )
    vpcs_str = json.dumps(vpcs)
    resp = json.loads(vpcs_str)
    data = json.dumps(resp['Vpcs'])
    vpcs = json.loads(data)
    for vpc in vpcs:
        vpc_list.append(vpc['VpcId'])
    return vpc_list

def del_igw(ec2, vpcid): 
    vpc_resource = ec2.Vpc(vpcid)
    igws = vpc_resource.internet_gateways.all()
    if igws:
        for igw in igws:
            try:
                print("Detaching and Removing igw-id: ", igw.id) if (VERBOSE == 1) else ""
                igw.detach_from_vpc(
                    VpcId=vpcid
                )
                igw.delete(
                    # DryRun=True
                )
            except boto3.exceptions.Boto3Error as e:
                print(e)

def del_sub(ec2, vpcid):
    vpc_resource = ec2.Vpc(vpcid)
    subnets = vpc_resource.subnets.all()
    default_subnets = [ec2.Subnet(subnet.id) for subnet in subnets if subnet.default_for_az]

    if default_subnets:
        try:
            for sub in default_subnets:
                print("Removing sub-id: ", sub.id) if (VERBOSE == 1) else ""
                sub.delete(
                )
        except boto3.exceptions.Boto3Error as e:
            print(e)

def del_rtb(ec2, vpcid):
    vpc_resource = ec2.Vpc(vpcid)
    rtbs = vpc_resource.route_tables.all()
    if rtbs:
        try:
            for rtb in rtbs:
                assoc_attr = [rtb.associations_attribute for rtb in rtbs]
                if [rtb_ass[0]['RouteTableId'] for rtb_ass in assoc_attr if rtb_ass[0]['Main'] == True]:
                    print(rtb.id + " is the main route table, continue...")
                    continue
                print("Removing rtb-id: ", rtb.id) if (VERBOSE == 1) else ""
                table = ec2.RouteTable(rtb.id)
                
                table.delete(
                )
        except boto3.exceptions.Boto3Error as e:
            print(e)

def del_acl(ec2, vpcid):
    vpc_resource = ec2.Vpc(vpcid)
    acls = vpc_resource.network_acls.all()

    if acls:
        try:
            for acl in acls:
                if acl.is_default:
                    print(acl.id + " is the default NACL, continue...")
                    continue
                print("Removing acl-id: ", acl.id) if (VERBOSE == 1) else ""
                acl.delete(
                )
        except boto3.exceptions.Boto3Error as e:
            print(e)

def del_sgp(ec2, vpcid):
    vpc_resource = ec2.Vpc(vpcid)
    sgps = vpc_resource.security_groups.all()
    if sgps:
        try:
            for sg in sgps:
                if sg.group_name == 'default':
                    print(sg.id + " is the default security group, continue...")
                    continue
                print("Removing sg-id: ", sg.id) if (VERBOSE == 1) else ""
                sg.delete(
                    # DryRun=True
                )
        except boto3.exceptions.Boto3Error as e:
            print(e)

def del_vpc(ec2, vpcid):
    #Delete the VPC 
    vpc_resource = ec2.Vpc(vpcid)
    print ("The list of vpc's are: ",vpc_resource)
    try:
        print("Removing vpc-id: ", vpc_resource.id)
        vpc_resource.delete(
            # DryRun=True
        )
    except boto3.exceptions.Boto3Error as e:
        print(e)
        print("Please remove dependencies and delete VPC manually.")

def main(keyid, secret):
    boto_sts=boto3.client('sts')
    stsresponse = boto_sts.assume_role(
        RoleArn= f"arn:aws:iam::{account_number}:role/AWSControlTowerExecution",
        RoleSessionName='newsession'
    )
    newsession_id = stsresponse["Credentials"]["AccessKeyId"]
    newsession_key = stsresponse["Credentials"]["SecretAccessKey"]
    newsession_token = stsresponse["Credentials"]["SessionToken"]
    print (newsession_id)
    ec2_assumed_client = boto3.client(
        'ec2',
        aws_access_key_id=newsession_id,
        aws_secret_access_key=newsession_key,
        aws_session_token=newsession_token
    )
    print (newsession_id)
    ec2 = boto3.resource(
        'ec2',
        aws_access_key_id=newsession_id,
        aws_secret_access_key=newsession_key,
        aws_session_token=newsession_token
    )
    regions = get_regions(ec2_assumed_client)
    for region in regions:
        try:
            ec2_assumed_client = boto3.client('ec2',
                region_name=region,
                aws_access_key_id=newsession_id,
                aws_secret_access_key=newsession_key,
                aws_session_token=newsession_token)
            ec2 = boto3.resource('ec2',
                region_name=region,
                aws_access_key_id=newsession_id,
                aws_secret_access_key=newsession_key,
                aws_session_token=newsession_token)
            vpcs = get_default_vpcs(ec2_assumed_client)
        except boto3.exceptions.Boto3Error as e:
            print(e)
            exit(1)
        else:
            for vpc in vpcs:
                print("\n" + "\n" + "REGION:" + region + "\n" + "VPC Id:" + vpc)
                del_igw(ec2, vpc)
                del_sub(ec2, vpc)
                del_rtb(ec2, vpc)
                del_acl(ec2, vpc)
                del_sgp(ec2, vpc)
                del_vpc(ec2, vpc)


if __name__ == "__main__":
    main(keyid='XXXX', secret='XXXX')
