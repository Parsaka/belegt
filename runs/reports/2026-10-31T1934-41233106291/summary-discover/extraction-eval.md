# Extraction accuracy

24 labelled reports, 96 labels. A figure is correct within 0.5% of the label and from the labelled page.

| split | metric | correct | wrong value | wrong page | missed | spurious | precision | recall |
|---|---|---|---|---|---|---|---|---|
| dev | scope1 | 9 | 2 | 0 | 0 | 0 | 81.8 % | 81.8 % |
| dev | scope2_market | 8 | 3 | 0 | 0 | 0 | 72.7 % | 72.7 % |
| dev | scope2_location | 9 | 2 | 0 | 0 | 0 | 81.8 % | 81.8 % |
| dev | scope3 | 9 | 2 | 0 | 0 | 0 | 81.8 % | 81.8 % |
| dev | **all** | 35 | 9 | 0 | 0 | 0 | 79.5 % | 79.5 % |
| test | scope1 | 9 | 4 | 0 | 0 | 0 | 69.2 % | 69.2 % |
| test | scope2_market | 8 | 3 | 0 | 2 | 0 | 72.7 % | 61.5 % |
| test | scope2_location | 7 | 4 | 0 | 1 | 0 | 63.6 % | 58.3 % |
| test | scope3 | 6 | 4 | 0 | 3 | 0 | 60.0 % | 46.2 % |
| test | **all** | 30 | 15 | 0 | 6 | 0 | 66.7 % | 58.8 % |
| all | scope1 | 18 | 6 | 0 | 0 | 0 | 75.0 % | 75.0 % |
| all | scope2_market | 16 | 6 | 0 | 2 | 0 | 72.7 % | 66.7 % |
| all | scope2_location | 16 | 6 | 0 | 1 | 0 | 72.7 % | 69.6 % |
| all | scope3 | 15 | 6 | 0 | 3 | 0 | 71.4 % | 62.5 % |
| all | **all** | 65 | 24 | 0 | 6 | 0 | 73.0 % | 68.4 % |

## Errors

