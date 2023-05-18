const collectionUtils = require("./utilities.js");
const axios = require("axios");

class StacSelectiveIngesterViaPost {
  constructor(
    sourceApiUrl,
    startUrl,
    startBody,
    targetStacApiUrl,
    update = false
  ) {
    // remove trailing slash if it exists on sourceApiUrl
    if (sourceApiUrl.endsWith("/")) {
      sourceApiUrl = sourceApiUrl.slice(0, -1);
    }
    this.sourceApiUrl = sourceApiUrl;
    this.startUrl = startUrl;
    this.targetStacApiUrl = targetStacApiUrl;
    // remove trailing slash if it exists on targetStacApiUrl
    if (targetStacApiUrl.endsWith("/")) {
      targetStacApiUrl = targetStacApiUrl.slice(0, -1);
    }
    this.update = update;
    this.startBody = startBody;
    this.processedCollections = [];
    this.newlyStoredCollectionsCount = 0;
    this.newlyStoredCollections = [];
    this.updatedCollectionsCount = 0;
    this.updatedCollections = [];
    this.newlyAddedItemsCount = 0;
    this.updatedItemsCount = 0;
    this.itemsAlreadyPresentCount = 0;
  }

  _make_report() {
    const data = {
      newly_stored_collections_count: this.newlyStoredCollectionsCount,
      newly_stored_collections: this.newlyStoredCollections,
      updated_collections_count: this.updatedCollectionsCount,
      updated_collections: this.updatedCollections,
      newly_stored_items_count: this.newlyAddedItemsCount,
      updated_items_count: this.updatedItemsCount,
      already_stored_items_count: this.itemsAlreadyPresentCount,
      callback_id: this.callbackId,
    };
    return data;
  }

  async getAllItems() {
    let itemsUrl = this.startUrl;
    let itemsBody = this.startBody;
    while (itemsUrl) {
      let response;
      for (let i = 0; i < 5; i++) {
        try {
          response = await axios.post(itemsUrl, itemsBody);
          break;
        } catch (error) {
          await new Promise((r) => setTimeout(r, 1000));
          if (i < 4) {
            console.log("Retrying...");
            continue;
          }
          // console.error("Error getting items from source API", error);
          throw error;
        }
      }
      itemsUrl = undefined;
      itemsBody = undefined;
      const data = response.data;
      const feautures = data.features;
      for (let i = 0; i < feautures.length; i++) {
        const item = feautures[i];
        const sourceStacApiCollectionUrl = item.links.find(
          (link) => link.rel === "collection"
        ).href;
        await this._storeCollectionIntoTargetStacApi(sourceStacApiCollectionUrl);
        let collectionId = sourceStacApiCollectionUrl.split("/").pop();
        collectionUtils.removeRelsFromLinks(item);
        await this._storeItemIntoTargetStacApi(item, collectionId);
      }
      const nextItemSetLink = data.links.find((link) => link.rel === "next");
      if (nextItemSetLink) {
        itemsUrl = nextItemSetLink.href;
        itemsBody = nextItemSetLink.body;
        console.log("Getting next page...", itemsUrl);
        console.log(JSON.stringify(itemsBody, null, 4));
      } else {
        console.log("Stopping at last page.");
        break;
      }
    }
    return this._make_report();
  }


  async _storeCollectionIntoTargetStacApi(sourceStacApiCollectionUrl) {
    if (this.processedCollections.includes(sourceStacApiCollectionUrl)) {
      return;
    }
    let collection;
    collection = await axios.get(sourceStacApiCollectionUrl);
    collectionUtils.addProviderToCollection(collection.data);
    collectionUtils.removeRelsFromLinks(collection.data);
    const collectionsEndpoint = this.targetStacApiUrl + "/collections";
    try {
      let response = await axios.post(collectionsEndpoint, collection.data);
      console.log("Stored collection: ", response.data.id);
      this.newlyStoredCollectionsCount++;
      this.newlyStoredCollections.push(sourceStacApiCollectionUrl);
    } catch (error) {
      if (error.response && error.response.data && error.response.data.code) {
        const message = error.response.data.code;
        if (message === "ConflictError")
          console.log(`Collection ${collection.data.id} already exists.`);
        let response = await axios.put(collectionsEndpoint, collection.data);
        console.log("Updated collection: ", response.data.id);
        this.updatedCollectionsCount++;
        this.updatedCollections.push(sourceStacApiCollectionUrl);
      } else {
        console.error(`Error storing collection ${collection.data.id}`, error);
      }
    }
    this.processedCollections.push(sourceStacApiCollectionUrl);
    await new Promise((r) => setTimeout(r, 1000));
  }

  async _storeItemIntoTargetStacApi(item, collectionId) {
    return new Promise(async (resolve, reject) => {
      console.log("Storing item: ", item.id);
      const itemsEndpoint =
        this.targetStacApiUrl + "/collections/" + collectionId + "/items";
      try {
        let response = await axios.post(itemsEndpoint, item);
        console.log("Stored item: ", response.data.id);
        this.newlyAddedItemsCount++;
        return resolve("Stored item: ", response.data.id);
      } catch (error) {
        if (error.response && error.response.data && error.response.data.code) {
          const message = error.response.data.code;
          if (message === "ConflictError") {
            if (this.update === false) {
              console.log(`Item ${item.id} already exists.`);
              this.itemsAlreadyPresentCount++;
              return resolve(`Item ${item.id} already exists.`);
            } else {
              try {
                let response = await axios.put(
                  itemsEndpoint + "/" + item.id,
                  item
                );
                this.updatedItemsCount++;
                console.log("Updated item: ", response.data.id);
                return resolve("Updated item: ", response.data.id);
              } catch (error) {
                console.error(`Error updating item ${item.id}`, error);
                return reject(error);
              }
            }
          } else {
            console.error(`Error storing item ${item.id}: ${error}`);
            return reject(error);
          }
        }
      }
    });
  }
}

module.exports = { StacSelectiveIngesterViaPost };