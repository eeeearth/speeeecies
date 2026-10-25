# Nine later species-request batches

This inventory holds 9,000 unpublished GBIF species keys, divided into nine batches of 1,000. They are discovery leads, not accepted GitHub tasks. Each key had at least 300 country-level month-bearing human observations under the recorded CC0/CC BY filters when discovered. The counts and countries are starting points for research, not range or seasonal-activity claims.

The discovery pass found 10,516 distinct GBIF keys across 97 countries. After excluding known and screened keys, 9,117 remained; the 9,000 highest-count leads were staged.

Before publishing a batch, check current GBIF acceptance and exact iNaturalist identity, deduplicate against species records, all issues, open PRs and retained work, and reject unsuitable or domestic-only taxa. Re-run the observation query. Replace rejected keys through a new discovery pass so the public queue receives only screened leads. [The operating rule](species-queue-10000.md) starts that work when fewer than 300 open requests remain, or earlier if active claims leave fewer than 300 available.

The [JSON inventory](species-reserve-2026-10.json) records every key, proposed country, discovery count and assigned batch. Provider identities and biological suitability have not been verified for these later leads.

| Later batch | Leads | Birds | Mammals | Reptiles | Amphibians |
|---:|---:|---:|---:|---:|---:|
| 1 | 1000 | 888 | 44 | 42 | 26 |
| 2 | 1000 | 890 | 45 | 40 | 25 |
| 3 | 1000 | 891 | 43 | 42 | 24 |
| 4 | 1000 | 890 | 42 | 43 | 25 |
| 5 | 1000 | 889 | 44 | 42 | 25 |
| 6 | 1000 | 891 | 43 | 42 | 24 |
| 7 | 1000 | 889 | 43 | 42 | 26 |
| 8 | 1000 | 890 | 43 | 41 | 26 |
| 9 | 1000 | 890 | 43 | 42 | 25 |

Birds dominate the current discovery pool. The reptile discovery source covers squamates only. Later passes should add turtle and crocodilian classes and review the group mix before publication; equal batch sizes do not imply equal group coverage.