| report | metric | outcome | label (t, page) | selected (t, page) | selected line |
|---|---|---|---|---|---|
| bayer-2024 | scope2_location | wrong_value | 1,650,000, p.148 | 1,790,000, p.148 | Gross location-based Scope 2 GHG emissions 1.79 1.66 1.65 –0.6 – – – – – |
| bayer-2024 | scope3 | wrong_value | 8,380,000, p.148 | 9,990,000, p.148 | Gross Scope 3 GHG emissions 3 9.99 9.18 8.38 –8.7 – – – – – |
| beiersdorf-2024 | scope1 | wrong_value | 73,072, p.75 | 24,729, p.75 | Gross Scope 1 GHG emissions tCO2e 44,537 24,729 62,682 48,107 107,219 73,072 |
| beiersdorf-2024 | scope2_location | wrong_value | 82,059, p.75 | 55,659, p.75 | Gross location-based Scope 2 GHG emissions tCO2e 60,132 55,659 23,757 26,502 83,889 82,059 |
| beiersdorf-2024 | scope2_market | wrong_value | 1,745, p.75 | 1,464, p.75 | Gross market-based Scope 2 GHG emissions tCO2e 16,187 1,464 16,616 281 32,803 1,745 |
| beiersdorf-2024 | scope3 | wrong_value | 2,040,295, p.75 | 1,533,218, p.75 | Total significant Scope 3 GHG emissions tCO2e 1,902,600 1,533,218 506,723 507,077 2,409,323 2,040,295 |
| brenntag-2024 | scope3 | missed | 29,841,798, p.111 | - |  |
| dhl-2024 | scope2_location | missed | 730,000, p.78 | - |  |
| dhl-2024 | scope2_market | missed | 80,000, p.78 | - |  |
| dhl-2024 | scope3 | missed | 32,030,000, p.78 | - |  |
| evonik-2024 | scope2_market | wrong_value | 1,670,000, p.137 | 830,000, p.137 | Scope 2 Fremdbezug Strom, marktbezogen 0,70 0,83 |
| mercedes-benz-2024 | scope3 | missed | 128,900,000, p.154 | - |  |
| rheinmetall-2024 | scope1 | wrong_value | 139,801, p.127 | 114,005, p.127 | Gross Scope 1 GHG emissions 114,005 129,800 139,801 0.1 - - - |
| rheinmetall-2024 | scope2_location | wrong_value | 152,924, p.127 | 131,728, p.127 | Gross location-based Scope 2 GHG emissions 131,728 133,768 152,924 0.1 - - - |
| rheinmetall-2024 | scope2_market | wrong_value | 69,897, p.127 | 132,821, p.127 | Gross market-based Scope 2 GHG emissions 132,821 68,896 69,897 0.0 - - - |
| rheinmetall-2024 | scope3 | wrong_value | 5,838,481, p.127 | 5,965,213, p.127 | Total Gross indirect (Scope 3) GHG emissions 5,965,213 5,965,213 5,838,481 (0.0) - - - |
| salzgitter-2024 | scope1 | wrong_value | 10,135,000, p.160 | 10,724,000, p.160 | Scope-1-THG-Bruttoemissionen (Tt CO2e) 10.724 0.35 6.900 |
| salzgitter-2024 | scope2_location | wrong_value | 338,000, p.160 | 366,000, p.160 | Standortbezogene Scope-2-THG-Bruttoemissionen (Tt CO2e) 366 338 |
| salzgitter-2024 | scope2_market | wrong_value | 279,000, p.160 | 531,000, p.160 | Marktbezogene Scope-2-THG-Bruttoemissionen (Tt CO2e) 531 79 0 |
| salzgitter-2024 | scope3 | wrong_value | 17,048,000, p.160 | 21,460,000, p.160 | Gesamte indirekte (Scope-3)THG-Bruttoemissionen (Tt CO2e) 21.460 7.048 17.600 |
| siemens-energy-2024 | scope1 | wrong_value | 175,000, p.2 | 1,343,077,000, p.2 | Scope 1-3 Total Fiscal year 1,000 metric tons CO 2e 1,343,077 1,107,780 |
| siemens-energy-2024 | scope2_market | missed | 22,000, p.2 | - |  |
| suedzucker-2025 | scope1 | wrong_value | 2,722,192, p.37 | 3,034,307, p.37 | Scope 1 gross GHG emissions 3,034,307 2,722,192 |
| suedzucker-2025 | scope2_location | wrong_value | 446,746, p.37 | 826,133, p.37 | Gross location-based Scope 2 GHG emissions 826,133 446,746 |
| suedzucker-2025 | scope2_market | wrong_value | 344,803, p.37 | 630,636, p.37 | Gross market-based Scope 2 GHG emissions 630,636 344,803 |
| suedzucker-2025 | scope3 | wrong_value | 7,977,385, p.37 | 8,201,684, p.37 | Total Gross indirect (Scope 3) GHG emissions 2 8,201,684 7,977,385 5,741,179 70.0 |
| wacker-2024 | scope1 | wrong_value | 1,212,000, p.159 | 1,285,000, p.159 | Scope 1 GHG gross emissions (kt CO2e) 1,285 1,368 1,212 –11 – – – – |
| wacker-2024 | scope2_location | wrong_value | 1,311,000, p.159 | 1,579,000, p.159 | Location-based Scope 2 GHG gross emissions (kt CO2e) 1,579 1,368 1,311 –4 – – – – |
| wacker-2024 | scope2_market | wrong_value | 1,317,000, p.159 | 2,340,000, p.159 | Market-based Scope 2 GHG gross emissions (kt CO2e) 2,340 1,387 1,317 –5 – – – – |
| wacker-2024 | scope3 | wrong_value | 6,052,000, p.160 | 7,713,000, p.155 | Net zero - Scope 3 - GHG gross emissions (kt CO2e)1,2 7,713 5,358 6,052 13 – – 771 3.6 |
