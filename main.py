import os
import json
import redis
import logging
from stac_selective_ingester import StacSelectiveIngester
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_queue_key = "stac_selective_ingester_input_list"

def process_request(json_payload):
    source_stac_api_url = json_payload.get("source_stac_catalog_url")
    if not source_stac_api_url:
        raise Exception("Source STAC API URL is required")
    source_stac_api_url = source_stac_api_url.rstrip("/")
    logging.info("Source STAC API URL: %s", source_stac_api_url)

    target_stac_api_url = json_payload.get("target_stac_catalog_url")
    if not target_stac_api_url:
        raise Exception("Target STAC API URL is required")
    target_stac_api_url = target_stac_api_url.rstrip("/")
    logging.info("Target STAC API URL: %s", target_stac_api_url)

    update = json_payload.get("update", False)
    logging.info("Update flag: %s", update)

    callback_id = json_payload.get("callback_id")
    if not callback_id:
        raise Exception("Callback ID is required")
    logging.info("Callback ID: %s", callback_id)

    url = f"{source_stac_api_url}/search"
    stac_search_parameters = json_payload.get("stac_search_parameters")
    stac_search_parameters["limit"] = 100
    
    if not stac_search_parameters:
        raise Exception("STAC search parameters are required")

    stac_selective_ingester = StacSelectiveIngester(
        source_stac_api_url,
        url,
        stac_search_parameters,
        target_stac_api_url,
        update=update
    )

    try:
        result = stac_selective_ingester.get_all_items()
        logging.info("Result: %s", result)
        result["callback_id"] = callback_id
        return result
    except Exception as e:
        logging.error("Error: %s", str(e))
        return {"error": str(e), 
                "callback_id": callback_id}

if __name__ == "__main__":
    redis_client = redis.Redis(host=redis_host, port=redis_port)
    if redis_client.ping():
        logging.info(f"Connected to Redis server at {redis_host}:{redis_port}")

    while True:
        item = redis_client.blpop(redis_queue_key, timeout=1)
        if item:
            _, request_body = item
            request_body = json.loads(request_body)
            result = process_request(request_body)
            redis_client.rpush("stac_selective_ingester_output_list", json.dumps(result))
            logging.info("Processed request: %s", request_body)
