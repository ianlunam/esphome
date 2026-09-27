# esphome

ESPHome device configs for my Home Assistant stack.

## Devices

| File | Hardware | Purpose |
| --- | --- | --- |
| [m5stack-echos3r.yaml](m5stack-echos3r.yaml) | M5Stack Atom EchoS3R | Assist voice satellite (wake word, mic/speaker, media player) |
| [ai-thinker-esp32-cam.yaml](ai-thinker-esp32-cam.yaml) | AI-Thinker ESP32-CAM | MJPEG camera source for Frigate, plus a native HA camera entity |
| [esp32-c6-thread-repeater.yaml](esp32-c6-thread-repeater.yaml) | ESP32-C6 | Router-eligible Thread mesh repeater, joins an existing Thread network |
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

## Validating and flashing

```bash
esphome config <file>.yaml    # check the config compiles/validates without building
esphome compile <file>.yaml   # full build
esphome run <file>.yaml       # build, flash, and start logs
```

The AI-Thinker ESP32-CAM has no onboard USB — first flash needs a USB-TTL
adapter, with GPIO0 jumpered to GND during flashing only (details in the
yaml's header comment).

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
