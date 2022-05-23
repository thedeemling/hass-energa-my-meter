# hass-energa-my-meter

[Home Assistant](https://www.home-assistant.io/) custom integration to gather data from the 
Energa My Meter (https://mojlicznik.energa-operator.pl/) website.

This component **uses webscraping** method - this means that it can break with any change Energa does with its website.
It is done this way because Energa does NOT have API that allows to gather any data.

## Energa My Meter integration issues

It is worth mentioning that this integration has **no way of forcing update on the data presented by Energa**. This means
that we can only get information about the recent usage as often as Energa updates it itself on the website. For each
meter this means different refresh intervals - it can be once a day or even slower.

## Installation

### Manual

All you have to do is place the [energa_my_meter](custom_components/energa_my_meter) directory inside your
`/config/custom_components/` directory (if the `custom_components` does not exist, simply create it).

### HACS

Currently [HACS](https://hacs.xyz/) integration does not exist. If the custom component will gain popularity
we will try to add it to the official HACS repository.

## Usage

This integration supports adding multiple Energa accounts by creating additional config entries.

### Config flow

This custom component does support GUI installation. In your Home Assistant instance please search for Energa
integration or simply click on button below 
(if you have configured the [My Home Assistant](https://my.home-assistant.io/)) to add it.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=energa_my_meter)

### YAML

The YAML configuration will be imported as a config flow and presented in GUI as additional integration config entry.

```yaml
energa_my_meter:
  - password: YOUR_ENERGA_PASSWORD
    username: YOUR_ENERGA_USERNAME
    # Optional. You can also configure it in the integration options (GUI)
    # Interval in *minutes* which will be used to refresh data from the Energa website
    scan_interval: 310
```

## Debugging

To enable debug logs please set up the Home Assistant logger:

```yaml
custom_components.energa_my_meter: debug
```
