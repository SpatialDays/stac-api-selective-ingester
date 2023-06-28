# stac-api-selective-ingester
Utility that ingests the STAC collection(s) and its items from the source STAC API into the target API.

## How it works
The `/search` endpoint is called on the source STAC API and the retrieved records are added into the target STAC API.

The search parameters can be passed through on an ingest request, together with any other optional flags (for example, to replace already present records or not).

## Environment Variables
| Env var | Used for | Default |
| --- | --- | --- |
| REDIS_HOST| | |
| REDIS_PORT| | |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_SET_HOST_PROVIDER | Set our details as an external provider for providers entry in the STAC record | `False` |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_NAME | Setting ourselves as the provider for the STAC API server entry | Spatial Days |
| STAC_API_SELECTIVE_INGESTER_PROVIDER_URL | Our organization provider URL (i.e. organization website) | https://spatialdays.com/ |
