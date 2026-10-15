# esphome

ESPHome device configs for my Home Assistant stack.

## Devices

| File | Hardware | Purpose |
| --- | --- | --- |
| [m5stack-echos3r.yaml](m5stack-echos3r.yaml) | M5Stack Atom EchoS3R | Assist voice satellite (wake word, mic/speaker, media player) |
| [ai-thinker-esp32-cam.yaml](ai-thinker-esp32-cam.yaml) | AI-Thinker ESP32-CAM | MJPEG camera source for Frigate, plus a native HA camera entity |
| [esp32-c6-thread-repeater.yaml](esp32-c6-thread-repeater.yaml) | ESP32-C6 | Router-eligible Thread mesh repeater, joins an existing Thread network |
| [lounge-controller.yaml](lounge-controller.yaml) | ESP32 + MPI3501 3.5" touch display + AHT25 | Lounge screen: clock and day, inside and forecast temp and humidity, hot water temp, bin day. Port of `controller-pio`, over the native API instead of MQTT |
| [alarm-clock.yaml](alarm-clock.yaml) | CYD (ESP32-2432S028) | Bedside alarm clock: clock, weather, holiday flag, LDR backlight, touch-to-stop alarm. Port of `AlarmClock-PIO`. Alarms are entities on the device, edited from HA (see [Alarm clock](#alarm-clock)). **Not yet compiled or flashed** |
| [esp32-c6-thread-border-router-rcp.md](esp32-c6-thread-border-router-rcp.md) | ESP32-C6 | *Not ESPHome* — instructions for flashing it as an RCP for HA's OpenThread Border Router add-on |

## Setup

1. Copy the secrets template and fill in real values:
   ```bash
   cp secrets.yaml.example secrets.yaml
   ```
2. Generate a fresh API encryption key per device (don't reuse one across devices):
   ```bash
   openssl rand -base64 32
   ```
3. For the Thread repeater, grab the operational dataset from Home Assistant:
   **Settings -> Devices & services -> Thread -> (your network) -> Show
   credentials -> Operational Dataset TLVs**.

`secrets.yaml` is gitignored — never commit it.

## Alarm clock

[alarm-clock.yaml](alarm-clock.yaml) plus one reusable
[alarm-clock/alarm-slot.yaml](alarm-clock/alarm-slot.yaml) per alarm. It
validates (`esphome config`, and the pytest suite) and has been run on the
real board: display, touch, backlight and the Ring Alarm Now / Stop buttons
work, as does a scheduled alarm firing (and Once Only switching it off). The
Skip Holidays rule is not yet tried.

[alarm-clock/dashboard.yaml](alarm-clock/dashboard.yaml) is a compact Home
Assistant dashboard for setting the alarms (time, enabled, days, once only,
skip holidays, plus test ring and stop). Paste it into a dashboard's raw
configuration editor; the file header has the details.

**Where alarm data lives.** Each alarm is a set of entities *on the device*:
`Alarm N Time`, `Alarm N Enabled`, `Alarm N Once Only`,
`Alarm N Skip Holidays` and one switch per day. Edit them in Home Assistant
(dashboard, automation, `time.set_value`, `switch.turn_on`, ...) and the
device is told at once and saves the change to its own flash, so alarms
survive reboots and power cuts. The device fires alarms from its own clock
(NTP first, HA time as a fallback), so an HA, broker or wifi outage at 6am
does not stop the alarm. HA remembers the entities but **not their values**:
a replacement device starts with every alarm disabled.

**Holidays.** `Skip Holidays` uses `calendar.workday_sensor_nz_bop_calendar`
(`holiday_entity` substitution). It only applies while HA is connected; if
HA is down the alarm rings regardless, so a stale flag can never make you
sleep through a work day.

**Also exposed to HA:** `Alarm Ringing` (binary sensor, for automations),
and `Ring Alarm Now` / `Stop Alarm` buttons (testing, or stopping it from
elsewhere).

**More alarms:** add another
`alarm_5: !include {file: alarm-clock/alarm-slot.yaml, vars: {n: 5}}` under
`packages:` in `alarm-clock.yaml`. Four are defined; the old firmware had six.

**Differences from the PlatformIO firmware:** no web page and no MQTT; weather
icons are Material Design Icons instead of hand-drawn shapes (the fonts are
downloaded at compile time); the unit tests for the alarm matching,
LDR hysteresis and icon mapping are gone with the code they tested.

## Validating and flashing

```bash
esphome config <file>.yaml    # check the config compiles/validates without building
esphome compile <file>.yaml   # full build
esphome run <file>.yaml       # build, flash, and start logs
```

The AI-Thinker ESP32-CAM has no onboard USB. Mine all sit on an ESP32-CAM-MB
base, which has its own USB port and handles the GPIO0/reset dance for you —
just plug in and flash. Without that base you'll need a USB-TTL adapter
wired to U0T/U0R/GND/5V, with GPIO0 jumpered to GND during flashing only
(details in the yaml's header comment).

### Corporate TLS-interception proxies (e.g. Zscaler)

If `esphome compile` fails with `CERTIFICATE_VERIFY_FAILED` while
downloading PlatformIO packages, it means the shell running the command
doesn't have your org's root CA on the trust path Python's `requests`
library uses. Check that `REQUESTS_CA_BUNDLE` and `SSL_CERT_FILE` point at
a bundle containing your org's root CA (often set repo-wide in
`~/.bashrc`), and that you're using a shell that actually sources it.

## Tests

A pytest suite in [tests/](tests/) catches config regressions before you
flash anything:

```bash
pip install pytest pyyaml
pytest
```

It checks that every yaml file parses, that every `!secret` it references
is documented in `secrets.yaml.example` (and vice versa — no stale unused
secrets), that `secrets.yaml` is gitignored, and — using the real `esphome`
CLI against a throwaway `secrets.yaml` in an isolated temp dir — that every
config actually validates with no schema errors. Network-dependent checks
(configs using a `packages:` github import) skip cleanly instead of failing
when there's no connectivity.
