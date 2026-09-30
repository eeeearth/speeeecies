# Per-species recipes

One block per open species-request issue. `fleet.sh` copies the block whose
`<!-- recipe:N -->` marker matches the issue it is spawning into that agent's
brief, under the "Your recipe" heading. The block is advice, not a contract:
if the repository disagrees with it, trust the repository and say so in the
PR.

Every recipe names one existing record to copy. Copying an existing record
and changing every field that belonged to the old animal is the reliable
path; a record written from a blank file will not validate first try.

Common to all recipes:

- External identifiers are pre-supplied in the issue body under "Data
  pointers". Paste them into `external.gbif_usage_key` and
  `external.inat_taxon_id` rather than re-deriving them.
- `Climb` and `Burrow` are legal `locomotion_modes` but have no pose in
  `body-plans.json`. Declare the mode, skip the pose.
- Poses are the minimum the host animates: `idle`, one per locomotion mode
  in {walk, trot, gallop, hop, slither, swim, fly, glide}, plus `perched`
  if `traits.perching` is true. Declaring a pose for a mode the species
  does not use is what makes a penguin flap.
- `provenance` is where reviewers look first. Every number traces to a
  source id. For pure judgement (`wariness`, `look`, behaviour `params`)
  set `derived: true` with `note: "judgement"`.
- If you shoehorn a shared behaviour program onto a species it does not
  quite fit, set `provenance["behavior"]` to `derived: true` with a note
  saying which part is wrong. Reviewers would rather read an honest note
  than spot the mismatch.

## Europe

<!-- recipe:2 -->
### Common blackbird (Turdus merula) — record already exists

`species/turdus-merula/` is already on `main`. Do not create it.

1. Read the record and the issue. The issue asks for `DE`, `FR`, `GB`, `PL`;
   the record only carries `GB`, `GB-ENG`.
2. Fetch what is missing, one run per region:
   `uv run tools/fetch_activity.py turdus-merula --region DE --write`
   and the same for `FR` and `PL`.
3. Correct anything you find that is actually wrong for this species, and
   say in the PR that you did.
4. Re-validate, re-run `--write-attribution`, commit, open the PR titled
   `species: Common blackbird (Turdus merula)` with `Closes #2`.
<!-- /recipe:2 -->

<!-- recipe:3 -->
### European hedgehog (Erinaceus europaeus) — record already exists

`species/erinaceus-europaeus/` is already on `main`. Do not create it.

1. The issue asks for `DE`, `DK`, `GB`, `NL`; the record carries only
   `GB`, `GB-ENG`. Fetch `DE`, `DK`, `NL` with `fetch_activity.py --write`.
2. The record uses `seasonal.strategy: Hibernation`. Check that
   `seasonal.phases` includes a `dormancy` phase and that `seasonal.triggers`
   are present and populated — the validator requires triggers with a
   dormant strategy, and this is the field most likely to be thin.
3. Fix anything genuinely wrong, then validate, regenerate attribution,
   and open the PR titled `species: European hedgehog (Erinaceus europaeus)`
   with `Closes #3`.
<!-- /recipe:3 -->

<!-- recipe:4 -->
### Eurasian red squirrel (Sciurus vulgaris)

Copy: `species/sciurus-carolinensis/` — same genus of small arboreal rodent.

Behaviour: `fsm-ground-forager-v1` (shared), and it fits. The issue asks for
a "new arboreal forager program"; you do not need one. Use the shared
program and override its sun params to the diurnal values the grey squirrel
uses (`rest_sun_lo_deg: -90`, `rest_sun_hi_deg: -6`) so it rests at night
rather than through the day.

Override from the template: `id`, `slug`, `external`, `taxonomy`,
`common_names`, `conservation`, `range`, `range.koppen`, every `traits`
field, `habitat`, `seasonal`, `activity.regions`, `vocalizations`, all of
`look`, and every `sources` entry. Regions are `DE`, `FI`, `GB`, `IT`.

