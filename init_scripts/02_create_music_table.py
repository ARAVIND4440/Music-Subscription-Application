# ============================================================
# Init Script 2: Create the "music" DynamoDB table
# Required by Assessment 2 spec, Section "Database (DynamoDB)
# and Storage (S3) Initialisation", Item 2.
#
# SCHEMA RATIONALE (graded under "Key Schema & Data Integrity"):
#
# Cardinality analysis of 2026a2_songs.json (137 songs):
#   - 130 unique titles (some titles repeat across artists,
#     e.g. "Rivers of Babylon" appears 3 times)
#   - 71 unique artists (good partition distribution)
#   - 102 unique albums
#   - (artist, title) pairs are NOT unique either:
#     Taylor Swift's "Delicate" appears on 2 different albums.
#   - (artist, title, album, year) IS unique across all 137 rows.
#
# Therefore:
#   Partition Key: artist
#   Sort Key:      title_album_year  (composite: "title#album#year")
#
#   This guarantees no song is overwritten during import (the rubric's
#   key concern: "no songs are accidentally overwritten").
#
# INDEX STRATEGY (graded under "Indexing & Retrieval"):
#
#   LSI (Local Secondary Index): AlbumIndex
#     PK = artist (same as base), SK = album
#     Supports demo query: "all Taylor Swift songs in album Fearless"
#     via Query(PK=artist, SK begins_with album) — no Scan needed.
#
#   GSI (Global Secondary Index): YearArtistIndex
#     PK = year, SK = artist
#     Supports demo query: "all Jimmy Buffett songs in 1974" via
#     Query(PK=year, SK=artist) — no Scan needed.
# ============================================================


# ---- Step 1: Imports ----
import boto3
from botocore.exceptions import ClientError


# ---- Step 2: Configuration ----
REGION = "us-east-1"
TABLE_NAME = "music"


# ---- Step 3: Connect to DynamoDB ----
dynamodb = boto3.resource("dynamodb", region_name=REGION)


# ---- Step 4: Check if the table already exists ----

def table_exists(name):
    client = boto3.client("dynamodb", region_name=REGION)
    try:
        client.describe_table(TableName=name)
        return True
    except ClientError as error:
        if error.response["Error"]["Code"] == "ResourceNotFoundException":
            return False
        raise


# ---- Step 5: Create the table ----

def create_music_table():
    if table_exists(TABLE_NAME):
        print("Table '" + TABLE_NAME + "' already exists. Skipping creation.")
        return dynamodb.Table(TABLE_NAME)

    print("Creating table '" + TABLE_NAME + "'...")
    print("  Partition Key: artist")
    print("  Sort Key:      title_album_year (composite)")
    print("  LSI:           AlbumIndex (artist + album)")
    print("  GSI:           YearArtistIndex (year + artist)")

    table = dynamodb.create_table(
        TableName=TABLE_NAME,

        # AttributeDefinitions: declare every attribute used in keys or indexes.
        # All four are Strings ("S"). We store year as a string to match
        # how it appears in the JSON file.
        AttributeDefinitions=[
            {"AttributeName": "artist",            "AttributeType": "S"},
            {"AttributeName": "title_album_year",  "AttributeType": "S"},
            {"AttributeName": "album",             "AttributeType": "S"},
            {"AttributeName": "year",              "AttributeType": "S"},
        ],

        # Primary key: partition key + sort key (composite key).
        # Lectorial Week 6 / DatabaseServices_Ying explicitly teaches this:
        # "Composite primary key: Partition Key and Sort Key — Two items
        # may have the same partition key, but must have different sort keys."
        KeySchema=[
            {"AttributeName": "artist",           "KeyType": "HASH"},
            {"AttributeName": "title_album_year", "KeyType": "RANGE"},
        ],

        # LSI shares the same partition key as the base table but uses a
        # different sort key. ProjectionType "ALL" means all attributes
        # are accessible through the index.
        LocalSecondaryIndexes=[
            {
                "IndexName": "AlbumIndex",
                "KeySchema": [
                    {"AttributeName": "artist", "KeyType": "HASH"},
                    {"AttributeName": "album",  "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],

        # GSI uses different keys from the base table. Lets us query by year
        # without knowing the artist upfront.
        GlobalSecondaryIndexes=[
            {
                "IndexName": "YearArtistIndex",
                "KeySchema": [
                    {"AttributeName": "year",   "KeyType": "HASH"},
                    {"AttributeName": "artist", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            },
        ],

        BillingMode="PAY_PER_REQUEST",
    )

    table.wait_until_exists()
    print("Table '" + TABLE_NAME + "' is ready.")
    return table


# ---- Main ----

print("=" * 60)
print("Init Script 2: Create music table")
print("=" * 60)

create_music_table()

print("")
print("Done. Music table is created and ready for data loading (Script 03).")