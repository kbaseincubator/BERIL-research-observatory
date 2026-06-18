# OpenViking Deployment on SPIN notes
## Short-short version for dev re-deployment
1. Build Dockerfile with command (from repo root):  
```
  docker build \  
  -t registry.nersc.gov/kbase/beril-openviking:develop \  
  --platform linux/amd64 \  
  --push \  
  knowledge/openviking/
```
2. Make sure secrets are set / updated.
3. Redeploy the knowledge-engine/beril-open-viking container.

## Longer version for dev deployment choices and such
### Dockerfile
The Dockerfile's pretty simple. It installs a pinned version of OpenViking and the Google-centric LiteLLM adapter (not installed with OpenViking, but needed for Google Cloud Provider (GCP) models).

It creates an `openviking` group and `ov` user and sets them to the right SPIN user id for deployment there.

Finally, it makes a `/ov` directory where all the OpenViking stuff should get stored.

### Deployment stack
Deployment is done on NERSC SPIN, which uses Rancher2 / Kubernetes for managing deployments. The stack uses the following:

*Secrets*
* openviking-secrets - holds the OV_ROOT_API_KEY key that has the root key for running the server remotely
* openviking-gcp-key - holds the JSON of the GCP key (created with the KBase account). This gets mounted to disk

*ConfigMaps*  
* openviking-config - non-secret config variables required for GCP, and the full JSON of the OpenViking config. These all get mounted to disk for simplicity, only `ov.conf` is used

*Workloads/Deployments*  
* imports OV_ROOT_API_KEY, VERTEXAI_LOCATION, VERTEXAI_PROJECT as environment variables
* mounts gcp key to /var/secrets/gcp/gcp-key.json (as Secret)
* mounts ov config to /var/openviking/ov.conf (as ConfigMap)
* mounts PersistentVolumeClaim to /ov/workspace - this is where the data lives

*Ingress*
* We want to keep it on the same "host" as https://beril.kbase.us (and https://beril-dev.kbase.us) under the /ov path. This requires a little mapping through K8s and NGINX that's not built into the Rancher2 UI.
* Leave the primary beril ingress alone
* Create a new ingress for just openviking
* It needs a default mapping (http://openviking.beril.production.svc.spin.nersc.org). Save that first.
* Open it back up, go into YAML editing mode, and make sure it aligns (more or less) with `ingress-beril-openviking.yaml`. That file is set up for beril-dev, make adjustments as needed for production. Make sure the path follows the regex and pathType is `ImplementationSpecific`, Also make sure to include these two lines near the top of the file under `metadata.annotations`:
  * nginx.ingress.kubernetes.io/rewrite-target: /$2
  * nginx.ingress.kubernetes.io/use-regex: 'true'
These aren't available in the UI, so you'll have to edit directly.

Once these are deployed, OpenViking should be available by calling `https://beril.kbase.us/ov` (i.e. setting the `OPENVIKING_URL` environment variable to that endpoint and invoking one of the scripts.)
