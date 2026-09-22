# Guardian algorithm prototype

This directory contains a replayable model of the YAML Guardian policy. It does
not connect to Home Assistant or control the charger.

It pauses a charging EV after 30 seconds above 6.0 kW, then resumes only after a
10-minute minimum pause and two minutes below 0.5 kW. The output is an auditable
list of pause, resume, and alert decisions.

Run the automated tests:

```sh
python3 -m unittest discover -s tests -v
```

Replay an exported P1 history file:

```sh
python3 -m tests.replay tests/test1.csv
```

The replay assumes each P1 reading stays in effect until the next sample and
that the EV was charging for the entire file. For a useful future replay, export
Ohme status and power alongside P1 history. The replay reports decisions only;
it does not modify the historical trace after a simulated pause.

## Home Assistant helpers (out of date)

Before enabling `ev-capacity-guardian.yaml`, create these two Toggle helpers in
Home Assistant's Settings → Devices & services → Helpers:

- `input_boolean.ev_guardian_yielding`
- `input_boolean.ev_guardian_quiet`

They allow the YAML automation to preserve the Guardian pause and sustained
quiet states across separate meter triggers.
