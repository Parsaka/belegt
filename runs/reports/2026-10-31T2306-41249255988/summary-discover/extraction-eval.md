# Extraction accuracy

36 labelled reports, 144 labels. A figure is correct within 0.5% of the label and from the labelled page.

| split | metric | correct | wrong value | wrong page | missed | spurious | precision | recall |
|---|---|---|---|---|---|---|---|---|
| dev | scope1 | 12 | 1 | 0 | 1 | 1 | 85.7 % | 85.7 % |
| dev | scope2_market | 10 | 2 | 0 | 2 | 1 | 76.9 % | 71.4 % |
| dev | scope2_location | 11 | 1 | 0 | 1 | 1 | 84.6 % | 84.6 % |
| dev | scope3 | 11 | 1 | 0 | 2 | 0 | 91.7 % | 78.6 % |
| dev | **all** | 44 | 5 | 0 | 6 | 3 | 84.6 % | 80.0 % |
| test | scope1 | 11 | 4 | 0 | 2 | 0 | 73.3 % | 64.7 % |
| test | scope2_market | 11 | 3 | 0 | 2 | 0 | 78.6 % | 68.8 % |
| test | scope2_location | 11 | 1 | 0 | 2 | 0 | 91.7 % | 78.6 % |
| test | scope3 | 8 | 1 | 0 | 8 | 0 | 88.9 % | 47.1 % |
| test | **all** | 41 | 9 | 0 | 14 | 0 | 82.0 % | 64.1 % |
| all | scope1 | 23 | 5 | 0 | 3 | 1 | 79.3 % | 74.2 % |
| all | scope2_market | 21 | 5 | 0 | 4 | 1 | 77.8 % | 70.0 % |
| all | scope2_location | 22 | 2 | 0 | 3 | 1 | 88.0 % | 81.5 % |
| all | scope3 | 19 | 2 | 0 | 10 | 0 | 90.5 % | 61.3 % |
| all | **all** | 85 | 14 | 0 | 20 | 3 | 83.3 % | 71.4 % |

## Errors

| report | metric | outcome | label (t, page) | selected (t, page) | selected line |
|---|---|---|---|---|---|
| aurubis-2024 | scope1 | missed | 561,000, p.26 | - |  |
| aurubis-2024 | scope2_market | missed | 522,000, p.26 | - |  |
| aurubis-2024 | scope3 | missed | 4,457,000, p.26 | - |  |
| beiersdorf-2024 | scope1 | wrong_value | 73,072, p.75 | 24,729, p.75 | Gross Scope 1 GHG emissions tCO2e 44,537 24,729 62,682 48,107 107,219 73,072 |
| beiersdorf-2024 | scope2_location | wrong_value | 82,059, p.75 | 55,659, p.75 | Gross location-based Scope 2 GHG emissions tCO2e 60,132 55,659 23,757 26,502 83,889 82,059 |
| beiersdorf-2024 | scope2_market | wrong_value | 1,745, p.75 | 1,464, p.75 | Gross market-based Scope 2 GHG emissions tCO2e 16,187 1,464 16,616 281 32,803 1,745 |
| beiersdorf-2024 | scope3 | wrong_value | 2,040,295, p.75 | 1,533,218, p.75 | Total significant Scope 3 GHG emissions tCO2e 1,902,600 1,533,218 506,723 507,077 2,409,323 2,040,295 |
| bmw-2024 | scope1 | wrong_value | 672,542, p.195 | 42,959, p.197 | Scope 1 42,959 |
| bmw-2024 | scope2_market | wrong_value | 164,421, p.195 | 21,942, p.197 | Scope 2 (market-based)2 21,942 |
| bmw-2024 | scope3 | missed | 130,297,238, p.196 | - |  |
| brenntag-2024 | scope3 | missed | 29,841,798, p.111 | - |  |
| deutsche-bahn-2024 | scope1 | missed | 1,070,000, p.79 | - |  |
| deutsche-bahn-2024 | scope2_market | missed | 2,720,000, p.79 | - |  |
| deutsche-bahn-2024 | scope3 | missed | 6,320,000, p.79 | - |  |
| dhl-2024 | scope2_location | missed | 730,000, p.78 | - |  |
| dhl-2024 | scope2_market | missed | 80,000, p.78 | - |  |
| dhl-2024 | scope3 | missed | 32,030,000, p.78 | - |  |
| evonik-2024 | scope2_market | wrong_value | 1,670,000, p.137 | 830,000, p.137 | Scope 2 Fremdbezug Strom, marktbezogen 0,70 0,83 |
| heidelberg-materials-2024 | scope1 | spurious | - | 61,100,000, p.125 | Absolute Brutto-CO2-Emissionen (Scope 1) – 61,2 61,1 Mio t |
| heidelberg-materials-2024 | scope2_location | spurious | - | 4,800,000, p.125 | und Wärme (Scope 2) – or tsbasierter Ansatz – 4,4 4,8 Mio t |
| heidelberg-materials-2024 | scope2_market | spurious | - | 4,200,000, p.125 | und Wärme (Scope 2) – mark tbasierter Ansatz – 4,5 4,2 Mio t |
| henkel-2024 | scope1 | wrong_value | 405,621, p.167 | 220,463, p.167 | Scope 1 (t CO2e) from steam, heat and electricity, and other used by Henkel 360,792 n.a. 220,463 n.a. n.a. n.a. n.a. n.a |
| henkel-2024 | scope3 | missed | 37,676,071, p.167 | - |  |
| k-s-2024 | scope2_location | missed | 100,000, p.101 | - |  |
| k-s-2024 | scope2_market | missed | 200,000, p.101 | - |  |
| k-s-2024 | scope3 | missed | 3,000,000, p.101 | - |  |
| mercedes-benz-2024 | scope3 | missed | 128,900,000, p.154 | - |  |
| mvv-2024 | scope1 | missed | 2,588,000, p.68 | - |  |
| mvv-2024 | scope3 | missed | 4,517,000, p.68 | - |  |
| salzgitter-2024 | scope1 | wrong_value | 10,135,000, p.160 | 10,724,000, p.160 | Scope-1-THG-Bruttoemissionen (Tt CO2e) 10.724 0.35 6.900 |
| salzgitter-2024 | scope2_location | wrong_value | 338,000, p.160 | 366,000, p.160 | Standortbezogene Scope-2-THG-Bruttoemissionen (Tt CO2e) 366 338 |
| salzgitter-2024 | scope2_market | wrong_value | 279,000, p.160 | 531,000, p.160 | Marktbezogene Scope-2-THG-Bruttoemissionen (Tt CO2e) 531 79 0 |
| salzgitter-2024 | scope3 | wrong_value | 17,048,000, p.160 | 21,460,000, p.160 | Gesamte indirekte (Scope-3)THG-Bruttoemissionen (Tt CO2e) 21.460 7.048 17.600 |
| volkswagen-2024 | scope1 | wrong_value | 3,300,000, p.291 | 1,370,000, p.469 | Scope 1 GHG emissions in million t CO 2e 1.37 |
| volkswagen-2024 | scope2_location | missed | 4,200,000, p.291 | - |  |
| volkswagen-2024 | scope2_market | wrong_value | 1,100,000, p.291 | 90,000, p.469 | Scope 2 GHG emissions (market-based) in million t CO2e 0.09 |
| volkswagen-2024 | scope3 | missed | 408,580,000, p.292 | - |  |
