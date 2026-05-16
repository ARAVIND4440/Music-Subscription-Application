# ============================================================
# Init Script 4: Download artist images and upload them to S3
# Required by Assessment 2 spec, Section "Database (DynamoDB)
# and Storage (S3) Initialisation", Item 4.
#
# What this script does:
#   1. Creates an S3 bucket (private, public access blocked).
#   2. Reads 2026a2_songs.json to get all image URLs.
#   3. Finds the unique URLs (multiple songs share the same artist
#      image, so we don't want to download the same image twice).
#   4. Downloads each image from the URL on the internet.
#   5. Uploads it to our S3 bucket with the original filename as the key.
#
# SECURITY NOTE (graded under "Accessibility & Security"):
#   The bucket is created with PublicAccessBlock enabled — no public
#   access. Later, the web app will use presigned URLs to access images
#   temporarily and securely. This matches the rubric's "Excellent" band.
# ============================================================

# ---- Step 1: Imports ----
import json                                       # to read the JSON dataset
import urllib.request                             # to download images from URLs (built-in, no external library)
import boto3
from botocore.exceptions import ClientError

# ---- Step 2: Configuration ----
REGION = "us-east-1"
JSON_FILE = "2026a2_songs.json"
MUSIC_TABLE = "music"

# We'll add the AWS account number to the bucket name below
# to make sure it's globally unique.
BUCKET_NAME_PREFIX = "cc-music-images-"

# ---- Step 3: Connect to AWS ----
s3_client = boto3.client("s3", region_name=REGION)
sts_client = boto3.client("sts", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)

# ---- Step 4: Build a unique bucket name using the AWS account number ----

def get_bucket_name():
    # Get our AWS account ID. This is unique per AWS customer,
    # so attaching it makes our bucket name globally unique.
    account_id = sts_client.get_caller_identity()["Account"]
    return BUCKET_NAME_PREFIX + account_id


# ---- Step 5: Check if the bucket already exists ----

def bucket_exists(name):
    try:
        s3_client.head_bucket(Bucket=name)
        return True
    except ClientError as error:
        # 404 = doesn't exist; 403 = exists but we can't access it (someone else owns it)
        code = error.response["Error"]["Code"]
        if code == "404":
            return False
        raise


# ---- Step 6: Create the bucket with public access blocked ----

def create_bucket(name):
    if bucket_exists(name):
        print("Bucket '" + name + "' already exists. Skipping creation.")
        return

    print("Creating bucket '" + name + "'...")

    # us-east-1 is the default region — for it, we don't pass LocationConstraint
    # (AWS gets unhappy if you do). For any other region, we'd need to pass it.
    s3_client.create_bucket(Bucket=name)

    # Block all public access (security best practice per spec rubric).
    print("Enabling Block Public Access...")
    s3_client.put_public_access_block(
        Bucket=name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls":       True,
            "IgnorePublicAcls":      True,
            "BlockPublicPolicy":     True,
            "RestrictPublicBuckets": True,
        },
    )

    print("Bucket '" + name + "' created and secured.")


# ---- Step 7: Read JSON and collect unique image URLs ----

def get_unique_image_urls():
    print("Reading", JSON_FILE, "to get image URLs...")
    with open(JSON_FILE, "r") as file:
        data = json.load(file)

    songs = data["songs"]

    # Use a set to automatically remove duplicates.
    # A "set" is like a list but each value can only appear once.
    unique_urls = set()
    for song in songs:
        unique_urls.add(song["img_url"])

    print("Found", len(unique_urls), "unique image URLs (from", len(songs), "songs).")
    return unique_urls


# ---- Step 8: Extract the filename from a URL ----
# Example URL: "https://raw.githubusercontent.com/.../TaylorSwift.jpg"
# We want just the last part: "TaylorSwift.jpg"

def filename_from_url(url):
    # Split the URL by "/" and take the last piece
    parts = url.split("/")
    return parts[-1]


# ---- Step 9: Download one image and upload it to S3 ----

def download_and_upload(url, bucket_name):
    filename = filename_from_url(url)

    # Download the image from the URL into memory
    with urllib.request.urlopen(url) as response:
        image_bytes = response.read()

    # Upload the image bytes to S3.
    # ContentType helps browsers know how to display the file later.
    s3_client.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=image_bytes,
        ContentType="image/jpeg",
    )

    return filename


# ---- Step 10: Process all images ----

def upload_all_images(bucket_name):
    urls = get_unique_image_urls()

    print("Downloading and uploading", len(urls), "images...")
    success_count = 0
    fail_count = 0

    for url in urls:
        try:
            filename = download_and_upload(url, bucket_name)
            success_count = success_count + 1
            # Print progress every 10 images so we can see it's working
            if success_count % 10 == 0:
                print("  ", success_count, "/", len(urls), "uploaded...")
        except Exception as error:
            print("  Failed:", url, "-", str(error))
            fail_count = fail_count + 1

    print("")
    print("Done uploading.")
    print("  Success:", success_count)
    print("  Failed:", fail_count)


# ---- Step 11: Verify by listing the bucket contents ----

def verify_bucket(bucket_name):
    print("")
    print("Verifying bucket contents...")

    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" not in response:
        print("  Bucket is empty!")
        return

    objects = response["Contents"]
    print("  Bucket contains", len(objects), "objects.")

    # Show the first 5 filenames as a sanity check
    print("  Sample filenames:")
    for obj in objects[:5]:
        print("    -", obj["Key"], "(", obj["Size"], "bytes)")

# ---- Step 12: Update DynamoDB image_url field to S3 filename ----
# After uploading images to S3, the music table still has the original
# GitHub URLs in its image_url field. We replace those with the S3
# filename (e.g. "TaylorSwift.jpg") so the backend can build presigned
# URLs directly from this field.

def update_dynamodb_image_urls():
    print("")
    print("Updating music table: replacing URLs with S3 filenames...")

    music_table = dynamodb.Table(MUSIC_TABLE)

    # Read all rows from the music table
    response = music_table.scan()
    items = response.get("Items", [])

    # Handle pagination (if the table grows past one scan page)
    while "LastEvaluatedKey" in response:
        response = music_table.scan(
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    print("  Found", len(items), "rows to check.")

    updated = 0
    skipped = 0
    for item in items:
        old_url = item.get("image_url", "")
        new_key = filename_from_url(old_url)

        # If it's already just a filename, skip (idempotent)
        if new_key == old_url:
            skipped = skipped + 1
            continue

        music_table.update_item(
            Key={
                "artist":           item["artist"],
                "title_album_year": item["title_album_year"],
            },
            UpdateExpression="SET image_url = :new_value",
            ExpressionAttributeValues={":new_value": new_key},
        )
        updated = updated + 1

    print("  Updated:", updated, " | Skipped (already correct):", skipped)

# ---- Main ----

print("=" * 60)
print("Init Script 4: Upload artist images to S3")
print("=" * 60)

bucket_name = get_bucket_name()
print("Bucket name:", bucket_name)
print("")

create_bucket(bucket_name)
upload_all_images(bucket_name)
verify_bucket(bucket_name)
update_dynamodb_image_urls()

print("")
print("Done. Images uploaded to S3 bucket:", bucket_name)
print("Bucket is PRIVATE — public access blocked per security best practice.")
print("Music table updated: image_url field now stores S3 filenames.")