# Extraction accuracy on 37 real reports

How often `belegt reports` picks the right Scope 1, Scope 2 (location- and market-based) and
Scope 3 figure from a German company's annual or sustainability report. Every number here was
measured on GitHub Actions runners against hand labels; nothing is estimated.

## Result

148 labels (37 reports × 4 metrics), measured 2026-10-31:

| | before the rule fixes | after |
|---|---|---|
| dev split (15 reports) | 45.7 % precision, 38.2 % recall | **84.6 %** precision, **80.0 %** recall |
| test split (22 reports) | 61.2 % precision, 44.8 % recall | **80.8 %** precision, **62.7 %** recall |
| all 37 reports | 53.7 % precision, 41.8 % recall | **82.7 %** precision, **70.5 %** recall |

- Precision is the share of selected figures that are right, and recall is the share of labelled
  figures that were found.
- *Before*: run [41230370112](https://github.com/Parsaka/belegt/actions/runs/41230370112),
  commit `27bd2d5`.
- *After*: run [41235204810](https://github.com/Parsaka/belegt/actions/runs/41235204810),
  commit `cd65e9d`.
- Both are scored with the final labels (`evals/reported_metrics.csv`).

Per metric, after the fixes (all 37 reports):

| metric | correct | wrong value | missed | spurious | precision | recall |
|---|---|---|---|---|---|---|
| Scope 1 | 23 | 6 | 3 | 1 | 76.7 % | 71.9 % |
| Scope 2 location-based | 22 | 2 | 3 | 1 | 88.0 % | 81.5 % |
| Scope 2 market-based | 21 | 5 | 5 | 1 | 77.8 % | 67.7 % |
| Scope 3 | 20 | 2 | 10 | 0 | 90.9 % | 62.5 % |

The full report, with every error and the line the extractor chose, is written by the Reports
workflow to `runs/reports/<run>/summary-discover/extraction-eval.md` on the `ops-results`
branch. To reproduce it locally from the published figures:

```
belegt reports-eval <dir with metrics/*.jsonl> --labels evals/reported_metrics.csv
```

## Method

**Reports.** The reports are 37 documents from DAX and MDAX companies for fiscal year 2024
(`dbt/seeds/reports.csv`). Most are annual reports with an ESRS sustainability statement. The
others are:

- older-style annual reports (Heidelberg Materials, Aurubis, MVV);
- a performance-indicator overview (Siemens Energy);
- annual reports whose climate figures sit in a separate report (Siemens, Fraport, Infineon,
  Symrise).

Each report's LEI is checked against GLEIF in the same workflow. The PDFs are copyrighted, so
they are only on the runner and never in Git.

**Labels.** For each report and metric there is one row:

- the value in tonnes for the reporting year;
- the PDF pages that state it (the E1-6 table first, then any summary table that repeats it);
- the figure as printed;
- the table line, at most 200 characters.

Claude labelled the rows by reading the table pages of each report. The Reports workflow prints
those pages on the runner (`probe_pages`, in [scripts/probe_reports.py](../../scripts/probe_reports.py)),
and the parsed header years are checked against them.

The rules for the labels:

- **The group figure for the reporting year.** That means continuing operations where the
  report separates them (Deutsche Bahn), not a segment.
- **An empty value means the document states no such figure.** In that case, selecting one is
  an error ("spurious"). Some examples:
  - Heidelberg Materials gives Scope 1 and 2 only per business line.
  - BMW, Aurubis and Deutsche Bahn give no location-based Scope 2 total.
  - MVV gives Scope 2 without a method.
  - Fraport, Infineon, Siemens and Symrise state no figures at all in these PDFs.
- **Salzgitter's text layer garbles the 2024 column.** For example, the PDF text reads "0.35"
  where the page prints 10.135. The label keeps the printed figure, cross-checked with the
  company's figures as republished on tracenable.com, and is marked with a `text layer:` note.
  The extractor reads the text layer, so these four labels count against it.

**Scoring.** A selected figure is correct when it is within 0.5 % of the label (tables round)
and comes from one of the labelled pages. See
[src/belegt/documents/evaluation.py](../../src/belegt/documents/evaluation.py).

**Splits.**

- The *dev* split has 15 reports:
  - the first six reports;
  - the nine added in the second batch;
  - Rheinmetall, whose header shaped one rule.
- Rule changes were made only for dev failures, each with a test built from the real row
  (`tests/test_metrics.py`). These are the changes:
  - a base-year column without a year;
  - a change column (`2024/2023`);
  - "1,000 tonnes" in a row label;
  - footnote digits glued to header years;
  - header lines with column titles between them;
  - wrapped rows;
  - `Konzern` and `Summe` total rows.
- The *test* split has the 22 reports added afterwards. They were measured as they came: none
  of their failures changed a rule. That the test split also rose, from 61.2 % to 80.8 %
  precision, shows that the rules generalise beyond the reports they were written for.

## What still fails

| cause | reports |
|---|---|
| several entities side by side in one table (Consumer, tesa, Group) | Beiersdorf |
| a summary page outranks the E1-6 table | BMW (p.197, biogenic emissions), Volkswagen (p.469, Volkswagen AG only) |
| figures two lines below their label, or a label split over lines | Volkswagen, Aurubis, K+S, Deutsche Bahn, DHL, Henkel Scope 3 |
| a sub-row read as the total | Henkel Scope 1, Evonik market-based Scope 2 |
| a fiscal-year header (`2024/25`) | Südzucker |
| a unit written as "1,000 metric tons" next to a "Scope 1-3 total" row | Siemens Energy |
| the PDF text layer is garbled | Salzgitter |
| segment figures where the group has no total | Heidelberg Materials (counted as spurious) |

Every selected figure carries its page and table line, and the consistency mart compares
Scope 1 with the ETS sum of the group. So a wrong pick is visible, and a reviewed value can go
into `dbt/seeds/reported_overrides.csv`.
