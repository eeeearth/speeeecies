# Evidence and behaviour before review

This is the required research checklist referenced by `AGENTS.md`. Apply it
to new records and to the fields you change in existing records. The schema
and `schema/v0.1/licenses.json` define the accepted format and licence policy.
An old recipe or review comment cannot override them.

## 1. Establish the taxon and scope

- Resolve GBIF and iNaturalist identifiers at their own providers. Check the
  scientific name, rank, status and accepted-name relationship. Optional
  identifiers need the same check. Omit an optional identifier you cannot verify.
- Check for the taxon under accepted names and synonyms in current `main`,
  open PRs and issue history. Reuse an existing record when it represents the
  same taxon. Explain genuine disagreements between taxonomic authorities.
- State which issue regions you will support. Check local presence and
  native/introduced status from distribution evidence. Occurrences can include
  introduced populations, captive animals, vagrants or misidentifications.
- Read the complete current record before editing it. List the fields and
  regions the contribution adds or intentionally changes.

## 2. Verify what each source actually supports

Open the source. Confirm that its title, authors, DOI and taxon agree with the
claim. A plausible citation or search snippet is insufficient. Use the actual
dataset row and column, paper table, or page section. Read the variable
definitions before transforming values. For example, EltonTraits `Diet-Vunk`
means vertebrates of unknown type.

Check the licence for the material you use. The website's general terms can
differ from a linked dataset or image. Record attribution and the checked URL
in `sources`; include an access date or the check date in the PR evidence note.
CC BY-SA and ODbL are allowed. Non-commercial material is a last resort:
identify the exact affected fields and the usable permissive alternatives you
checked. Do not widen provenance coverage to an NC source when a permissive
source already supports that field.

Use provenance paths narrow enough to describe their evidence. A source for
body mass cannot support all of `traits`. Copying a source reference from an
example does not establish coverage for the new animal.

Separate these cases in the provenance note:

| Case | Required explanation |
|---|---|
| Direct observation or published estimate | Source locator, units, population and statistic where relevant |
| Conversion or calculation | Source inputs and the operation used, with `derived: true` |
| Authored simulation estimate | State that it is authored, explain the rationale and uncertainty, and distinguish supporting context from a measured value |
| Missing evidence | Omit optional fields; identify a blocker when a required field has no defensible value |

Apply the schema's meaning to the value:

- `lifespan_y` asks for typical wild lifespan. A captive or wild maximum is
  evidence about a different statistic. Never rename it or divide it by an
  arbitrary factor to manufacture a typical value. This field is required;
  omission will fail. A defensible proxy must disclose its inputs, limitations
  and low confidence. If no defensible estimate is possible, explain the gap.
- Keep adult mass, mass range, length and wingspan measurements distinct.
  Wing chord is a different measurement from wingspan. Do not invent a fixed
  multiplier. Optional measurements can be omitted.
- Presence/absence diet flags do not establish percentages. Label a modelled
  diet allocation as authored and account for every source category used.
- Breeding, calling, migration and dormancy dates need the population or
  region they describe. Avoid extending local observations to a whole species.
- Rendering conventions and biological traits have separate definitions.
  Check the schema's limb-count convention instead of inferring anatomy from
  a mesh part count. Document ambiguous mappings.

## 3. Inspect activity output

Use `tools/fetch_activity.py` and retain its query URLs, query dates, licences,
counts and provenance. Verify that each provider query uses the intended taxon
and geography. For a subdivision, verify both provider place identifiers.
Do not label national observations as a subdivision sample.

Inspect all twelve months, the source tier and `usable` flags. The current
default observation threshold is 300. GBIF's total may include records without
a month, while the monthly bins only contain month-bearing records. Report
both when they differ materially. A total above the threshold alone does not
prove that every month is well sampled.

If evidence is insufficient:

1. Try a suitable permissive source and check the filters; do not automatically
   widen to non-commercial data when a usable permissive query already exists.
2. If only a broader geography is defensible, report that geography honestly
   and explain which requested region is still unsupported.
3. If a provisional curve or neutral fallback is necessary, explicitly label
   it as an authored fallback with its rationale and retain the real counts
   and failed usability flags. Do not claim fabricated observations or a
   successful empirical fetch. Explain the simulation effect in the PR.
4. If no defensible fallback fits the animal, leave the region or contribution
   incomplete and describe the evidence needed to finish it.

