# Custom Odido Mobile Home Assistant integration
Home Assistant integration for Odido Mobile (formerly T-Mobile NL). It lets you view your mobile usage and (optionally) buy a data bundle via a Home Assistant service call.

## Disclaimer
**Using this integration may result in extra costs with Odido.** Proceed only if you fully understand and accept this risk.

## Automation example
```yaml
alias: Reload below 300
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
