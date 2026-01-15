"""Constants for LightStack integration."""

from typing import Final

# Base component constants
NAME: Final = "LightStack"
DOMAIN: Final = "lightstack"
VERSION: Final = "1.0.0"
MANUFACTURER: Final = "LightStack"

ISSUE_URL: Final = "https://github.com/sjafferali/lightstack-homeassistant/issues"

# Icons
ICON_ALERT: Final = "mdi:alert"
ICON_ALERT_CIRCLE: Final = "mdi:alert-circle"
ICON_CHECK_CIRCLE: Final = "mdi:check-circle"
ICON_CLEAR_ALL: Final = "mdi:notification-clear-all"
ICON_LED: Final = "mdi:led-on"

# Platforms
BINARY_SENSOR: Final = "binary_sensor"
SENSOR: Final = "sensor"
BUTTON: Final = "button"
PLATFORMS: Final = [BINARY_SENSOR, SENSOR, BUTTON]

# Configuration
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"

# Defaults
DEFAULT_HOST: Final = "localhost"
DEFAULT_PORT: Final = 8080

# WebSocket event types (server -> client)
WS_EVENT_CONNECTION_ESTABLISHED: Final = "connection_established"
WS_EVENT_ALERT_TRIGGERED: Final = "alert_triggered"
WS_EVENT_ALERT_CLEARED: Final = "alert_cleared"
WS_EVENT_ALL_ALERTS_CLEARED: Final = "all_alerts_cleared"
WS_EVENT_CURRENT_ALERT_CHANGED: Final = "current_alert_changed"
WS_EVENT_COMMAND_RESULT: Final = "command_result"
WS_EVENT_ERROR: Final = "error"

# WebSocket command types (client -> server)
WS_CMD_PING: Final = "ping"
WS_CMD_GET_STATE: Final = "get_state"
WS_CMD_GET_ACTIVE_ALERTS: Final = "get_active_alerts"
WS_CMD_GET_ALL_ALERTS: Final = "get_all_alerts"
WS_CMD_TRIGGER_ALERT: Final = "trigger_alert"
WS_CMD_CLEAR_ALERT: Final = "clear_alert"
WS_CMD_CLEAR_ALL_ALERTS: Final = "clear_all_alerts"

# Priority levels
PRIORITY_CRITICAL: Final = 1
PRIORITY_HIGH: Final = 2
PRIORITY_MEDIUM: Final = 3
PRIORITY_LOW: Final = 4
PRIORITY_INFO: Final = 5

PRIORITY_NAMES: Final = {
    PRIORITY_CRITICAL: "Critical",
    PRIORITY_HIGH: "High",
    PRIORITY_MEDIUM: "Medium",
    PRIORITY_LOW: "Low",
    PRIORITY_INFO: "Info",
}

# LED Effects
LED_EFFECT_SOLID: Final = "solid"
LED_EFFECT_BLINK: Final = "blink"
LED_EFFECT_PULSE: Final = "pulse"
LED_EFFECT_CHASE: Final = "chase"

LED_EFFECTS: Final = [LED_EFFECT_SOLID, LED_EFFECT_BLINK, LED_EFFECT_PULSE, LED_EFFECT_CHASE]

# Inovelli LED Color mapping (0-255)
LED_COLOR_RED: Final = 0
LED_COLOR_ORANGE: Final = 21
LED_COLOR_YELLOW: Final = 42
LED_COLOR_GREEN: Final = 85
LED_COLOR_CYAN: Final = 127
LED_COLOR_BLUE: Final = 170
LED_COLOR_PURPLE: Final = 212
LED_COLOR_PINK: Final = 234
LED_COLOR_WHITE: Final = 255

LED_COLOR_NAMES: Final = {
    LED_COLOR_RED: "Red",
    LED_COLOR_ORANGE: "Orange",
    LED_COLOR_YELLOW: "Yellow",
    LED_COLOR_GREEN: "Green",
    LED_COLOR_CYAN: "Cyan",
    LED_COLOR_BLUE: "Blue",
    LED_COLOR_PURPLE: "Purple",
    LED_COLOR_PINK: "Pink",
    LED_COLOR_WHITE: "White",
}

# Service names
SERVICE_TRIGGER_ALERT: Final = "trigger_alert"
SERVICE_CLEAR_ALERT: Final = "clear_alert"
SERVICE_CLEAR_ALL_ALERTS: Final = "clear_all_alerts"

# Service data fields
ATTR_ALERT_KEY: Final = "alert_key"
ATTR_PRIORITY: Final = "priority"
ATTR_NOTE: Final = "note"

# Sensor attributes
ATTR_IS_ALL_CLEAR: Final = "is_all_clear"
ATTR_ACTIVE_COUNT: Final = "active_count"
ATTR_LED_COLOR: Final = "led_color"
ATTR_LED_COLOR_NAME: Final = "led_color_name"
ATTR_LED_EFFECT: Final = "led_effect"
ATTR_LAST_TRIGGERED: Final = "last_triggered"
ATTR_DESCRIPTION: Final = "description"
ATTR_EFFECTIVE_PRIORITY: Final = "effective_priority"
ATTR_PRIORITY_NAME: Final = "priority_name"

# Error codes from WebSocket API
ERROR_MISSING_ALERT_KEY: Final = "MISSING_ALERT_KEY"
ERROR_ALERT_NOT_FOUND: Final = "ALERT_NOT_FOUND"
ERROR_INVALID_MESSAGE: Final = "INVALID_MESSAGE"
ERROR_INVALID_JSON: Final = "INVALID_JSON"
ERROR_UNKNOWN_COMMAND: Final = "UNKNOWN_COMMAND"

# Reconnection settings
RECONNECT_INTERVAL: Final = 5  # seconds
CONNECTION_TIMEOUT: Final = 10  # seconds

# State values
STATE_ALL_CLEAR: Final = "All Clear"

STARTUP_MESSAGE: Final = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
