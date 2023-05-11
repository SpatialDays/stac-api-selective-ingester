const axios = require("axios");

/**
 * Addends the provider from the environment to the collection
 * @param {Object.<string, Object>} collection
 */
function addProviderToCollection(collection) {
  const SET_PROVIDER =
    process.env.STAC_API_SELECTIVE_INGESTER_PROVIDER_SET_HOST_PROVIDER || true;
  if (SET_PROVIDER) {
    collection.providers.push({
      name:
        process.env.STAC_API_SELECTIVE_INGESTER_PROVIDER_NAME ||
        "Spatial Days",
      url:
        process.env.STAC_API_SELECTIVE_INGESTER_PROVIDER_URL ||
        "https://spatialdays.com/",
      roles: ["host"],
    });
  }
}

/**
 * Removes the rels from the links in the collection.
 */
function removeRelsFromLinks(collection) {
  const refsToRemove = ["items", "parent", "root", "self", "collection"];
  collection.links = collection.links.filter(
    (link) => !refsToRemove.includes(link.rel)
  );
}

async function getStacVersionFromStacApi(apiRootUrl) {
  let response = await axios.get(apiRootUrl);
  return response.data.stac_version;
}

module.exports = {
  addProviderToCollection,
  removeRelsFromLinks,
  getStacVersionFromStacApi,
};
