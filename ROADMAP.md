# Roadmap

Milestone ids are `SPEEEECIES-Mn`; sizes are S (a day or less), M (a few
days), L (a week or more).

| Id | Size | Milestone | Status |
|---|---|---|---|
| SPEEEECIES-M0 | L | Kit v0: format 0.1 schema, three worked examples (red fox, European robin, common toad), validator with behaviour lint and licence policy, activity fetcher, visual check, GitHub Pages site with previewer, agent and human guides, CI, first batch of species requests. | this PR |
| SPEEEECIES-M1 | S | Import path: accepted records flow into the simulation; a round-trip test proves every example imports without hand edits. | next |
| SPEEEECIES-M2 | M | Gallery grows: first community species merged; per-species pages on the site with activity charts, call descriptions and attribution. | |
| SPEEEECIES-M3 | M | Sub-national regions: activity curves and phases at ISO 3166-2 level, with hemisphere-aware defaults and an iNaturalist place lookup. | |
| SPEEEECIES-M4 | M | Behaviour simulator in the browser: tick a program against scripted perceptions and show the state or branch trace, so authors can test behaviour without the engine. | |
| SPEEEECIES-M5 | S | Vocalisation references: link openly licensed recordings (CC0 / CC BY first) per call, with licence checks. | |
| SPEEEECIES-M6 | M | Richer looks: optional per-life-stage models (tadpole, juvenile), seasonal plumage variants, and a larger palette. | |
| SPEEEECIES-M7 | S | Format 0.2: fold in lessons from the first contributions; migration notes and a converter from 0.1. | |
| SPEEEECIES-M8 | L | **Plants, phase 2.** Needs a data-driven plant preset format first: growth form, crown and height, seasonal leaf and flower phases, resource tags (fruit, nectar, host plant), and a block or L-system look. Plant `species-request` issues (labelled `phase-2`) open for work once this lands. | blocked on format |
| SPEEEECIES-M9 | M | Trophic web view: which contributed species eat, shelter in or depend on which others, checked for dangling links. | |
