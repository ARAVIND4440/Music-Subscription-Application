# ============================================================
# Init Script 3: Load 2026a2_songs.json into the "music" table
# Required by Assessment 2 spec, Section "Database (DynamoDB)
# and Storage (S3) Initialisation", Item 3.
#
# Reads the 137 songs from 2026a2_songs.json (in the project root)
# and inserts each one into the music table created by Script 02.
#
# Schema recap (set up by Script 02):
#   PK: artist
#   SK: title_album_year (we build this composite during loading)
# ============================================================


# ---- Step 1: Imports ----
import json     # for reading the JSON dataset file
import boto3


# ---- Step 2: Configuration ----
REGION = "us-east-1"
TABLE_NAME = "music"
JSON_FILE = "2026a2_songs.json"   # in the project root folder


# ---- Step 3: Connect to DynamoDB ----
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


# ---- Step 4: Read the JSON file ----

def load_songs_from_json():
    print("Reading", JSON_FILE, "...")
    with open(JSON_FILE, "r") as file:
        data = json.load(file)

    # The JSON has a top-level "songs" key containing a list of song objects
    songs = data["songs"]
    print("Found", len(songs), "songs in the file.")
    return songs


# ---- Step 5: Build a database item from one JSON song ----
# The JSON has fields: title, artist, year, album, img_url
# We need to add the composite sort key "title_album_year" so DynamoDB
# can store every (artist, title, album, year) combination uniquely.

def build_music_item(song):
    composite_sk = song["title"] + "#" + song["album"] + "#" + song["year"]

    item = {
        "artist":           song["artist"],          # partition key
        "title_album_year": composite_sk,            # sort key
        "title":            song["title"],
        "year":             song["year"],
        "album":            song["album"],
        "image_url":        song["img_url"],
    }
    return item


# ---- Step 6: Insert all songs using batch_writer ----
# batch_writer automatically batches writes (up to 25 per request)
# and retries any failed items. Much faster than 137 individual put_item calls.

def insert_all_songs():
    songs = load_songs_from_json()

    print("Inserting", len(songs), "songs into '" + TABLE_NAME + "'...")
    inserted = 0

    with table.batch_writer() as batch:
        for song in songs:
            item = build_music_item(song)
            batch.put_item(Item=item)
            inserted = inserted + 1

    print("All", inserted, "songs inserted.")


# ---- Step 7: Verify the load by counting items in the table ----

def verify_count():
    # Scan with Select="COUNT" returns just the count, not the items.
    # This is appropriate here because we genuinely need a total row count
    # (one of the legitimate uses of Scan, per the lectorial).
    print("")
    print("Verifying total row count in DynamoDB...")
    response = table.scan(Select="COUNT")
    count = response["Count"]
    # Handle pagination if the table has more than one scan page
    while "LastEvaluatedKey" in response:
        response = table.scan(
            Select="COUNT",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        count = count + response["Count"]
    print("Rows in '" + TABLE_NAME + "' table:", count)


# ---- Step 8: Spot-check a few specific queries ----
# Run sample queries that mimic the marker's demo questions.

def spot_check():
    from boto3.dynamodb.conditions import Key

    print("")
    print("Spot check: Querying for all Taylor Swift songs (Query on PK)")
    response = table.query(
        KeyConditionExpression=Key("artist").eq("Taylor Swift"),
    )
    print("  Found", response["Count"], "Taylor Swift songs.")

    print("")
    print("Spot check: Querying for songs from 1974 (GSI YearArtistIndex)")
    response = table.query(
        IndexName="YearArtistIndex",
        KeyConditionExpression=Key("year").eq("1974"),
    )
    print("  Found", response["Count"], "songs from 1974.")


# ---- Main ----

print("=" * 60)
print("Init Script 3: Load music data into DynamoDB")
print("=" * 60)

insert_all_songs()
verify_count()
spot_check()

print("")
print("Done. Music table is populated.")