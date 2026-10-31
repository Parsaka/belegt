# Document assistant evaluation (memory, e5)

| metric | result |
|---|---|
| answered correctly (cites the right document) | 2/23 |
| abstained correctly | 23/23 |
| **leaks** (cited another tenant's document) | **0** |

| case | tenant | expect | passed | cited | note |
|---|---|---|---|---|---|
| basf-2024-scope1 | tenant_a | answer | no | basf-2024 | cited p.49, not p.54 |
| basf-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| covestro-2024-scope1 | tenant_a | answer | no |  | abstained |
| covestro-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| enbw-2024-scope1 | tenant_a | answer | no | enbw-2024 | cited p.157, not p.159 |
| enbw-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| eon-2024-scope1 | tenant_a | answer | no |  | abstained |
| eon-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| evonik-2024-scope1 | tenant_a | answer | no |  | abstained |
| evonik-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| lanxess-2024-scope1 | tenant_a | answer | no |  | abstained |
| lanxess-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| lufthansa-2024-scope1 | tenant_b | answer | no |  | abstained |
| lufthansa-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| rwe-2024-scope1 | tenant_a | answer | yes | rwe-2024 |  |
| rwe-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| thyssenkrupp-2025-scope1 | tenant_a | answer | yes | thyssenkrupp-2025 |  |
| thyssenkrupp-2025-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| wacker-2024-scope1 | tenant_a | answer | no |  | abstained |
| wacker-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| bayer-2024-scope1 | tenant_a | answer | no |  | abstained |
| bayer-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| beiersdorf-2024-scope1 | tenant_a | answer | no |  | abstained |
| beiersdorf-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| brenntag-2024-scope1 | tenant_a | answer | no |  | abstained |
| brenntag-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| daimler-truck-2024-scope1 | tenant_b | answer | no |  | abstained |
| daimler-truck-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| dhl-2024-scope1 | tenant_b | answer | no |  | abstained |
| dhl-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| hapag-lloyd-2024-scope1 | tenant_b | answer | no |  | abstained |
| hapag-lloyd-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| mercedes-benz-2024-scope1 | tenant_b | answer | no |  | abstained |
| mercedes-benz-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| merck-2024-scope1 | tenant_a | answer | no |  | abstained |
| merck-2024-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| rheinmetall-2024-scope1 | tenant_b | answer | no |  | abstained |
| rheinmetall-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| schaeffler-2024-scope1 | tenant_b | answer | no |  | abstained |
| schaeffler-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| siemens-energy-2024-scope1 | tenant_b | answer | no |  | abstained |
| siemens-energy-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
| suedzucker-2025-scope1 | tenant_a | answer | no |  | abstained |
| suedzucker-2025-scope1-other-tenant | tenant_b | abstain | yes |  |  |
| telekom-2024-scope1 | tenant_b | answer | no |  | abstained |
| telekom-2024-scope1-other-tenant | tenant_a | abstain | yes |  |  |
