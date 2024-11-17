# Local development using Docker

This Docker compose project helps with the development process of the Home Assistant component.

## Prerequisites

1. One must have a working Docker installed, with the `docker compose` plugin included

## Usage

### Running the Home Assistant instance

The `home-assistant` service creates a new, empty Home Assistant instance that will have the component preinstalled.
This instance is configured to store its persistence layer inside the [`config`](config) directory - you can find there 
standard Home Assistant configuration files, that will allow you - for example import the component from YAML.

```shell
docker compose up -d home-assistant
```

After making any change to component's files, please ensure to restart your Home Assistant instance.

### Executing tests

Because Home Assistant unit tests are hard to configure on some systems (for example: on Windows), the `tests` service
creates the same container that is used by CI pipeline process. This service during the startup will automatically
download all components dependencies, so after it starts you can execute tests.

```shell
# Start the container
docker compose up -d tests
# Execute tests (escape variables if necessary)
docker compose exec -it tests uv run -- pytest --asyncio-mode=auto -vv --cov
# Lint your code
docker compose exec -it tests uv run -- pylint custom_components/energa_my_meter tests
```

You do not need to restart the container after making any changes to the code as it is mounted via the volume with your
host repository.
