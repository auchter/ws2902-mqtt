# ws2902-mqtt

This component implements an MQTT bridge for the Ambient Weather WS-2902 weather station, primarily intended to expose the sensor measurements to a Home-Assistant instance.
It exposes an HTTP which the weather station is configured to report measurements to, and publishes those sensor measurements as MQTT topics.
The topics published adhere to the [Home-Assistant MQTT Discovery](https://www.home-assistant.io/docs/mqtt/discovery/) requirements, and so the weather station's sensors will be automatically added as Home-Assistant entities.

## Usage

- Install this package using your method of choice
- Run the server on a machine, specifying the port to serve the HTTP endpoint on, and the connection settings for your MQTT broker
- Use the awnet application to configure your weather station to connect to your server. Be sure the update your firmware to the latest revision! Settings:
  - Protocol Type Same As: Ambient Weather
  - Server IP / Hostname: <your server host>
  - Path: `/data?` (NB: the trailing `?` is important!)
  - Port: `8543` (by default, can be changed by passing `--port` to `ws2902-mqtt`
