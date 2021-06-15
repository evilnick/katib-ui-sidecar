# katib-ui-sidecar

## Description



## Usage

Clone this repository and deploy with:

```
juju deploy ./katib-ui.charm  --resource katib-oci-image=docker.io/kubeflowkatib/katib-ui:v1beta1-a96ff59
```

## Developing

Create and activate a virtualenv with the development requirements:

    virtualenv -p python3 venv
    source venv/bin/activate
    pip install -r requirements-dev.txt

## Testing

The Python operator framework includes a very nice harness for testing
operator behaviour without full deployment. Just `run_tests`:

    ./run_tests
