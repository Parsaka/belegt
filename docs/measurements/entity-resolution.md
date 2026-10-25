# Entity resolution: measured on the fixture sample

Measured on 2026-10-25 with `make warehouse` on `tests/fixtures` (74 German installations, 55
distinct operator or parent names). This is the sample, not all of Germany. The full run
needs the cloud phase.

| Decision | Names | Installations |
|---|---|---|
| accepted | 40 | 66 |
| review | 7 | 2 |
| unmatched | 8 | 5 |

Evidence behind the 40 accepted names: 31 by register number plus name, 8 by normalised name,
1 by the LEI the operator reported to the registry.

What the review queue catches, from the real rows:

- *Progroup Paper PM2 GmbH* has the same register number as *Propapier PM2 GmbH* in GLEIF
  (name similarity 0.25). This looks like a renamed company, so a human decides.
- *HRB 6000* belongs to five different GLEIF entities, because register numbers repeat across
  courts. Only *BASF SE* has a matching name, so the number alone is never accepted.

Group roll-up check (2024, verified tonnes CO₂e): *BASF SE* gets 1,520,127 t from 10
installations. That includes the subsidiaries *BASF Schwarzheide GmbH* and *BASF Personal Care
and Nutrition GmbH* through GLEIF ultimate-parent relationships valid in 2024.

Coverage numbers for all of Germany are in `eea_link_stats.json` and `ets_operator_stats.json`
in this folder.
