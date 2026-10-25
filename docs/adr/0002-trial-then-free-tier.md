# ADR 0002: Build during the free trial, run on the free tier

Status: accepted (2026-10-25)

## Context
The budget is 1.50 EUR per month. Some technologies the project demonstrates (GKE, Looker,
Cloud SQL, Dagster) cost far more than that when they run continuously: about 80 USD per month
together, based on list prices for europe-west1. Paid Looker is sold only through sales on
annual terms.

## Decision
Run the full stack during the 90-day GCP free trial, paid by the trial credit. Before the trial
ends, move to a steady state that uses only free-tier services. Document the switched-off parts
with screenshots and label them as temporary.

## Consequences
- The architecture has two runtimes over time: GKE during the trial, Cloud Run afterwards.
  The same container images run on both, and Kubernetes manifests stay tested with kind in CI.
- The measured cost of both states goes into the README; it is part of the story.
