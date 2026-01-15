"""WebSocket client for LightStack integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable
import uuid

import aiohttp

from .const import (
    CONNECTION_TIMEOUT,
    RECONNECT_INTERVAL,
    WS_CMD_CLEAR_ALERT,
    WS_CMD_CLEAR_ALL_ALERTS,
    WS_CMD_GET_STATE,
    WS_CMD_PING,
    WS_CMD_TRIGGER_ALERT,
    WS_EVENT_COMMAND_RESULT,
    WS_EVENT_ERROR,
)

_LOGGER = logging.getLogger(__name__)


class LightStackWebSocketError(Exception):
    """Exception for LightStack WebSocket errors."""


class LightStackConnectionError(LightStackWebSocketError):
    """Exception for connection errors."""


class LightStackCommandError(LightStackWebSocketError):
    """Exception for command errors."""

    def __init__(self, code: str, message: str):
        """Initialize the error."""
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class LightStackWebSocket:
    """WebSocket client for LightStack."""

    def __init__(
        self,
        host: str,
        port: int,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the WebSocket client."""
        self._host = host
        self._port = port
        self._session = session
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._listeners: list[Callable[[str, dict[str, Any]], None]] = []
        self._pending_commands: dict[str, asyncio.Future] = {}
        self._running = False
        self._listen_task: asyncio.Task | None = None
        self._reconnect_task: asyncio.Task | None = None
        self._connected = False
        self._server_version: str | None = None

    @property
    def url(self) -> str:
        """Return the WebSocket URL."""
        return f"ws://{self._host}:{self._port}/api/v1/ws"

    @property
    def connected(self) -> bool:
        """Return True if connected to the WebSocket."""
        return self._connected and self._ws is not None and not self._ws.closed

    @property
    def server_version(self) -> str | None:
        """Return the server version if known."""
        return self._server_version

    async def connect(self) -> dict[str, Any]:
        """Connect to the WebSocket and return initial state.

        Returns:
            The initial state received from connection_established event.

        Raises:
            LightStackConnectionError: If connection fails.
        """
        try:
            _LOGGER.debug("Connecting to LightStack WebSocket at %s", self.url)
            self._ws = await asyncio.wait_for(
                self._session.ws_connect(self.url),
                timeout=CONNECTION_TIMEOUT,
            )
            self._connected = True
            self._running = True

            # Wait for connection_established message
            initial_msg = await asyncio.wait_for(
                self._ws.receive(),
                timeout=CONNECTION_TIMEOUT,
            )

            if initial_msg.type == aiohttp.WSMsgType.TEXT:
                data = initial_msg.json()
                if data.get("type") == "connection_established":
                    event_data = data.get("data", {})
                    self._server_version = event_data.get("server_version")
                    _LOGGER.info(
                        "Connected to LightStack server version %s",
                        self._server_version,
                    )
                    return event_data.get("state", {})
                raise LightStackConnectionError(
                    f"Unexpected initial message type: {data.get('type')}"
                )
            raise LightStackConnectionError(
                f"Unexpected WebSocket message type: {initial_msg.type}"
            )

        except asyncio.TimeoutError as err:
            self._connected = False
            raise LightStackConnectionError(
                f"Timeout connecting to LightStack at {self.url}"
            ) from err
        except aiohttp.ClientError as err:
            self._connected = False
            raise LightStackConnectionError(
                f"Failed to connect to LightStack at {self.url}: {err}"
            ) from err

    async def start_listening(self) -> None:
        """Start listening for WebSocket messages."""
        if self._listen_task is not None and not self._listen_task.done():
            return

        self._listen_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        """Listen for incoming WebSocket messages."""
        if self._ws is None:
            return

        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = msg.json()
                        await self._handle_message(data)
                    except ValueError:
                        _LOGGER.error("Failed to parse WebSocket message: %s", msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    _LOGGER.error(
                        "WebSocket error: %s",
                        self._ws.exception() if self._ws else "Unknown",
                    )
                    break
                elif msg.type in (
                    aiohttp.WSMsgType.CLOSE,
                    aiohttp.WSMsgType.CLOSED,
                    aiohttp.WSMsgType.CLOSING,
                ):
                    _LOGGER.debug("WebSocket connection closed")
                    break
        except Exception as err:
            _LOGGER.error("Error in WebSocket listener: %s", err)
        finally:
            self._connected = False
            # Notify listeners of disconnection
            await self._notify_listeners("disconnected", {})

    async def _handle_message(self, data: dict[str, Any]) -> None:
        """Handle an incoming WebSocket message."""
        event_type = data.get("type", "")
        event_data = data.get("data", {})

        _LOGGER.debug("Received WebSocket message: %s", event_type)

        # Handle command responses
        if event_type == WS_EVENT_COMMAND_RESULT:
            command_id = event_data.get("command_id")
            if command_id and command_id in self._pending_commands:
                future = self._pending_commands.pop(command_id)
                if not future.done():
                    future.set_result(event_data)
            return

        # Handle errors
        if event_type == WS_EVENT_ERROR:
            command_id = event_data.get("command_id")
            if command_id and command_id in self._pending_commands:
                future = self._pending_commands.pop(command_id)
                if not future.done():
                    future.set_exception(
                        LightStackCommandError(
                            event_data.get("code", "UNKNOWN"),
                            event_data.get("message", "Unknown error"),
                        )
                    )
            else:
                _LOGGER.error(
                    "LightStack error: %s - %s",
                    event_data.get("code"),
                    event_data.get("message"),
                )
            return

        # Notify listeners of other events
        await self._notify_listeners(event_type, event_data)

    async def _notify_listeners(
        self, event_type: str, event_data: dict[str, Any]
    ) -> None:
        """Notify all listeners of an event."""
        for listener in self._listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_type, event_data)
                else:
                    listener(event_type, event_data)
            except Exception as err:
                _LOGGER.error("Error in WebSocket listener callback: %s", err)

    def add_listener(
        self, callback: Callable[[str, dict[str, Any]], None]
    ) -> Callable[[], None]:
        """Add a listener for WebSocket events.

        Returns:
            A function to remove the listener.
        """
        self._listeners.append(callback)

        def remove_listener() -> None:
            if callback in self._listeners:
                self._listeners.remove(callback)

        return remove_listener

    async def send_command(
        self,
        command_type: str,
        data: dict[str, Any] | None = None,
        wait_for_result: bool = True,
        timeout: float = 10.0,
    ) -> dict[str, Any] | None:
        """Send a command to the server.

        Args:
            command_type: The type of command to send.
            data: Optional data to include with the command.
            wait_for_result: Whether to wait for a command result.
            timeout: Timeout in seconds for waiting for result.

        Returns:
            The command result if wait_for_result is True.

        Raises:
            LightStackConnectionError: If not connected.
            LightStackCommandError: If the command fails.
        """
        if not self.connected:
            raise LightStackConnectionError("Not connected to LightStack")

        command_id = str(uuid.uuid4())
        message: dict[str, Any] = {
            "type": command_type,
            "id": command_id,
        }
        if data:
            message["data"] = data

        _LOGGER.debug("Sending command: %s (id: %s)", command_type, command_id)

        if wait_for_result:
            future: asyncio.Future[dict[str, Any]] = asyncio.Future()
            self._pending_commands[command_id] = future

        try:
            await self._ws.send_json(message)

            if wait_for_result:
                return await asyncio.wait_for(future, timeout=timeout)
            return None

        except asyncio.TimeoutError:
            self._pending_commands.pop(command_id, None)
            raise LightStackCommandError(
                "TIMEOUT", f"Command {command_type} timed out"
            ) from None

    async def ping(self) -> bool:
        """Send a ping command to check connection health.

        Returns:
            True if ping was successful.
        """
        try:
            result = await self.send_command(WS_CMD_PING)
            return result is not None and result.get("result", {}).get("pong", False)
        except LightStackWebSocketError:
            return False

    async def get_state(self) -> dict[str, Any]:
        """Get the current alert state.

        Returns:
            The current alert state.
        """
        result = await self.send_command(WS_CMD_GET_STATE)
        if result is None:
            return {}
        return result.get("result", {})

    async def trigger_alert(
        self,
        alert_key: str,
        priority: int | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Trigger an alert.

        Args:
            alert_key: The unique identifier for the alert.
            priority: Optional priority override (1-5).
            note: Optional note for audit trail.

        Returns:
            The command result.
        """
        data: dict[str, Any] = {"alert_key": alert_key}
        if priority is not None:
            data["priority"] = priority
        if note is not None:
            data["note"] = note

        result = await self.send_command(WS_CMD_TRIGGER_ALERT, data)
        return result or {}

    async def clear_alert(
        self,
        alert_key: str,
        note: str | None = None,
    ) -> dict[str, Any]:
        """Clear an alert.

        Args:
            alert_key: The alert to clear.
            note: Optional note for audit trail.

        Returns:
            The command result.
        """
        data: dict[str, Any] = {"alert_key": alert_key}
        if note is not None:
            data["note"] = note

        result = await self.send_command(WS_CMD_CLEAR_ALERT, data)
        return result or {}

    async def clear_all_alerts(self, note: str | None = None) -> dict[str, Any]:
        """Clear all active alerts.

        Args:
            note: Optional note for audit trail.

        Returns:
            The command result.
        """
        data: dict[str, Any] = {}
        if note is not None:
            data["note"] = note

        result = await self.send_command(WS_CMD_CLEAR_ALL_ALERTS, data)
        return result or {}

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._running = False
        self._connected = False

        # Cancel pending commands
        for command_id, future in list(self._pending_commands.items()):
            if not future.done():
                future.cancel()
        self._pending_commands.clear()

        # Cancel listen task
        if self._listen_task is not None and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        # Close WebSocket
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        self._ws = None

        _LOGGER.debug("Disconnected from LightStack WebSocket")

    async def reconnect(self) -> dict[str, Any] | None:
        """Attempt to reconnect to the WebSocket.

        Returns:
            The initial state if reconnection succeeds, None otherwise.
        """
        await self.disconnect()

        try:
            initial_state = await self.connect()
            await self.start_listening()
            return initial_state
        except LightStackConnectionError as err:
            _LOGGER.warning("Failed to reconnect to LightStack: %s", err)
            return None

    async def maintain_connection(self) -> None:
        """Maintain the WebSocket connection with automatic reconnection."""
        while self._running:
            if not self.connected:
                _LOGGER.info("Attempting to reconnect to LightStack...")
                initial_state = await self.reconnect()
                if initial_state is not None:
                    await self._notify_listeners(
                        "reconnected", {"state": initial_state}
                    )
                else:
                    await asyncio.sleep(RECONNECT_INTERVAL)
                    continue

            # Wait for disconnection or check periodically
            await asyncio.sleep(RECONNECT_INTERVAL)

            # Ping to verify connection is still alive
            if self.connected and not await self.ping():
                _LOGGER.warning("LightStack connection appears dead, reconnecting...")
                self._connected = False
