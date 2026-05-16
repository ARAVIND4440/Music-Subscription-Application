import boto3
from botocore.exceptions import ClientError


REGION = "us-east-1"
TABLE_NAME = "subscriptions"


dynamodb = boto3.resource("dynamodb", region_name=REGION)


def table_exists(name):

    client = boto3.client("dynamodb", region_name=REGION)

    try:
        client.describe_table(TableName=name)
        return True

    except ClientError as error:
        if error.response["Error"]["Code"] == "ResourceNotFoundException":
            return False

        raise


def create_subscription_table():

    if table_exists(TABLE_NAME):
        print("Table '" + TABLE_NAME + "' already exists. Skipping creation.")
        return dynamodb.Table(TABLE_NAME)

    print("Creating table '" + TABLE_NAME + "'...")

    table = dynamodb.create_table(
        TableName=TABLE_NAME,

        AttributeDefinitions=[
            {
                "AttributeName": "email",
                "AttributeType": "S"
            },
            {
                "AttributeName": "music_id",
                "AttributeType": "S"
            }
        ],

        KeySchema=[
            {
                "AttributeName": "email",
                "KeyType": "HASH"
            },
            {
                "AttributeName": "music_id",
                "KeyType": "RANGE"
            }
        ],

        BillingMode="PAY_PER_REQUEST"
    )

    table.wait_until_exists()

    print("Table '" + TABLE_NAME + "' is ready.")

    return table


print("=" * 60)
print("Create subscriptions table")
print("=" * 60)

create_subscription_table()

print("")
print("Done. Subscriptions table is ready.")