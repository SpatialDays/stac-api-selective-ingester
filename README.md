# stac-api-selective-ingester
Utility that ingests the STAC collection(s) and its items from the source STAC API into the target API.

## How it works
The `/search` endpoint is called on the source STAC API and the retrieved records are added into the target STAC API.

The search parameters can be passed through on an ingest request, together with any other optional flags (for example, to replace already present records or not).

### Starting the ingest
Make a `POST` request to `/` endpoint.

At a minimum, your request must have source and target STAC API URLs. You should have GET request permission for the source STAC API and GET, POST, and PUT request permission on the target STAC API server.

Additional "update" parameter can be set to `true`, which will update items that are already present on the STAC API server.

In addition to target and source STAC API URLs, all additional search query parameters from the official STAC item search standard can be used. 
Those are available at: https://github.com/radiantearth/stac-api-spec/tree/main/item-search#Query%20Parameter%20Table 

## Deploying
Meant to be running on Azure serverless ACI.

## Environment Variables
| Env var | Used for | Default |
| --- | --- | --- |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_SET_HOST_PROVIDER | Set our details as an external provider for providers entry in the STAC record | `False` |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_NAME | Setting ourselves as the provider for the STAC API server entry | Spatial Days |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_URL | Our organization provider URL (i.e. organization website) | https://spatialdays.com/ |
