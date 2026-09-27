# ESP32-C6 as a Thread RCP for Home Assistant's OpenThread Border Router add-on

This isn't an ESPHome YAML, deliberately. ESPHome's `openthread` component
can only make a device join a Thread network as a router (FTD) or end device
(MTD) — it explicitly conflicts with the `wifi` component and has no border
router / NAT64 / DNS64 / border-agent support. That bridging logic lives in
OpenThread Border Router (OTBR) software, which Home Assistant's official
**OpenThread Border Router** add-on already provides — it just needs a Thread
radio to talk to over serial. The ESP32-C6 fills that role by running a
different, much simpler firmware: a Radio Co-Processor (RCP), built straight
from Espressif's ESP-IDF, with no ESPHome involved.

## 1. Build and flash the RCP firmware

Requires the ESP-IDF toolchain (or use Espressif's `espressif/idf` Docker
image if you don't want it installed locally).

```bash
git clone --recursive https://github.com/espressif/esp-idf.git
cd esp-idf && ./install.sh esp32c6 && . ./export.sh

cd examples/openthread/ot_rcp
idf.py set-target esp32c6
idf.py menuconfig
```

In menuconfig, go to:
`Component config -> OpenThread -> Thread Core Features -> Thread Radio Co-Processor Feature`
and make sure **USB RCP** is selected (UART RCP / SPI RCP deselected). This
lets the C6 talk Spinel over its native USB port — no extra wiring needed.

```bash
idf.py build
idf.py -p /dev/ttyACM0 flash   # adjust port to match your board
```

## 2. Plug it in and point the add-on at it

1. Plug the ESP32-C6's USB port into the machine running Home Assistant.
2. On Linux, prefer the stable path over the raw tty node, since `/dev/ttyACMx`
   numbering isn't guaranteed across reboots:
   ```bash
   ls -l /dev/serial/by-id/
   # usb-Espressif_USB_JTAG_serial_debug_unit_XX-XX-XX-XX-XX-XX-if00
   ```
3. In Home Assistant: **Settings -> Add-ons -> Add-on store**, search for
   **OpenThread Border Router**, install it, and point its serial device
   setting at the `by-id` path from above.
4. Start the add-on, then **Settings -> Devices & services -> Add Integration
   -> OpenThread Border Router** to bring the network into HA.

Once this network exists, grab its **Operational Dataset TLVs** from
**Settings -> Devices & services -> Thread -> (your network) -> Show
credentials** — that's the value [esp32-c6-thread-repeater.yaml](esp32-c6-thread-repeater.yaml)
needs in `secrets.yaml` to join the same mesh as a router.

Sources: [Espressif esp-idf `ot_rcp` example](https://github.com/espressif/esp-idf/tree/master/examples/openthread/ot_rcp), [derekmolloy.ie: ESP32-C6-WROOM as an OpenThread RCP for Home Assistant](https://derekmolloy.ie/a-low-cost-thread-border-router-esp32-c6-wroom-as-an-openthread-rcp-for-home-assistant-in-docker/)
