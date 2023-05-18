from flask import Flask, request, jsonify
from functools import wraps
from stac_selective_ingester_via_post import StacSelectiveIngesterViaPost
import os

app = Flask(__name__)

def validate_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.json or "source_stac_catalog_url" not in request.json:
            return jsonify({"error": "source_stac_catalog_url not found in body"}), 400
        if not request.json or "target_stac_catalog_url" not in request.json:
            return jsonify({"error": "target_stac_catalog_url not found in body"}), 400
        return f(*args, **kwargs)
    return decorated_function

@app.route("/", methods=["POST"])
@validate_request
def process_request():
    body = request.json
    source_stac_api_url = body["source_stac_catalog_url"]
    if source_stac_api_url.endswith("/"):
        source_stac_api_url = source_stac_api_url[:-1]
    del body["source_stac_catalog_url"]
    print("Source STAC API URL:", source_stac_api_url)

    target_stac_api_url = body["target_stac_catalog_url"]
    if target_stac_api_url.endswith("/"):
        target_stac_api_url = target_stac_api_url[:-1]
    del body["target_stac_catalog_url"]
    print("Target STAC API URL:", target_stac_api_url)

    update = body.get("update", False)
    del body["update"]
    print("Update flag:", update)

    url = f"{source_stac_api_url}/search"
    body["limit"] = 100

    stac_selective_ingester = StacSelectiveIngesterViaPost(
        source_stac_api_url,
        url,
        body,
        target_stac_api_url,
        update
    )

    try:
        result = stac_selective_ingester.get_all_items()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    port = int(os.getenv("STAC_SELECTIVE_INGESTER_PORT", 7001))
    app.run(host="0.0.0.0", port=port)
    print("Listening on port", port)
