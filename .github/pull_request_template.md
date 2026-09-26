## Species

<!-- species: <common name> (<Scientific name>) -->

Closes #

## Validate report

<!-- Paste the output of:
uv run tools/validate.py species/<slug> --write-attribution --report
It must show no errors. -->

## Checklist

- [ ] Closes the linked species-request issue
- [ ] Validate report pasted above, with no errors
- [ ] `species/<slug>/ATTRIBUTION.md` regenerated (`--write-attribution`) and committed
- [ ] Activity curves generated with `tools/fetch_activity.py` for every suggested region
- [ ] Previewed and checked every pose (`idle`, each locomotion mode, `perched` if applicable)
- [ ] Licences preferred CC0/CC BY where available; any CC BY-SA or NC source is justified below
- [ ] No personal data, local paths, hostnames, or tokens anywhere in the diff
- [ ] One species per PR

## Non-CC0/CC-BY sources (if any)

<!-- Justify each CC BY-SA, ODbL, or NC source here: why nothing better was available. -->
