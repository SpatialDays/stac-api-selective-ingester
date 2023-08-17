import time
import requests
import os
import logging
import json
from urllib.parse import urljoin, urlparse

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class StacSelectiveIngester:
    def __init__(
        self,
        source_stac_api_url,
        start_url,
        start_body,
        target_stac_api_url,
        update=False,
    ):
        self.source_api_url = source_stac_api_url.rstrip("/")
        self.start_url = start_url
        self.target_stac_api_url = target_stac_api_url.rstrip("/")
        self.update = update
        self.start_body = start_body
        self.processed_collections = []
        self.newly_stored_collections_count = 0
        self.newly_stored_collections = []
        self.updated_collections_count = 0
        self.updated_collections = []
        self.newly_added_items_count = 0
        self.updated_items_count = 0
        self.items_already_present_count = 0

    def _make_report(self):
        data = {
            "newly_stored_collections_count": self.newly_stored_collections_count,
            "newly_stored_collections": self.newly_stored_collections,
            "updated_collections_count": self.updated_collections_count,
            "updated_collections": self.updated_collections,
            "newly_stored_items_count": self.newly_added_items_count,
            "updated_items_count": self.updated_items_count,
            "already_stored_items_count": self.items_already_present_count,
        }
        return data

    def get_all_items(self):
        items_url = self.start_url
        items_body = self.start_body
        while items_url:
            response = None
            for i in range(5):
                try:
                    response = requests.post(items_url, json=items_body)
                    response.raise_for_status()
                    break
                except requests.exceptions.RequestException as error:
                    time.sleep(1)
                    if i < 4:
                        logging.info("Retrying...")
                        continue
                    raise error
            items_url = None
            items_body = None
            data = response.json()
            features = data["features"]
            for item in features:
                source_stac_api_collection_url = next(
                    (
                        link["href"]
                        for link in item["links"]
                        if link["rel"] == "collection"
                    ),
                    None,
                )
                if source_stac_api_collection_url:
                    self._store_collection_into_target_stac_api(
                        source_stac_api_collection_url
                    )
                    collection_id = source_stac_api_collection_url.split("/")[-1]
                    self._remove_rels_from_links(item)
                    self._store_item_into_target_stac_api(item, collection_id)
            next_item_set_link = next(
                (link for link in data.get("links", []) if link["rel"] == "next"),
                None,
            )
            if next_item_set_link:
                items_url = urljoin(self.source_api_url, next_item_set_link["href"])
                items_body = next_item_set_link["body"]
                logging.info("Getting next page... %s", items_url)
                logging.info(json.dumps(items_body, indent=4))
            else:
                logging.info("Stopping at last page.")
                break
        return self._make_report()

    def _store_collection_into_target_stac_api(self, source_stac_api_collection_url):
        if source_stac_api_collection_url in self.processed_collections:
            return
        collection_response = requests.get(source_stac_api_collection_url)
        collection = collection_response.json()
        stac_extensions = collection.get("stac_extensions", [])
        stac_extensions.append(
            "https://raw.githubusercontent.com/SpatialDays/sd-stac-extensions/main/spatialdays-stac-portal-metadata/v0.0.1/schema.json"
        )
        collection["stac_extensions"] = stac_extensions
        collection["stac-portal-metadata"] = {
            "type-of-collection": "public",
        }
        self._add_provider_to_collection(collection)
        self._remove_rels_from_links(collection)
        collections_endpoint = urljoin(self.target_stac_api_url, "/collections")
        try:
            response = requests.post(collections_endpoint, json=collection)
            response.raise_for_status()
            logging.info("Stored collection: %s", response.json()["id"])
            self.newly_stored_collections_count += 1
            self.newly_stored_collections.append(source_stac_api_collection_url)
        except requests.exceptions.HTTPError as error:
            if (error.response.status_code == 409):
                logging.info("Collection %s already exists.", collection["id"])
                self.updated_collections.append(source_stac_api_collection_url)
                self.updated_collections_count += 1
                response = requests.put(collections_endpoint, json=collection)
                response.raise_for_status()
                logging.info("Updated collection: %s", response.json()["id"])
            else:
                logging.error(
                    "Error storing collection %s: %s", collection["id"], error
                )
        self.processed_collections.append(source_stac_api_collection_url)

    def _store_item_into_target_stac_api(self, item, collection_id):
        items_endpoint = urljoin(
            self.target_stac_api_url, f"/collections/{collection_id}/items"
        )
        try:
            response = requests.post(items_endpoint, json=item)
            response.raise_for_status()
            logging.info("Stored item: %s", response.json()["id"])
            self.newly_added_items_count += 1
            return f"Stored item: {response.json()['id']}"
        except requests.exceptions.HTTPError as error:
            # if (
            #     error.response
            #     and error.response.json().get("code") == "ConflictError"
            # ):
            if not self.update:
                logging.info("Item %s already exists.", item["id"])
                self.items_already_present_count += 1
                return f"Item {item['id']} already exists."
            else:
                try:
                    response = requests.put(f"{items_endpoint}/{item['id']}", json=item)
                    response.raise_for_status()
                    self.updated_items_count += 1
                    logging.info("Updated item: %s", response.json()["id"])
                    return f"Updated item: {response.json()['id']}"
                except Exception as error:
                    logging.error("Error updating item %s: %s", item["id"], error)
                    return f"Error updating item {item['id']}: {error}"

    @staticmethod
    def _add_provider_to_collection(collection):
        set_provider = (
            os.getenv("STAC_API_SELECTIVE_INGESTER_PROVIDER_SET_HOST_PROVIDER") or True
        )
        if set_provider:
            collection["providers"].append(
                {
                    "name": os.getenv("STAC_API_SELECTIVE_INGESTER_PROVIDER_NAME")
                    or "Spatial Days",
                    "url": os.getenv("STAC_API_SELECTIVE_INGESTER_PROVIDER_URL")
                    or "https://spatialdays.com/",
                    "roles": ["host"],
                }
            )

    @staticmethod
    def _remove_rels_from_links(collection):
        refs_to_remove = ["items", "parent", "root", "self", "collection"]
        collection["links"] = [
            link for link in collection["links"] if link["rel"] not in refs_to_remove
        ]
