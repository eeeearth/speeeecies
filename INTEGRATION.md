# PR #93 review addendum

The Guttural toad source says males call throughout the year, with October and
November as the main breeding period. The record scopes its breeding phase to
South Africa (`ZA`) and uses those months for its croak season. The shared
`fsm-anuran-nocturnal-v1` program gates calling with one global month pair, so
`call_m1` and `call_m2` are now 10 and 11. The format cannot express a separate
schedule for each region; this setting represents the documented ZA main
breeding window wherever the shared program runs. Rain-driven and regional
variation remains outside the current model.

Suggested PR-body update:

> The shared anuran FSM now gates calls in October and November, matching the
> record's cited main breeding period and croak season. The source says calling
> can occur year-round; the FSM's single global month pair represents the
> record's ZA main breeding window because this format cannot encode regional
> call schedules.

# PR #110 regional-curve review addendum

Prepared on `codex/pr110-magpie-fix-20261010` from current `origin/main`
`fdd777ed1ccb82dbc857210adf432e7d6da96dfc`; reviewed against PR head
`a9a74badb53ba53b2911ae4464cc1c5dfc60ea8f`. Issue #11 has a claim with ETA
2026-10-01, now expired; no duplicate claim comment was posted. Publication is
on hold.

The current-main `Copsychus saularis` record, including its `IN-KA` curve, is
preserved. The only additions are national `IN`, `TH`, `MY`, and `SG` curves,
GBIF-backed source entries, and the verified ITIS identifier (TSN 559432).
GBIF Tier A totals at fetch were 765,636 (IN), 99,378 (TH), 704 (MY), and
20,048 (SG); all exceed the 300 minimum. Curves use GBIF effort-corrected
monthly shares alone. No iNaturalist national source was included, so Singapore
NC-SA and Malaysia CC-BY-SA mixtures from the old PR are avoided. The existing
`IN-KA` row remains byte-for-byte equal to current main, including its existing
NC warning.

Old PR changes to species range, traits, habitat, seasons, behavior, and look
were not copied. The current-main fixes for the Bhutan code (`BT`) and the
EltonTraits `Diet-Vunk` vertebrate share remain intact. ITIS identifies TSN
559432 as valid `Copsychus saularis`; no unsupported multilingual names were
added.

Species validation has zero errors and retains one warning for the unchanged
IN-KA NC source. All-locale validation completed with no errors; self-check
scanned 585 files with zero findings; all three focused regression tests passed.
No behavior or mesh changed, so no new pose preview was needed.

## PR #110 CI test fixture follow-up

The preservation regression now compares the working record against a checked-in
snapshot captured from the branch's actual current-main parent (`fdd777e`), so
hosted tests do not need Git history objects or a path lookup. The test still
compares the entire record after removing only the approved new national rows,
sources, and ITIS additions, and separately checks the full `IN-KA` row exactly.
Species data is unchanged in this follow-up.
