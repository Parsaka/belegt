# Document assistant evaluation (bigquery, e5)

| metric | result |
|---|---|
| answered correctly (cites the right document) | 2/2 |
| abstained correctly | 3/3 |
| **leaks** (cited another tenant's document) | **0** |

| case | tenant | expect | passed | cited | note |
|---|---|---|---|---|---|
| tenant-a-own | tenant_a | answer | yes | tenant-a-memo |  |
| tenant-a-asks-for-b | tenant_a | abstain | yes |  |  |
| tenant-b-own | tenant_b | answer | yes | tenant-b-memo |  |
| tenant-b-asks-for-a | tenant_b | abstain | yes |  |  |
| not-in-any-document | tenant_a | abstain | yes |  |  |
