# hass-energa-my-meter

[Home Assistant](https://www.home-assistant.io/) custom integration to gather data from the
Energa My Meter (https://mojlicznik.energa-operator.pl/) website.

## Features

This integration will include the following entities to Home Assistant:

![Example sensors](docs/images/example-sensors.png)

| Parameter                | Description                                                                                                                                                                                                                       |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Energy used              | The latest reading in `kWh` for the specified meter                                                                                                                                                                               |
| Client type              | The reading of the client type specified for the account on Energa website. For example: `Odbiorca`                                                                                                                               |
| Contract period          | The reading of the contract start / end, as provided on Energa website                                                                                                                                                            |
| Energy used (statistics) | Historical readings for the energy used sensor. This has to be a separate entity due to Energa rarely updating the latest value & limitations of Home Assistant to provide statistical data. Will always be `Unknown` - it is OK. |
| ID                       | The internal meter's ID for Energa. It seems that the REST API for Energa does not use the meter number, but uses (probably) database ID instead                                                                                  |
| Last update              | The information about when was the last update published on the Energa website (**not** when it was updated in Home Assistant). This can be used to determine how often Energa refreshes the data on the account.                 |
| PPE address              | The physical address for the PPE, as provided by Energa                                                                                                                                                                           |
| Seller                   | The name of energy seller, as provided by Energa                                                                                                                                                                                  |
| Tariff                   | The name of the tariff type used by the meter                                                                                                                                                                                     |

The integration also supports loading old data from previous days. In the configuration options you can specify how many
days should be loaded on the initial run - after that the integration will load only the missing data from the last
loaded historical point.

## Energa My Meter integration issues / Known problems

1. This component **uses webscraping** method - this means that it can break with any change Energa does with its
   website. It is done this way because Energa does NOT have a proper REST API that allows to gather any data.
   Until something changes on Energa side (publishing a proper REST API), this cannot be changed.
2. It is worth mentioning that this integration has **no way of forcing update on the data presented by Energa**. This
   means that we can only get information about the recent usage as often as Energa updates it itself on the website.
   For each meter this means different refresh intervals - it can be once a day or even slower.
3. Since the author of the components has only one meter assigned to his account, support for multiple PPEs is probably
   not working.
   **The support can be added in the future**, if somebody is willing to include some data/information on this.
   Please create an issue if you wish such feature to be added.
4. Since the author of this component does not produce energy, the support for including such information is probably
   not working.
   **The support can be added in the future**, if somebody is willing to include some data/information on this.
   Please create an issue if you wish such feature to be added.

However, we are supporting statistics for the past, as Energa does support showing the usage with a 1-hour resolution
for the specific day.

## Installation

This integration is a standard Home Assistant custom component and there are many tutorials on how to install it.

### Manual

All you have to do is place the [energa_my_meter](custom_components/energa_my_meter) directory inside your
`/config/custom_components/` directory (if the `custom_components` does not exist, simply create it).

### HACS

Currently, the component is not included in the [HACS](https://hacs.xyz/) repository.
If the custom component will gain popularity the support for it could be provided, but HACS also allows including
[custom repositories](https://www.hacs.xyz/docs/faq/custom_repositories/) and the Energa integration should be
supported.

## Configuration

This integration supports adding multiple Energa accounts and meters/PPEs by creating additional config entries.

### Config flow

This custom component does support GUI installation. In your Home Assistant instance please search for Energa
integration or simply click on button below
(if you have configured the [My Home Assistant](https://my.home-assistant.io/)) to add it.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=energa_my_meter)

The configuration wizard will provide the details about possible configuration options.

You can also change the interval of refreshing the data (by default 5 hours) to best suit your needs by clicking on the
`Configure` button near the integration's config entry.

### YAML

The YAML configuration will be imported as a config flow and presented in GUI as additional integration config entry.

```yaml
energa_my_meter:
  - password: YOUR_ENERGA_PASSWORD
    username: YOUR_ENERGA_USERNAME
     # The meter number that the integration should monitor
    selected_meter: XX
    # The internal Energa ID for the meter. Can be seen in API calls when checking the past usage
    selected_meter_internal_id: XX 
    # Optional. You can also configure it in the integration options (GUI)
    # Interval in *minutes* which will be used to refresh data from the Energa website
    # By default 300 minutes
    scan_interval: 310
    # Optional. How many historical days should be loaded initially, by default 10
    number_of_days_to_load: 100
```

## Debugging

To enable debug logs please set up the Home Assistant logger:

```yaml
custom_components.energa_my_meter: debug
```
