from flask import Flask, jsonify, request
from flask_cors import CORS
from boto3.dynamodb.conditions import Key, Attr
import boto3

app = Flask(__name__)

# ======================================================
# CORS CONFIGURATION
# ======================================================

CORS(app, resources={
    r"/*": {
        "origins": [
            "http://music-app-frontend-unique.s3-website-us-east-1.amazonaws.com"
        ],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


# ======================================================
# AWS CONFIGURATION
# ======================================================

REGION = "us-east-1"

dynamodb = boto3.resource(
    "dynamodb",
    region_name=REGION
)

login_table = dynamodb.Table("login")
music_table = dynamodb.Table("music")
subscriptions_table = dynamodb.Table("subscriptions")

s3_client = boto3.client("s3", region_name=REGION)

S3_BUCKET_NAME = "cc-music-images-993022968106"


# ======================================================
# HELPER: Add presigned image URL
# ======================================================

def add_presigned_image_url(item):
    image_key = item.get("image_url")

    if image_key:
        presigned_url = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": image_key
            },
            ExpiresIn=3600
        )
        item["image_display_url"] = presigned_url
    else:
        item["image_display_url"] = ""

    return item


# ======================================================
# HOME
# ======================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "Flask backend is running"})


# ======================================================
# LOGIN
# ======================================================

@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password required"
        }), 400

    response = login_table.get_item(Key={"email": email})
    user = response.get("Item")

    if not user or user["password"] != password:
        return jsonify({
            "success": False,
            "message": "Email or password is invalid"
        }), 401

    return jsonify({
        "success": True,
        "message": "Login successful",
        "user_name": user["user_name"]
    })


# ======================================================
# REGISTER
# ======================================================

@app.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    data = request.get_json()
    email = data.get("email")
    user_name = data.get("user_name")
    password = data.get("password")

    if not email or not user_name or not password:
        return jsonify({
            "success": False,
            "message": "All fields are required"
        }), 400

    response = login_table.get_item(Key={"email": email})
    if response.get("Item"):
        return jsonify({
            "success": False,
            "message": "The email already exists"
        }), 409

    login_table.put_item(Item={
        "email": email,
        "user_name": user_name,
        "password": password
    })

    return jsonify({
        "success": True,
        "message": "Registration successful"
    })


# ======================================================
# SEARCH MUSIC
# ======================================================

@app.route("/music/search", methods=["GET", "OPTIONS"])
def search_music():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    title = request.args.get("title", "").strip()
    artist = request.args.get("artist", "").strip()
    album = request.args.get("album", "").strip()
    year = request.args.get("year", "").strip()

    if not (title or artist or album or year):
        return jsonify({
            "success": False,
            "message": "Please enter at least one search field"
        }), 400

    items = []

    if artist and album:
        kwargs = {
            "IndexName": "AlbumIndex",
            "KeyConditionExpression":
                Key("artist").eq(artist) & Key("album").eq(album),
        }

        filters = []

        if title:
            filters.append(Attr("title").contains(title))
        if year:
            filters.append(Attr("year").eq(year))

        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            kwargs["FilterExpression"] = combined

        result = music_table.query(**kwargs)
        items = result.get("Items", [])

    elif artist:
        kwargs = {
            "KeyConditionExpression": Key("artist").eq(artist),
        }

        filters = []

        if title:
            filters.append(Attr("title").contains(title))
        if year:
            filters.append(Attr("year").eq(year))
        if album:
            filters.append(Attr("album").contains(album))

        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            kwargs["FilterExpression"] = combined

        result = music_table.query(**kwargs)
        items = result.get("Items", [])

    elif year:
        kwargs = {
            "IndexName": "YearArtistIndex",
            "KeyConditionExpression": Key("year").eq(year),
        }

        filters = []

        if title:
            filters.append(Attr("title").contains(title))
        if album:
            filters.append(Attr("album").contains(album))

        if filters:
            combined = filters[0]
            for f in filters[1:]:
                combined = combined & f
            kwargs["FilterExpression"] = combined

        result = music_table.query(**kwargs)
        items = result.get("Items", [])

    else:
        filters = []

        if title:
            filters.append(Attr("title").contains(title))
        if album:
            filters.append(Attr("album").contains(album))

        combined = filters[0]

        for f in filters[1:]:
            combined = combined & f

        result = music_table.scan(FilterExpression=combined)
        items = result.get("Items", [])

    items = [add_presigned_image_url(song) for song in items]

    return jsonify({
        "success": True,
        "songs": items
    })


# ======================================================
# SUBSCRIBE
# ======================================================

@app.route("/subscribe", methods=["POST", "OPTIONS"])
def subscribe_music():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    data = request.get_json()
    email = data.get("email")
    title = data.get("title")
    artist = data.get("artist")
    album = data.get("album")
    year = data.get("year")
    image_url = data.get("image_url")

    if not email or not title:
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400

    music_id = f"{title}_{album}_{year}"

    existing = subscriptions_table.get_item(
        Key={"email": email, "music_id": music_id}
    ).get("Item")

    if existing:
        return jsonify({
            "success": False,
            "message": "Song already subscribed"
        })

    subscriptions_table.put_item(Item={
        "email": email,
        "music_id": music_id,
        "title": title,
        "artist": artist,
        "album": album,
        "year": year,
        "image_url": image_url
    })

    return jsonify({
        "success": True,
        "message": "Subscription added successfully"
    })


# ======================================================
# GET USER SUBSCRIPTIONS
# ======================================================

@app.route("/subscriptions", methods=["GET", "OPTIONS"])
def get_subscriptions():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    email = request.args.get("email")

    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required"
        }), 400

    response = subscriptions_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )

    subscriptions = response.get("Items", [])
    subscriptions = [add_presigned_image_url(s) for s in subscriptions]

    return jsonify({
        "success": True,
        "subscriptions": subscriptions
    })


# ======================================================
# REMOVE SUBSCRIPTION
# ======================================================

@app.route("/subscription", methods=["DELETE", "OPTIONS"])
@app.route("/subscriptions", methods=["DELETE", "OPTIONS"])
def delete_subscription():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    data = request.get_json()
    email = data.get("email")
    music_id = data.get("music_id")

    if not email or not music_id:
        return jsonify({
            "success": False,
            "message": "Missing required fields"
        }), 400

    subscriptions_table.delete_item(
        Key={
            "email": email,
            "music_id": music_id
        }
    )

    return jsonify({
        "success": True,
        "message": "Subscription removed successfully"
    })


# ======================================================
# LEGACY FALLBACK
# ======================================================

@app.route("/remove_subscription", methods=["POST", "DELETE", "OPTIONS"])
def remove_subscription_legacy():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    return delete_subscription()


# ======================================================
# RUN FLASK
# ======================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=80)