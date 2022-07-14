#!/usr/bin/env python3

from flask import Flask, request
from gevent.pywsgi import WSGIServer

import paho.mqtt.client as mqtt

import argparse
import enum
import json
import logging
import sys


_LOGGER = logging.getLogger(__name__)
MQTT = None
TOPIC_PREFIX = None


class Units(enum.Enum):
    DEGREES_F = "°F"
    DEGREES_C = "°C"
    PERCENT_RH = "%"
    PRESSURE_INHG = "inHg"
    DEGREES = "°"
    MPH = "MPH"
    INCHES = "in"
    WATTS_M2 = "W/m²"


class Sensor:
    def __init__(self, name, unit=None, device_class=None, fmap=None):
        self.friendly_name = name
        self.name = name.lower().replace("(", "").replace(")", "").replace(" ", "_")
        self.unit = unit
        self.device_class = device_class
        self.published_config = False
        self.fmap = fmap

    def topic(self, topic):
        return "/".join([TOPIC_PREFIX, "sensor", "ws2902", self.name, topic])

    def handle(self, data):
        _LOGGER.debug(f"{self.name}: {data} {self.unit}")

        if self.fmap is not None:
            data = self.fmap(data)

        MQTT.publish(self.topic("state"), data)

        if not self.published_config:
            config = {}
            config["name"] = self.friendly_name
            config["unique_id"] = "_".join(["ws2902", self.name])
            config["state_topic"] = self.topic("state")
            if self.device_class is not None:
                config["device_class"] = self.device_class
            if self.unit is not None:
                config["unit_of_measurement"] = self.unit.value

            MQTT.publish(self.topic("config"), json.dumps(config), retain=True)
            self.published_config = True


SENSOR_TYPES = {
    "stationtype": Sensor("Station Type"),
    "PASSKEY": Sensor("MAC Address"),
    "dateutc": Sensor("Last Update", device_class="timestamp", fmap=lambda x: x.replace(" ", "T") + "+00:00"),
    "tempinf": Sensor("Indoor Temperature", unit=Units.DEGREES_F, device_class="temperature"),
    "humidityin": Sensor("Indoor Humidity", unit=Units.PERCENT_RH, device_class="humidity"),
    "baromrelin": Sensor("Barometer (relative)", unit=Units.PRESSURE_INHG, device_class="pressure"),
    "baromabsin": Sensor("Barometer (absolute)", unit=Units.PRESSURE_INHG, device_class="pressure"),
    "tempf": Sensor("Temperature", unit=Units.DEGREES_F, device_class="temperature"),
    "humidity": Sensor("Humidity", unit=Units.PERCENT_RH, device_class="humidity"),
    "winddir": Sensor("Wind Direction", unit=Units.DEGREES),
    "windspeedmph": Sensor("Wind Speed", unit=Units.MPH),
    "windgustmph": Sensor("Wind Gust", unit=Units.MPH),
    "maxdailygust": Sensor("Max Wind Gust", unit=Units.MPH),
    "hourlyrainin": Sensor("Hourly Rain", unit=Units.INCHES),
    "eventrainin": Sensor("Event Rain", unit=Units.INCHES),
    "dailyrainin": Sensor("Daily Rain", unit=Units.INCHES),
    "weeklyrainin": Sensor("Weekly Rain", unit=Units.INCHES),
    "monthlyrainin": Sensor("Monthly Rain", unit=Units.INCHES),
    "totalrainin": Sensor("Total Rain", unit=Units.INCHES),
    "solarradiation": Sensor("Solar Radiation", unit=Units.WATTS_M2),
    "uv": Sensor("UV Index"),
}

app = Flask("ws2902-mqtt")


@app.route("/data", methods=["GET"])
def report():
    args = request.args
    _LOGGER.debug("/data" + str(args))

    for key, sensor in SENSOR_TYPES.items():
        if key in args:
            sensor.handle(args.get(key))

    return ""


def main():
    parser = argparse.ArgumentParser(description="ws2902-mqtt")

    parser.add_argument("--port", default=8543, action="store", type=int, help="port to serve HTTP endpoint on")
    parser.add_argument("--log", default="warning", action="store", help="log level")
    parser.add_argument("--prefix", default="homeassistant", action="store", help="mqtt topic prefix")
    parser.add_argument("--mqtt-host", default="localhost", action="store", help="mqtt server host")
    parser.add_argument("--mqtt-port", default=1883, action="store", type=int, help="mqtt server port")
    parser.add_argument("--mqtt-user", default=None, action="store", help="mqtt username")
    parser.add_argument("--mqtt-pass", default=None, action="store", help="mqtt password")

    args = parser.parse_args()

    logging.basicConfig(level=args.log.upper())
    wsgi_log = None
    if args.log.upper() == 'DEBUG':
        wsgi_log = sys.stderr

    global TOPIC_PREFIX
    TOPIC_PREFIX = args.prefix

    client = mqtt.Client()
    if args.mqtt_user is not None:
        client.username_pw_set(args.mqtt_user, args.mqtt_pass)
    client.connect(args.mqtt_host, args.mqtt_port)
    client.loop_start()

    global MQTT
    MQTT = client

    server = WSGIServer(("", args.port), app, log=wsgi_log)
    server.serve_forever()