The grey squirrel's `activity.regions` are `GB`, `GB-ENG` — do not carry
them over. Its sources are its own; none of them describe *vulgaris*.
Red squirrels are strongly associated with mast but also take buds and
eggs; `traits.diet` must still sum to 1.
<!-- /recipe:4 -->

<!-- recipe:5 -->
### Common pipistrelle (Pipistrellus pipistrellus) — needs its own behaviour

Copy: `species/erithacus-rubecula/` for a small flying bird's shape, then
override heavily. Do **not** use a quadruped template: a bat's wings are
forelimbs, so `look.body_plan` is `biped_winged`.

- `traits.flight: Powered`, `traits.limb_count: 2`
- `traits.locomotion_modes: [Fly]` (`Hover` is also legal if you want to
  argue for it)
- `traits.thermoregulation: Endotherm`, `traits.skin: Fur`,
  `traits.size_class: Tiny`, `traits.nest_type: Cavity`
- `traits.activity_pattern: Nocturnal`
- `look.proportions`: `wing_aspect` around 5 (the highest the schema
  allows), `leg_length_ratio` around 0.05, `tail_ratio` around 0.4,
  `beak_ratio` around 0.2, `ear_ratio` around 1.5
- Poses: `idle`, `fly`, `perched`, `rest`. There is no hang pose in the
  schema, so `perched` is a stylisation — mark that as judgement.

Behaviour: none of the three shared programs fits. `bt-perching-songbird-v1`
eats by hopping from a perch; `fsm-ground-forager-v1` assumes terrestrial
gait; `fsm-anuran-nocturnal-v1` is the wrong taxon. Write
`species/pipistrellus-pipistrellus/behavior.json` against
`schema/v0.1/behavior-program.schema.json` and explain why in the PR.

A workable shape is a `fsm` with states `roost -> emerge -> aerial_forage
-> return -> roost`, driven by sun angle: `emerge_sun_deg: -6`,
`return_sun_deg: -12`, `flee_m: 10`, `flee_gait: fly`,
`food_tag: invertebrate`. The id must match
`^(fsm|bt)-[a-z0-9]+(-[a-z0-9]+)*-v[0-9]+$`.

Regions: `DE`, `ES`, `FR`, `GB`.
<!-- /recipe:5 -->

## Asia

<!-- recipe:9 -->
### Eurasian tree sparrow (Passer montanus)

Copy: `species/passer-domesticus/` — the house sparrow, same genus, same
behaviour program, same `food_tag: seed`.

Behaviour: `bt-perching-songbird-v1` (shared), keep the params as they are.
The tree sparrow really is a cavity nester, so the template's
`nest_type: Cavity` is already right.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `range.koppen`, `traits`, `habitat`, `seasonal`,
`activity.regions`, `vocalizations`, `look.palette` (the tree sparrow has a
chestnut crown and a black cheek spot that the house sparrow lacks — the
palette is the field most visibly wrong if you skip it), and every
`sources` entry. Regions are `CN`, `JP`, `KR`, `TW`.
<!-- /recipe:9 -->

<!-- recipe:10 -->
### Common myna (Acridotheres tristis)

Copy: `species/pica-pica/` — a bold, vocal, ground-foraging corvid-analogue
with `Walk`, `Hop`, `Fly`.