Zero observations are not proof of seasonal absence. Check whether low-count
zeros would suppress a year-round resident. A neutral fallback is also a
modelling choice; it can be wrong for a migrant or hibernating animal.

## 4. Trace the behaviour that will execute

Read the selected program, including defaults and substituted parameters.
Its name or description is insufficient. Reusing a program saves work only
when its actions fit the animal.

- **Movement:** every reachable gait must be declared and have the appropriate
  supported pose. `Climb` and `Burrow` have no built-in pose; describe the
  rendering limitation. Ground-feeding birds may walk rather than hop.
- **Feeding:** food-resource tags must match the diet, and the intended feeding
  actions must be reachable. A fish/invertebrate diet with only one reachable
  food action needs an explanation or a correction.
- **Time:** check dawn, daytime, dusk and night. For an FSM, examine exits
  from every active state when daylight or temperature changes; testing only
  the transition out of shelter can leave an animal active all night.
- **Calendar:** write out the actual enabled month set after substitution.
  `month_in` is a set, so `[8, 12]` contains two months. Include interior
  months and year boundaries only when the evidence supports them. Check each
  region and hemisphere represented by the record.
- **Other actions:** nesting, perching, swimming, fleeing and roosting must fit
  the animal. A waterfowl record cannot inherit songbird hopping and nesting
  solely because the shared program passes validation.

Use a species-local program when shared defaults cannot express the supported
behaviour. Explain any simplification. An acknowledged contradiction remains
a defect; a `derived` note does not resolve it. Changes to shared programs
need review of every existing user.

Add focused regression tests when a new program, transformation or shared-data
change creates a meaningful failure risk. Assert outcomes such as an exact
month set, reachable food actions or preserved regional rows. Avoid tests that
merely copy every literal in the new record. Fixtures must work in a shallow
checkout without old Git commits, private files or a live API dependency.

## 5. Preserve shared records and finish the public checks

Compare against the latest base before requesting review. Preserve unrelated
fields and existing activity regions, source entries and provenance. Explain
every intentional removal or replacement, including refreshed curves that
change an installed locale's inputs. Resolve conflicts field by field.

Run the commands in `AGENTS.md` and inspect the results. Regenerate attribution
after the last source change. Check every supported declared pose and report
which ones you actually viewed. Passing schema validation cannot verify
biology; static preview inspection cannot verify a full live scene.

For a review-ready PR, provide these compact summaries in the PR template:

- **Evidence:** taxon resolution and any disagreements; source locators and
  transformations for mass, lifespan, diet and seasonal/range claims you add
  or change; NC fields and alternatives considered. Refer to precise
  provenance entries instead of duplicating their full contents.
- **Activity:** requested and delivered regions, provider scope, counts/tier,
  and any missing, unusable or authored fallback series.
- **Behaviour:** selected program, actual season months, day/night handling,
  gait and feeding fit, and limitations checked.
- **Validation:** tested commit, command results, warnings and inspected poses.
  Identify incomplete work and leave its checkbox unchecked.

Draft PRs can preserve partial work. Request review when the public acceptance
criteria are met, or when a clearly stated question needs maintainer input.
After feedback, link each resolution to its commit and rerun checks affected
by the change. Verify reviewer suggestions against sources too.

## Why these checks exist

The links below show historical review findings. Check the current head before
attributing a defect to a repaired PR:

- [#109](https://github.com/eeeearth/speeeecies/pull/109): a DOI resolved to an
  unrelated paper, and hand-estimated activity was presented as observed data.
- [#110](https://github.com/eeeearth/speeeecies/pull/110) and
  [#158](https://github.com/eeeearth/speeeecies/pull/158): country-code,
  diet-column and identifier-namespace errors.
- [#99](https://github.com/eeeearth/speeeecies/pull/99),
  [#101](https://github.com/eeeearth/speeeecies/pull/101) and
  [#166](https://github.com/eeeearth/speeeecies/pull/166): month-set, night-exit
  and hemisphere errors in otherwise valid records.
- [#155](https://github.com/eeeearth/speeeecies/pull/155): incompatible
  waterfowl behaviour and a sparse curve suppressing an active fox.
- [#189](https://github.com/eeeearth/speeeecies/pull/189): replacement of shared
  records dropped existing regional activity data.
- [#118](https://github.com/eeeearth/speeeecies/pull/118) and
  [#178](https://github.com/eeeearth/speeeecies/pull/178): later reviews corrected
  earlier licence interpretations and distinguished unverified suggested
  values from checked source evidence.
