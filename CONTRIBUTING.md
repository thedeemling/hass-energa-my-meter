# Contributing

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

Because this repository is hosted mainly
on [GitLab](https://gitlab.com/home-assistant-custom-components/hass-energa-my-meter),
and the [GitHub repo](https://github.com/thedeemling/hass-energa-my-meter) is just a mirror, please try to contribute 
on the GitLab if possible, to make it easier to avoid conflicts during the mirroring process.

## Local development

This repository was configured to make it as easy as it is possible to develop changes locally,
without having to push them to the repository.

To make a repeatable environment for everybody, we have decided to create a Docker compose project
that allows the user to execute development & unit tests, as well as execute CI pipeline scripts. More information
about usage of Docker can be found in the [`local-docker`](local-docker) directory.

The owner of the repository uses
the [JetBrains IntelliJ Ultimate](https://www.jetbrains.com/idea/buy/?section=commercial&billing=yearly) IDE, but we are
welcome to any kind of IDE setups that would help with local development.

## Pull Request Process

1. Ensure your change works locally
2. In the change requires it, please update the README.md documentation with details of changes to the interface.
3. You may merge the Pull Request in once you have an approval from the owner of the repository, after the CI pipeline
   finishes successfully.