Behaviour: `bt-perching-songbird-v1` (shared). Override `food_tag` to a
diet split between `fruit` and `invertebrate` rather than the magpie's
pure `invertebrate`; the magpie's proportions are also larger than a myna's,
so tighten them.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`,
all of `look`, and every `sources` entry. Regions are `BD`, `IN`, `LK`, `TH`.
Keep one or two vocalizations, not a dozen — a myna's repertoire is real but
long, and two well-sourced entries beat ten thin ones.
<!-- /recipe:10 -->

<!-- recipe:11 -->
### Oriental magpie-robin (Copsychus saularis)

Copy: `species/erithacus-rubecula/` — a small perching insectivorous
songbird with a full pose set including `glide`.

Behaviour: `bt-perching-songbird-v1` (shared), keep it. It is noted for an
unusually varied song, so keep several `vocalizations` entries and set
`time_windows` to `[DawnChorus, Day, Dusk]`.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `range.koppen`, `traits`, `habitat`, `seasonal`,
`activity.regions`, all of `look`, and every `sources` entry. Regions are
`IN`, `MY`, `SG`, `TH`.
<!-- /recipe:11 -->

<!-- recipe:12 -->
### Asian common toad (Duttaphrynus melanostictus)

Copy: `species/bufo-bufo/` — the European common toad, same genus-level
shape and the same behaviour program. This is close to a rename-and-refetch
job.

Behaviour: `fsm-anuran-nocturnal-v1` (shared). `min_temp_c` and
`max_temp_c` still apply. `call_m1`/`call_m2` are month integers for the
breeding call window and will need to move: the European toad's window is a
northern-spring one, and this species calls across a tropical Asian range.
Set them to what the sources support and mark them derived if you are
inferring from a relative.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`,
`activity.regions`, and every `sources` entry. Regions are `IN`, `LK`, `MY`,
`TH`.
<!-- /recipe:12 -->

## Africa

<!-- recipe:16 -->
### Vervet monkey (Chlorocebus pygerythrus) — needs its own behaviour

Copy: `species/sciurus-carolinensis/` for a small quadruped's proportions
only, then override heavily. `look.body_plan` is `quadruped`.

- `traits.social.structure: Group`, `traits.social.group_size: [5, 30]`
- `traits.activity_pattern: Diurnal`, `traits.thermoregulation: Endotherm`
- `traits.locomotion_modes: [Walk, Climb]` — no pose for `Climb`
- `look.proportions`: `tail_ratio` around 1.5 (a long vervet tail),
  `leg_length_ratio` around 0.55, `shoulder_height_m` around 0.5
- Diet split across `fruit`, `invertebrate` and `browse`, summing to 1

Behaviour: none of the three shared programs fits. `bt-perching-songbird-v1`
is the wrong taxon; `fsm-ground-forager-v1` models a lone forager and cannot
express a troop with sentinels. Write
`species/chlorocebus-pygerythrus/behavior.json` and explain why in the PR.

A workable shape is an `fsm` with states `forage -> sentinel -> groom ->
rest`, params `sentinel_interval_s: 300`, `social_distance_m: 15`,
`food_tag: invertebrate`.

Regions: `KE`, `TZ`, `UG`, `ZA`.
<!-- /recipe:16 -->

<!-- recipe:17 -->
### Laughing dove (Spilopelia senegalensis)

Copy: `species/columba-livia/` — same family (Columbidae), same behaviour
program.

Behaviour: `bt-perching-songbird-v1` (shared), with `food_tag: seed` and
`song: coo` kept from the template. The laughing dove is considerably
smaller than a rock dove, so tighten the proportions rather than inheriting
them.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`
(the call is a coo, not a song), all of `look`, and every `sources` entry.
Regions are `EG`, `KE`, `NG`, `ZA`.
<!-- /recipe:17 -->

<!-- recipe:18 -->
### Hadada ibis (Bostrychia hagedash)

Copy: `species/pica-pica/` for the `biped_winged` shape, then override the
proportions hard — an ibis is not a magpie.

- `traits.locomotion_modes: [Walk, Fly]` — no `perched` pose, this bird
  forages on the ground
- `traits.size_class: Medium`, `traits.skin: Feathers`
- `look.proportions`: `leg_length_ratio` around 1.3 (long stilt legs; the
  schema allows up to 1.5), `beak_ratio` at or near 2 (the long decurved
  bill, which is the max the schema allows), `neck_angle_deg` around 60
- `habitat.use`: it probes wet ground, so give `aquatic` real weight

Behaviour: the issue asks for a "new ground-probing bird program".
`bt-perching-songbird-v1` will not do — it eats from a perch. Write
`species/bostrychia-hagedash/behavior.json` and explain why in the PR. A
workable shape is an `fsm` with states `wade -> probe -> swallow -> rest`,
params `water_within_m: 5`, `probe_depth_s: 8`,
`food_tag: invertebrate`.

Regions: `KE`, `UG`, `ZA`.
<!-- /recipe:18 -->

<!-- recipe:19 -->
### Guttural toad (Sclerophrys gutturalis)

Copy: `species/bufo-bufo/` — anuran, `fsm-anuran-nocturnal-v1`, near
verbatim apart from the identity fields.

Behaviour: `fsm-anuran-nocturnal-v1` (shared). Move `call_m1`/`call_m2` to
the Southern Hemisphere: the European toad's window will be wrong by about
six months. Derive them from a source and say which.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`,
`activity.regions`, and every `sources` entry. Regions are `KE`, `MZ`, `TZ`,
`ZA`.
<!-- /recipe:19 -->

