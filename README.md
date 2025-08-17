# Custom Odido Mobile Home Assistant integration
Home Assistant integration for Odido Mobile (formerly T-Mobile NL). It lets you view your mobile usage and (optionally) buy a data bundle via a Home Assistant service call.

This integration relies on the data from Odido. If you consume your bundle too quickly and the Odido API hasn’t yet updated, this integration may not reflect the correct usage in time. Automations may therefore not trigger or may trigger too late.

## Disclaimer
**Using this integration may result in extra costs with Odido.** Proceed only if you fully understand and accept this risk.

## Installation
### HACS
1. Go to HACS → Integrations → Custom repositories.
2. Add this repository URL: `https://github.com/arjenbos/ha-odido-mobile`
3. Search for Odido Mobile in HACS and install it.
4. Restart Home Assistant.
5. Add the integration in Settings → Devices & services → + Add integration → Odido.

### Manually
Manual (custom component)

1. Download or clone this repo.
2. Copy the custom_components/odido directory into your Home Assistant config folder: `<config>/custom_components/odido`
3. Restart Home Assistant.
4. In Home Assistant: Settings → Devices & services → + Add integration → Odido.
5. Follow the on-screen steps.

## Automation example
```yaml
alias: Buy bundle below 300
description: ""
triggers:
  - trigger: numeric_state
    entity_id:
      - sensor.YOURSENSOR_data_left
    below: 300
conditions: []
actions:
  - action: odido.buy_bundle
    data:
      device_id: YOURDEVICEID
      buying_code: A0DAY05
mode: single
```
