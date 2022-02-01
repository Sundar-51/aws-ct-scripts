import boto3
import json
import csv

client = boto3.client('organizations')
response = client.list_accounts()
length=len(response["Accounts"])

def account_numbers():
    new_list=[]
    for iteration in range(length):
        acc_list=(response["Accounts"][(iteration)])
        first_pair=next(iter(acc_list.items()))
        accts=first_pair
        acct_id=accts[1]
        new_list.append(acct_id)
    return (new_list)
an=account_numbers()
print (an)

# open the file in the write mode
f = open('AccountList.csv', 'w')
# create the csv writer
writer = csv.writer(f)
# write a row to the csv file
writer.writerow(an)
# close the file
f.close()
