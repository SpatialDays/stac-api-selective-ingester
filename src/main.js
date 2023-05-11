const express = require("express");
const express_queue = require("express-queue");
const ingesterViaPost = require("./StacSelectiveIngesterViaPost.js");
const app = express();
app.use(express.json());

app.post(
  "/",
  express_queue({ activeLimit: 1, queuedLimit: -1 }),
  async (req, res) => {
    let body = req.body;
    let sourceStacApiUrl = body.source_stac_catalog_url;
    if (!sourceStacApiUrl) {
      return res.status(400).send({error:"source_stac_catalog_url not found in body"});
    }
    // if sourceStacApiUrl ends with a slash, remove it
    if (sourceStacApiUrl.endsWith("/")) {
      sourceStacApiUrl = sourceStacApiUrl.slice(0, -1);
    }

    delete body.source_stac_catalog_url;
    console.log("Source stac api url: ", sourceStacApiUrl);
    let targetStacApiUrl = body.target_stac_catalog_url;
    if (!targetStacApiUrl) {
      return res.status(400).send({error:"target_stac_catalog_url not found in body"});
    }
    delete body.target_stac_catalog_url;
    console.log("Target stac api url: ", targetStacApiUrl);
    // if targetStacApiUrl ends with a slash, remove it
    if (targetStacApiUrl.endsWith("/")) {
      targetStacApiUrl = targetStacApiUrl.slice(0, -1);
    }
    let update = body.update;
    if (!update) {
      update = false;
    }
    delete body.update;
    console.log("Update flag: ", update);
    let callbackEndpoint = body.callback_endpoint;
    delete body.callback_endpoint;
    console.log("Callback endpoint: ", callbackEndpoint);
    let callbackId = body.callback_id;
    delete body.callback_id;
    const url = `${sourceStacApiUrl}/search`;
    body.limit = 100;

    let stacSelectiveIngester =
      new ingesterViaPost.StacSelectiveIngesterViaPost(
        sourceStacApiUrl,
        url,
        body,
        targetStacApiUrl,
        update,
        callbackEndpoint,
        callbackId
      );
    try {
      const result = await stacSelectiveIngester.getAllItems();
      return res.status(200).send(result);
    } catch (error) {
      // console.log the keys from the error object
      return res.status(400).send({ error: error.response.data });
    }
  }
);

let port = process.env.STAC_SELECTIVE_INGESTER_PORT || 7001;
app.listen(port, "0.0.0.0");
console.log("Listening on port 80");
