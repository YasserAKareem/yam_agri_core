from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="YAM IoT Gateway", version="0.1.0")

MQTT_HOST = os.environ.get("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "yam/iot/observation")

FRAPPE_URL = os.environ.get("FRAPPE_URL", "")
FRAPPE_SITE = os.environ.get("FRAPPE_SITE", "")

_state: dict[str, Any] = {
	"mqtt_connected": False,
	"mqtt_last_message_at": "",
	"mqtt_last_error": "",
	"mqtt_messages_received": 0,
	"ingest_events": [],
}
_state_lock = threading.Lock()


class ObservationIngestPayload(BaseModel):
	site: str = Field(min_length=1)
	device: str = Field(min_length=1)
	observation_type: str = Field(min_length=1)
	value: float
	unit: str = Field(default="")
	quality_flag: str = Field(default="OK")
	observed_at: str | None = None
	raw_payload: dict[str, Any] | None = None


def _utc_now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _record_ingest_event(source: str, payload: dict[str, Any]) -> None:
	with _state_lock:
		events = _state.get("ingest_events") or []
		events.append(
			{
				"source": source,
				"at": _utc_now_iso(),
				"site": payload.get("site"),
				"device": payload.get("device"),
				"observation_type": payload.get("observation_type"),
				"quality_flag": payload.get("quality_flag"),
			}
		)
		_state["ingest_events"] = events[-200:]


def _transform_mqtt_message(raw: dict[str, Any]) -> dict[str, Any]:
	return {
		"site": str(raw.get("site") or "").strip(),
		"device": str(raw.get("device") or "").strip(),
		"observation_type": str(raw.get("observation_type") or raw.get("metric") or "sensor").strip(),
		"value": float(raw.get("value") or 0),
		"unit": str(raw.get("unit") or ""),
		"quality_flag": str(raw.get("quality_flag") or "OK"),
		"observed_at": raw.get("observed_at"),
		"raw_payload": raw,
	}


def _on_connect(client: mqtt.Client, _userdata: Any, _flags: Any, rc: int, _properties: Any = None) -> None:
	with _state_lock:
		_state["mqtt_connected"] = rc == 0
		if rc != 0:
			_state["mqtt_last_error"] = f"connect_rc={rc}"
	if rc == 0:
		client.subscribe(MQTT_TOPIC, qos=1)


def _on_disconnect(_client: mqtt.Client, _userdata: Any, rc: int, _properties: Any = None) -> None:
	with _state_lock:
		_state["mqtt_connected"] = False
		if rc != 0:
			_state["mqtt_last_error"] = f"disconnect_rc={rc}"


def _on_message(_client: mqtt.Client, _userdata: Any, msg: mqtt.MQTTMessage) -> None:
	payload_text = ""
	try:
		payload_text = msg.payload.decode("utf-8")
		raw = json.loads(payload_text)
		transformed = _transform_mqtt_message(raw)
		_record_ingest_event("mqtt", transformed)
		with _state_lock:
			_state["mqtt_messages_received"] = int(_state.get("mqtt_messages_received") or 0) + 1
			_state["mqtt_last_message_at"] = _utc_now_iso()
	except (ValueError, TypeError) as exc:
		with _state_lock:
			_state["mqtt_last_error"] = f"message_parse_error={exc}; payload={payload_text[:200]}"


def _run_mqtt_loop() -> None:
	client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
	client.on_connect = _on_connect
	client.on_disconnect = _on_disconnect
	client.on_message = _on_message

	while True:
		try:
			client.connect(MQTT_HOST, MQTT_PORT, keepalive=30)
			client.loop_forever(retry_first_connection=True)
		except Exception as exc:  # pylint: disable=broad-except
			with _state_lock:
				_state["mqtt_connected"] = False
				_state["mqtt_last_error"] = f"loop_exception={exc}"
			time.sleep(3)


@app.on_event("startup")
def startup_event() -> None:
	thread = threading.Thread(target=_run_mqtt_loop, daemon=True, name="mqtt-loop")
	thread.start()


@app.get("/health")
def health() -> dict[str, Any]:
	with _state_lock:
		return {
			"status": "ok",
			"service": "iot-gateway",
			"mqtt_connected": bool(_state.get("mqtt_connected")),
			"mqtt_messages_received": int(_state.get("mqtt_messages_received") or 0),
			"mqtt_last_message_at": _state.get("mqtt_last_message_at") or "",
			"mqtt_last_error": _state.get("mqtt_last_error") or "",
			"frappe_target_configured": bool(FRAPPE_URL and FRAPPE_SITE),
		}


@app.get("/status")
def status() -> dict[str, Any]:
	with _state_lock:
		return {
			"status": "ok",
			"mqtt_connected": bool(_state.get("mqtt_connected")),
			"mqtt_messages_received": int(_state.get("mqtt_messages_received") or 0),
			"mqtt_last_message_at": _state.get("mqtt_last_message_at") or "",
			"recent_ingest_events": (_state.get("ingest_events") or [])[-20:],
		}


@app.post("/ingest/observation")
def ingest_observation(payload: ObservationIngestPayload) -> dict[str, Any]:
	transformed = payload.model_dump()
	_record_ingest_event("http", transformed)
	return {
		"status": "accepted",
		"source": "http",
		"site": transformed.get("site"),
		"device": transformed.get("device"),
		"observation_type": transformed.get("observation_type"),
	}
