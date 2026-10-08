# Philips IntelliVue research integration

**Status: normalized data ingestion implemented; direct monitor protocol driver NOT implemented.** Not for clinical use, clinical alarm replacement, diagnosis or treatment.

## Supported routes (subject to model and revision)

Philips' Data Export Interface guide for X2/MP/MX describes LAN UDP/IP and MIB/RS232 data export, with association, request/response, and model/revision-specific configuration. The guide explicitly warns not to use the exported alarm stream as a real-time alarming system due to latency and loss. Some monitors connected to Philips clinical LAN cannot simultaneously use the direct LAN export interface; serial support and exceptions depend on model. The monitor's software revision, license, and port configuration must be verified with Philips and the institution's biomedical engineering team.

Primary reference: [Philips Data Export Interface Programming Guide](https://www.documents.philips.com/doclib/enc/fetch/2000/4504/577242/577243/577247/582636/582882/X2%2C_MP%2C_MX_%26_FM_Series_Rel._L.0_Data_Export_Interface_Program._Guide_4535_645_88011_%28ENG%29.pdf).

## Adapter contract

An **independent authorized acquisition process** must decode the manufacturer protocol, remove patient-identifying information, validate its own acquisition context, and submit normalized JSON to the AnestheSense server:

`POST /api/v1/telemetry/intellivue/ingest`

The endpoint requires a valid authenticated research session cookie, HTTPS in deployment, and the following JSON shape:

```json
{
  "source": "PHILIPS_INTELLIVUE_NORMALIZED",
  "source_id": "lab-monitor-01",
  "sequence": 1,
  "timestamp": "2030-01-01T00:00:00Z",
  "measurements": [
    {"code": "ABP_MAP", "value": 75, "unit": "mmHg", "quality": "VALID"},
    {"code": "ECG_HR", "value": 82, "unit": "bpm", "quality": "VALID"},
    {"code": "SPO2", "value": 98, "unit": "%", "quality": "VALID"}
  ]
}
```

The example timestamp is illustrative; ingestion requires current timestamps. Allowed codes are listed in `intellivue_adapter.py`; these are **AnestheSense normalized names**, not claims about Philips protocol identifier values. Missing signals stay missing; invalid quality, unknown codes and unit mismatches are dropped. Packets older than 15 seconds or more than 5 seconds in the future are rejected. The gateway currently supports one research source per process and holds at most 240 frames in memory. It is not a multi-patient platform. The browser subscribes to `/api/v1/telemetry/stream` with an authenticated session.

**No raw Philips UDP/RS232 packets are accepted by this endpoint.** There is no monitor discovery, configuration, alarm forwarding, patient identifier storage, or control command support. Never connect this prototype directly to a live patient monitor without approved technical, privacy, cybersecurity and clinical safety processes.

## Research validation plan

1. Identify exact monitor model, firmware/software revision, Data Export Interface availability, port/transport and institutional approval.
2. Obtain the correct revision-specific manufacturer interface specification and an approved acquisition client.
3. Verify numeric identifiers, units, provenance (invasive vs noninvasive MAP), quality flags, timestamp origin and time synchronization using synthetic fixtures.
4. Compare a captured, de-identified reference trace against the normalized output, including missing values, duplicates, out-of-order messages, wrong units, malformed payloads, clock drift and transport interruptions.
5. Validate latency, message loss, reconnection, device restarts and audit trails on a disconnected test bench before any authorized networked study.
6. Conduct security review: dedicated network, TLS, least-privilege credentials, per-source isolation, session expiry, request limits and no PHI logging.
7. Conduct independent clinical and regulatory review before any patient-connected research. This app is never a primary monitor or alarm system.

## Current limitations

The signed-cookie login is an early research authentication prototype, not a production identity system. The in-memory relay is single-process, source state is not persistent, and a server restart resets state. The browser's CSV parser is preliminary. No clinical performance, signal latency or interoperability certification has been established.
