# LightStack Home Assistant Integration

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![pre-commit][pre-commit-shield]][pre-commit]
[![Black][black-shield]][black]

[![hacs][hacsbadge]][hacs]
[![Project Maintenance][maintenance-shield]][user_profile]

A Home Assistant custom component for [LightStack](https://github.com/sjafferali/LightStack) - a priority-based alert management system for Inovelli LED switches.

## Features

- **Real-time Updates**: Uses WebSocket for instant push notifications - no polling required
- **Current Alert Sensor**: Shows the highest priority active alert with LED color/effect attributes
- **Alert Status Binary Sensor**: Simple on/off indicator when any alert is active
- **Clear All Button**: One-click button to clear all active alerts
- **Services**: Full control via Home Assistant services for automations

## Platforms

| Platform        | Description                                                                |
| --------------- | -------------------------------------------------------------------------- |
| `sensor`        | Shows the current (highest priority) active alert name with LED attributes |
| `binary_sensor` | Indicates if any alert is currently active (`on`) or all clear (`off`)     |
| `button`        | Clear all active alerts with a single press                                |

## Services

| Service                       | Description                                              |
| ----------------------------- | -------------------------------------------------------- |
| `lightstack.trigger_alert`    | Trigger an alert by key, with optional priority override |
| `lightstack.clear_alert`      | Clear a specific alert by key                            |
| `lightstack.clear_all_alerts` | Clear all active alerts                                  |

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/sjafferali/lightstack-homeassistant` as an Integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/lightstack` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

After installation:

1. Go to Settings -> Devices & Services
2. Click "+ Add Integration"
3. Search for "LightStack"
4. Enter your LightStack server host and port

## Configuration

The integration is configured through the UI:

| Field | Description                              | Default     |
| ----- | ---------------------------------------- | ----------- |
| Host  | Hostname or IP of your LightStack server | `localhost` |
| Port  | WebSocket API port                       | `8080`      |

## Sensor Attributes

The Current Alert sensor provides these attributes for use in automations:

| Attribute            | Description                                                 |
| -------------------- | ----------------------------------------------------------- |
| `is_all_clear`       | Boolean indicating if all alerts are cleared                |
| `active_count`       | Number of currently active alerts                           |
| `alert_key`          | Unique identifier of the current alert                      |
| `effective_priority` | Priority level (1-5) of the current alert                   |
| `priority_name`      | Human-readable priority (Critical, High, Medium, Low, Info) |
| `led_color`          | Inovelli LED color value (0-255)                            |
| `led_color_name`     | Human-readable color name (Red, Blue, Green, etc.)          |
| `led_effect`         | LED effect code (solid, pulse, chase, aurora, etc.)         |
| `led_effect_name`    | Human-readable effect name (Solid, Pulse, Chase, etc.)      |
| `led_brightness`     | LED brightness level (0-100)                                |
| `led_duration`       | LED duration value (encoded, see below)                     |
| `led_duration_name`  | Human-readable duration (e.g., "5 Minutes", "Indefinitely") |
| `last_triggered`     | Timestamp when the alert was last triggered                 |
| `description`        | Alert description if configured                             |

### LED Effects

All supported Inovelli Blue series LED effects:

| Effect Code      | Display Name   |
| ---------------- | -------------- |
| `off`            | Off            |
| `solid`          | Solid          |
| `fast_blink`     | Fast Blink     |
| `slow_blink`     | Slow Blink     |
| `pulse`          | Pulse          |
| `chase`          | Chase          |
| `open_close`     | Open/Close     |
| `small_to_big`   | Small to Big   |
| `aurora`         | Aurora         |
| `slow_falling`   | Slow Falling   |
| `medium_falling` | Medium Falling |
| `fast_falling`   | Fast Falling   |
| `slow_rising`    | Slow Rising    |
| `medium_rising`  | Medium Rising  |
| `fast_rising`    | Fast Rising    |
| `medium_blink`   | Medium Blink   |
| `slow_chase`     | Slow Chase     |
| `fast_chase`     | Fast Chase     |
| `fast_siren`     | Fast Siren     |
| `slow_siren`     | Slow Siren     |
| `clear_effect`   | Clear Effect   |

### LED Duration Encoding

Duration values are encoded as follows:

| Value Range | Unit       | Example            |
| ----------- | ---------- | ------------------ |
| 1-60        | Seconds    | 30 = 30 seconds    |
| 61-120      | Minutes    | 65 = 5 minutes     |
| 121-254     | Hours      | 132 = 12 hours     |
| 255         | Indefinite | Runs until cleared |

## Example Automations

### Trigger an alert when garage door opens

```yaml
automation:
  - alias: "Alert on Garage Door Open"
    trigger:
      - platform: state
        entity_id: cover.garage_door
        to: "open"
    action:
      - service: lightstack.trigger_alert
        data:
          alert_key: "garage_door_open"
          priority: 2
          note: "Garage door opened"
```

### Clear alert when garage door closes

```yaml
automation:
  - alias: "Clear Garage Door Alert"
    trigger:
      - platform: state
        entity_id: cover.garage_door
        to: "closed"
    action:
      - service: lightstack.clear_alert
        data:
          alert_key: "garage_door_open"
```

### Set Inovelli LED based on LightStack state (Zigbee2MQTT)

For Inovelli Blue series switches with Zigbee2MQTT:

```yaml
automation:
  - alias: "Update Inovelli LED from LightStack"
    trigger:
      - platform: state
        entity_id: sensor.lightstack_current_alert
    action:
      - service: mqtt.publish
        data:
          topic: "zigbee2mqtt/Office Switch/set"
          payload_template: >
            {% set sensor = states.sensor.lightstack_current_alert %}
            {% if sensor.state == 'All Clear' %}
              {"led_effect": {"effect": "off"}}
            {% else %}
              {
                "led_effect": {
                  "effect": "{{ sensor.attributes.led_effect | default('solid') }}",
                  "color": {{ sensor.attributes.led_color | default(0) }},
                  "level": {{ sensor.attributes.led_brightness | default(100) }},
                  "duration": {{ sensor.attributes.led_duration | default(255) }}
                }
              }
            {% endif %}
```

### Set Inovelli LED (Z-Wave)

For Z-Wave Inovelli switches:

```yaml
automation:
  - alias: "Update Inovelli LED from LightStack"
    trigger:
      - platform: state
        entity_id: sensor.lightstack_current_alert
    action:
      - choose:
          - conditions:
              - condition: state
                entity_id: sensor.lightstack_current_alert
                state: "All Clear"
            sequence:
              - service: zwave_js.set_config_parameter
                target:
                  entity_id: light.inovelli_switch
                data:
                  parameter: 16
                  value: 0 # Clear notification
          - conditions:
              - condition: template
                value_template: "{{ state_attr('sensor.lightstack_current_alert', 'led_color') is not none }}"
            sequence:
              - service: zwave_js.set_config_parameter
                target:
                  entity_id: light.inovelli_switch
                data:
                  parameter: 16
                  value: >
                    {% set color = state_attr('sensor.lightstack_current_alert', 'led_color') | default(0) %}
                    {% set effect = state_attr('sensor.lightstack_current_alert', 'led_effect') %}
                    {% set effect_num = {'solid': 1, 'fast_blink': 2, 'slow_blink': 3, 'pulse': 4}.get(effect, 1) %}
                    {{ (color * 65536) + (effect_num * 256) + 255 }}
```

## Requirements

- Home Assistant 2023.1.0 or newer
- LightStack server running and accessible

## Troubleshooting

### Cannot Connect

1. Verify LightStack server is running
2. Check the host and port are correct
3. Ensure there are no firewalls blocking the WebSocket connection
4. Check Home Assistant logs for detailed error messages

### Entities Not Updating

The integration uses WebSocket push notifications. If entities stop updating:

1. Check if LightStack server is still running
2. Reload the integration from Settings -> Devices & Services
3. Check logs for reconnection messages

## Contributing

Contributions are welcome! Please read the [Contribution guidelines](CONTRIBUTING.md).

## Credits

This project was generated from [@oncleben31](https://github.com/oncleben31)'s [Home Assistant Custom Component Cookiecutter](https://github.com/oncleben31/cookiecutter-homeassistant-custom-component) template.

---

[integration_blueprint]: https://github.com/custom-components/integration_blueprint
[black]: https://github.com/psf/black
[black-shield]: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[commits]: https://github.com/sjafferali/lightstack-homeassistant/commits/main
[hacs]: https://hacs.xyz
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-%40sjafferali-blue.svg?style=for-the-badge
[pre-commit]: https://github.com/pre-commit/pre-commit
[pre-commit-shield]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/sjafferali/lightstack-homeassistant.svg?style=for-the-badge
[releases]: https://github.com/sjafferali/lightstack-homeassistant/releases
[user_profile]: https://github.com/sjafferali