## South America

<!-- recipe:23 -->
### Rufous hornero (Furnarius rufus)

Copy: `species/erithacus-rubecula/` — a small perching bird with a full
pose set.

Behaviour: `bt-perching-songbird-v1` (shared). It forages on the ground, so
include the `walk` pose in addition to `hop`, `fly` and `perched`.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`,
all of `look`, and every `sources` entry. Two fields deserve care:

- `nest_type: Platform` — the hornero builds a mud oven, which is closer to
  a platform than to a cup or a cavity.
- `traits.diet`: it eats insects and seeds, so split between
  `invertebrate` around 0.6 and `seed` around 0.4 rather than taking the
  robin's pure `invertebrate`.

Regions: `AR`, `BR`, `PY`, `UY`.
<!-- /recipe:23 -->

<!-- recipe:24 -->
### Rufous-bellied thrush (Turdus rufiventris)

Copy: `species/turdus-merula/` — the same genus, and the same behaviour
program. This is the closest copy in the repository for this species.

Behaviour: `bt-perching-songbird-v1` (shared), unchanged.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `range.koppen`, `traits`, `habitat`, `seasonal`,
`activity.regions`, `vocalizations`, and every `sources` entry.
`look.palette` is the one that matters visibly: this thrush is rufous below
and brown above, where the blackbird is uniformly dark. Leave it and the
record is a blackbird with a new name.

Regions: `AR`, `BR`, `PY`, `UY`.
<!-- /recipe:24 -->

<!-- recipe:25 -->
### Common marmoset (Callithrix jacchus) — judgement call on behaviour

Copy: `species/sciurus-carolinensis/` for a small arboreal quadruped's
proportions, then override.

- `traits.thermoregulation: Endotherm`, `traits.skin: Fur`
- `traits.social.structure: Group`, `traits.social.group_size: [3, 15]`
- `traits.activity_pattern: Diurnal`
- `traits.locomotion_modes: [Walk, Climb]`
- `look.proportions`: `tail_ratio` around 1.2 (a long marmoset tail, and
  non-prehensile, so mark that as judgement)
- Diet split: `fruit` around 0.4, `invertebrate` around 0.3, `browse`
  around 0.2, `nectar` around 0.1

Behaviour: the issue asks for a "new arboreal forager program".
`fsm-ground-forager-v1` is what the grey squirrel uses and it runs; the
mismatch is that marmosets are diurnal troops with social calls, which it
does not model. Two defensible answers, and the PR must say which you took:

- **Pragmatic**: use `fsm-ground-forager-v1` and set
  `provenance["behavior"]` to `derived: true` with a note that troop
  behaviour is not modelled. This is what the repository already does for
  imperfect fits, and it is fine.
- **Honest**: write `species/callithrix-jacchus/behavior.json` with states
  `forage -> social_groom -> sentinel -> rest`.

Either way, the diurnal sun params matter: the grey squirrel template
overrides them to rest overnight, and a diurnal marmoset needs the same.

Regions: `BR` (single region — the issue asks for no others).
<!-- /recipe:25 -->

<!-- recipe:26 -->
### Argentine black and white tegu (Salvator merianae) — judgement call on behaviour

Copy: `species/vulpes-vulpes/` for a `Medium` quadruped's proportions, then
override the reptile specifics hard.

- `traits.thermoregulation: Ectotherm` — the template says `Endotherm`
- `traits.skin: Scales` — the template says `Fur`
- `traits.size_class: Medium` (keep; keep `mass_kg` consistent with it)
- `traits.locomotion_modes: [Walk]`, `traits.perching: false`
- `look.proportions`: `leg_length_ratio` around 0.4, `tail_ratio` around
  1.8, `ear_ratio` around 0.1
- `seasonal.strategy: Brumation` — legal in the schema, and the right one
  for a large lizard. (`Aestivation` is also legal if your sources support
  it; pick the one you can source and say which.)

Behaviour: the issue asks for a "new basking reptile program".
`fsm-ground-forager-v1` runs but has no basking mechanic, because it has no
thermoregulation in it at all.

- **Pragmatic**: use `fsm-ground-forager-v1` with
  `forage_gait: walk`, `flee_gait: walk`, a diet split across
  `invertebrate` and `vertebrate`, and
  `provenance["behavior"]` = `derived: true` with a note that basking is
  not modelled.
- **Honest**: write `species/salvator-merianae/behavior.json` with states
  `bask -> forage -> burrow` and temperature triggers.

Regions: `AR`, `BR`, `PY`, `UY`.
<!-- /recipe:26 -->

## Oceania

<!-- recipe:30 -->
### Rainbow lorikeet (Trichoglossus moluccanus)

Copy: `species/psittacula-krameri/` — a parrot, same behaviour program.

Behaviour: `bt-perching-songbird-v1` (shared) with `food_tag: nectar` and
`derived: true` on the behaviour provenance, because a lorikeet's feeding is
nectar and fruit, not seed. Poses: `idle`, `hop`, `fly`, `perched`, `rest`.
The vocalization is a screech, so set the call accordingly rather than
describing it as song.

Watch the taxonomy. GBIF may match this name to a synonym rather than the
accepted one. If you set `taxonomy.status: Synonym`, then
`taxonomy.accepted_id` is **required** and the validator will fail without
it. Confirm the accepted usage key from the GBIF match response and cite it.

Regions: `AU` (single region).
<!-- /recipe:30 -->

<!-- recipe:31 -->
### Common brushtail possum (Trichosurus vulpecula) — judgement call on behaviour

Copy: `species/sciurus-carolinensis/` — a small arboreal quadruped.

Behaviour: `fsm-ground-forager-v1` (shared), and here the template's sun
params are the trap. The grey squirrel template overrides
`rest_sun_lo_deg: -90` / `rest_sun_hi_deg: -6` because it is **diurnal** and
rests overnight. The brushtail possum is **nocturnal** and rests through the
day, so it needs the program's *default* sun params
(`rest_sun_lo_deg: 10`, `rest_sun_hi_deg: 90`) — delete the template's
override rather than editing its numbers. Getting this backwards is the
single most likely error in this record.

- `traits.thermoregulation: Endotherm`, `traits.skin: Fur`
- `traits.activity_pattern: Nocturnal`
- `traits.social.structure: Solitary`
- `traits.locomotion_modes: [Walk, Climb]`
- Diet: `browse` around 0.6, `fruit` around 0.3, `invertebrate` around 0.1

Behaviour fits the shared program well enough. Set
`provenance["behavior"]` to `derived: true` with a note that arboreal
denning is not modelled. An honest bespoke program with states
`forage_arboreal -> den -> forage_ground -> den` is also acceptable.

Regions: `AU`, `NZ`.
<!-- /recipe:31 -->

<!-- recipe:32 -->
### Australian magpie (Gymnorhina tibicen)

Copy: `species/pica-pica/` — a corvid-analogue with the same
`Walk, Hop, Fly` locomotion set and the same behaviour program.

Behaviour: `bt-perching-songbird-v1` (shared), keep the params.

Override: `id`, `slug`, `external`, `taxonomy`, `common_names`,
`conservation`, `range`, `traits`, `habitat`, `seasonal`, `vocalizations`,
all of `look`, and every `sources` entry. `look.palette` is the visible
one: this bird is black and white where the magpie is black and white but
with a very different distribution, and reviewers check the palette against
the source. The call is a carolling warble, so describe it as such.

Regions: `AU` (single region).
<!-- /recipe:32 -->

<!-- recipe:33 -->
### Eastern blue-tongued lizard (Tiliqua scincoides) — judgement call on behaviour

Copy: `species/apodemus-sylvaticus/` or `species/erinaceus-europaeus/` for
a small quadruped's proportions, then override the reptile specifics.
`look.body_plan` is `quadruped` — the schema has no reptile plan, and
`quadruped` is documented as covering lizards. `serpentine` is for snakes
and legless lizards only; do not use it here.

- `traits.thermoregulation: Ectotherm`, `traits.skin: Scales`
- `traits.activity_pattern: Diurnal`
- `traits.defense: Freeze` (`Hide` is also legal)
- `traits.locomotion_modes: [Walk]`, `traits.perching: false`
- `look.proportions`: `leg_length_ratio` around 0.15 (very short legs),
  `torso_aspect` around 2.5, `tail_ratio` around 0.8
- `look.extra_parts`: a blue tongue is the field's namesake and is worth
  adding if the schema's part shape allows it; mark it as judgement
- Diet: `invertebrate` around 0.4, `fruit` around 0.3, `browse` around 0.3
- `seasonal.strategy: Brumation`

Behaviour: the issue asks for a "new basking reptile program".
`fsm-ground-forager-v1` runs but has no basking mechanic.

- **Pragmatic**: use `fsm-ground-forager-v1` with
  `food_tag: invertebrate` and
  `provenance["behavior"]` = `derived: true` noting basking is unmodelled.
- **Honest**: write `species/tiliqua-scincoides/behavior.json` with states
  `bask -> forage -> shelter` and temperature triggers.

Regions: `AU` (single region).
<!-- /recipe:33 -->

## Antarctica

Antarctic notes that apply to all four: the only region available is `AQ`,
and it is thin. Expect the activity curve to come back sparse or empty for
some species. If it does, say so explicitly in the PR and mark the affected
`provenance` with `confidence: Low` rather than dropping the region silently
or inventing a curve. All four are `Endotherm` with `Feathers` or `Fur`.

<!-- recipe:37 -->
### Adelie penguin (Pygoscelis adeliae) — needs its own behaviour

Copy: `species/erithacus-rubecula/` for the `biped_winged` base, then
override heavily. A penguin is a bird, so `look.body_plan` stays
`biped_winged` — what changes is that it does not fly.

- `traits.flight: None` — legal, and the point of the record
- `traits.locomotion_modes: [Walk, Swim]`
- `traits.thermoregulation: Endotherm`, `traits.skin: Feathers`
- `traits.social.structure: Colony`, `traits.social.group_size` large
- `traits.nest_type: Ground` (they lay on pebbles)
- `look.proportions`: `leg_length_ratio` around 0.25, `wing_aspect` around
  2, `tail_ratio` around 0.3, `beak_ratio` around 0.6
- Poses: `idle`, `walk`, `swim`, `rest` — **no `fly`, no `glide`, no
  `perched`**. Declaring a fly pose is how a penguin ends up flapping.

Behaviour: none of the three shared programs models diving. Write
`species/pygoscelis-adeliae/behavior.json` and explain why in the PR. Shape:
`fsm` with states `colony -> commute -> dive_forage -> haul_out -> colony`,
params `dive_depth_m: 20`, `food_tag: fish`, and a colonial group size.

Diet must split between `fish` and `invertebrate` (krill), summing to 1.

Region: `AQ`.
<!-- /recipe:37 -->

<!-- recipe:38 -->
### Emperor penguin (Aptenodytes forsteri) — needs its own behaviour

Everything in the Adelie penguin recipe applies, at a larger scale:

- `traits.size_class: Medium` (the Adelie template may say `Small`; make
  `mass_kg` consistent with whichever you choose — the validator enforces
  this pairing)
- larger `look.proportions` throughout
- `traits.flight: None`, `locomotion_modes: [Walk, Swim]`, poses `idle`,
  `walk`, `swim`, `rest` only

Behaviour: same as the Adelie's — a bespoke
`species/aptenodytes-forsteri/behavior.json` with the same
`colony -> commute -> dive_forage -> haul_out -> colony` shape. The two
penguins can each have their own program; the schema does not require
bespoke programs to be shared.

Region: `AQ`.
<!-- /recipe:38 -->

<!-- recipe:39 -->
### Weddell seal (Leptonychotes weddellii) — needs its own behaviour

Copy: `species/erinaceus-europaeus/` or `species/vulpes-vulpes/` for the
`quadruped` base. **Do not use `serpentine`** — the issue suggests it, but
`serpentine` is a snake plan and this is a mammal. `quadruped` with very
short legs is the right read.

- `traits.flight` is not applicable; leave it out
- `traits.thermoregulation: Endotherm`, `traits.skin: Fur`
- `traits.locomotion_modes: [Walk, Swim]` — `Walk` for moving over ice
- `traits.social.structure: Colony`, `traits.nest_type: None`
- `look.proportions`: `leg_length_ratio` around 0.1 (flippers as low
  boxes), `torso_aspect` around 2.5, `tail_ratio` around 0.05,
  `beak_ratio` around 0.3
- Poses: `idle`, `walk`, `swim`, `rest` (the `quadruped` plan has all four)
- `seasonal.strategy: ActiveYearRound`

Behaviour: none of the three shared programs models diving. Write
`species/leptonychotes-weddellii/behavior.json` and explain why in the PR.
Shape: `fsm` with states `haul_out -> dive_forage -> haul_out`, params
`dive_depth_m: 600`, `haul_out_hours: 8`, `food_tag: fish`.

Diet splits between `vertebrate` and `fish`.

Region: `AQ`.
<!-- /recipe:39 -->

<!-- recipe:40 -->
### South polar skua (Stercorarius maccormicki) — judgement call on behaviour

Copy: `species/pica-pica/` for the `biped_winged` shape and the
`Walk, Hop, Fly` set, then override.

- `traits.locomotion_modes: [Walk, Fly]` — **no `perched` pose**. A skua
  does not perch and sing; it flies, walks on ice, and stoops.
- `traits.social.structure: Colony`
- `traits.thermoregulation: Endotherm`, `traits.skin: Feathers`
- `habitat.use`: split `ground` and `aerial` roughly evenly
- Diet: `vertebrate` around 0.4, `invertebrate` around 0.3, `fish` around
  0.2, `carrion` around 0.1 — kleptoparasitism is the thing that makes this
  bird what it is, and it belongs in the record
- Poses: `idle`, `walk`, `fly`, `rest`

Behaviour: the issue asks for a "new seabird predator program".
`bt-perching-songbird-v1` is structurally close but its dawn-song-from-a-
perch mechanic is wrong for a skua, and you cannot delete that flow by
editing params.

- **Honest** (preferred here): write
  `species/stercorarius-maccormicki/behavior.json` as a `bt` with states
  `swoop -> steal -> eat -> perch`.
- **Pragmatic**: use `bt-perching-songbird-v1` with a `food_tag` covering
  `small_vertebrate` and `carrion`, and set
  `provenance["behavior"]` = `derived: true` stating that kleptoparasitism
  and the absence of song are not modelled.

Region: `AQ`.
<!-- /recipe:40 -->
