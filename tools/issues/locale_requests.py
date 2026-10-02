#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["jsonschema>=4.18"]
# ///
"""Generate (and optionally post) the `locale-request` GitHub issues.

Every issue body comes from one template (`render_body`) filled from the
PLACES and TAXA tables below, so the set is reproducible: rerun the script
and the Markdown under `tools/issues/out/` comes out the same unless the
tables change.

The table values were looked up once from public APIs and pages:

- centroid and elevation: Wikidata (CC0), `P625` and `P2044` on the item
  named in `wikidata`, rounded to 2 decimals;
- `activity_region`: the ISO 3166-2 code (`P300`) of the subdivision
  Wikidata places the city in;
- `gadm_gid`: GBIF's reverse geocoder (`/v1/geocode/reverse`) at the
  centroid, level 1;
- iNaturalist place ids: `/v1/places/nearby` at the centroid (the
  subdivision for activity curves, the city for species lists);
- candidate species: iNaturalist research-grade species counts for the
  city place (for US places, the county or independent city), filtered by
  hand to animals a garden or courtyard actually sees; GBIF keys from
  `/v1/species/match`, iNaturalist ids from `/v1/taxa`;
- Köppen class: the English Wikipedia article's climate section, marked
  for the contributor to confirm; where the article gives no code, or one
  the import cannot use, `koppen_source` names the source instead (the
  Beck et al. 2018 Köppen-Geiger map, CC BY 4.0).

Usage:
    uv run tools/issues/locale_requests.py            # write tools/issues/out/*.md and lint them
    uv run tools/issues/locale_requests.py --check    # fail if out/ is stale or any body fails the lint
    uv run tools/issues/locale_requests.py --post --dry-run
    uv run tools/issues/locale_requests.py --post     # create missing issues with gh (skips existing titles)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = Path(__file__).resolve().parent / "out"
REPO_URL = "https://github.com/eeeearth/speeeecies"
SITE_URL = "https://eeeearth.github.io/speeeecies/"
LIVE_URL = "https://www.youtube.com/@jt55401/live"
LABEL = "locale-request"
LABEL_COLOR = "fbca04"
LABEL_DESCRIPTION = "A place someone would like added to the live rotation"

# Continent labels already used by species-request issues; north-america is
# created on first use.
CONTINENT_LABELS = {
    "europe": ("c5def5", "Continent: Europe"),
    "asia": ("f9d0c4", "Continent: Asia"),
    "africa": ("fef2c0", "Continent: Africa"),
    "oceania": ("c2e0c6", "Continent: Oceania / Australia"),
    "south-america": ("d4c5f9", "Continent: South America"),
    "north-america": ("bfdadc", "Continent: North America"),
}

# Scientific name -> (common name, GBIF usage key, iNaturalist taxon id, note).
# The note flags where GBIF and iNaturalist disagree on the name.
TAXA: dict[str, tuple[str, int, int, str | None]] = {
    "Acanthis flammea": ("Redpoll", 5231630, 145300, None),
    "Acridotheres tristis": ("Common Myna", 2489005, 204454, None),
    "Agama picticauda": ("Peters's Rock Agama", 5226316, 797597, None),
    "Agelaius phoeniceus": ("Red-winged Blackbird", 9409198, 9744, None),
    "Alopochen aegyptiaca": ("Egyptian Goose", 2498252, 72486, None),
    "Anas platyrhynchos": ("Mallard", 9761484, 6930, None),
    "Anaxyrus americanus": ("American Toad", 2422872, 64968, None),
    "Anaxyrus fowleri": ("Fowler's Toad", 2422905, 64977, None),
    "Anolis carolinensis": ("Green Anole", 2466939, 36514, None),
    "Anser anser": ("Greylag Goose", 2498036, 7018, None),
    "Antigone canadensis": ("Sandhill Crane", 2474953, 508048, "GBIF files it as a synonym of Grus canadensis"),
    "Antrozous pallidus": ("Pallid Bat", 2432339, 40614, None),
    "Aphelocoma woodhouseii": ("Woodhouse's Scrub-Jay", 5844900, 506117, None),
    "Apus apus": ("Common Swift", 5228676, 6638, None),
    "Archilochus alexandri": ("Black-chinned Hummingbird", 5228513, 6433, None),
    "Archilochus colubris": ("Ruby-throated Hummingbird", 5228514, 6432, None),
    "Ardea herodias": ("Great Blue Heron", 9630752, 4956, None),
    "Astur cooperii": ("Cooper's Hawk", 2480621, 1579017, "GBIF uses Accipiter cooperii"),
    "Baeolophus bicolor": ("Tufted Titmouse", 2487887, 13632, None),
    "Bassariscus astutus": ("Ringtail", 2433557, 41676, None),
    "Blarina brevicauda": ("Northern Short-tailed Shrew", 2435862, 63113, None),
    "Bombycilla cedrorum": ("Cedar Waxwing", 2484609, 7428, None),
    "Bostrychia hagedash": ("Hadada Ibis", 5229203, 3743, None),
    "Bradypodion pumilum": ("Cape Dwarf Chameleon", 8683892, 32954, None),
    "Brotogeris tirica": ("Plain Parakeet", 2479562, 19214, None),
    "Bubo virginianus": ("Great Horned Owl", 5959118, 20044, None),
    "Bubulcus ibis": ("Western Cattle-Egret", 2480830, 411086, "iNaturalist uses Ardea ibis"),
    "Bufo bufo": ("European Toad", 5217160, 326296, None),
    "Bufo japonicus": ("Eastern-Japanese Common Toad", 5217143, 1402613, "iNaturalist splits the eastern Japanese population as Bufo formosus; use that taxon id for activity"),
    "Buteo jamaicensis": ("Red-tailed Hawk", 2480542, 5212, None),
    "Buteo lineatus": ("Red-shouldered Hawk", 2480529, 5206, None),
    "Cacatua galerita": ("Sulphur-crested Cockatoo", 2479888, 116834, None),
    "Callipepla gambelii": ("Gambel's Quail", 5228072, 1406, None),
    "Callithrix jacchus": ("Common Marmoset", 5219542, 43373, None),
    "Callithrix penicillata": ("Black-tufted-ear Marmoset", 5219541, 43374, None),
    "Callosciurus finlaysonii": ("Finlayson's Squirrel", 2437399, 45949, None),
    "Calotes versicolor": ("Indian Garden Lizard", 9125207, 31281, None),
    "Calypte anna": ("Anna's Hummingbird", 2476674, 6317, None),
    "Cardinalis cardinalis": ("Northern Cardinal", 2490384, 9083, None),
    "Centropus senegalensis": ("Senegal Coucal", 5231999, 1670, None),
    "Cercopithecus mitis": ("Blue Monkey", 5219578, 43486, None),
    "Chlorocebus pygerythrus": ("Vervet Monkey", 7262034, 68137, None),
    "Chroicocephalus ridibundus": ("Black-headed Gull", 6065824, 144510, None),
    "Chrysemys picta": ("Painted Turtle", 2443133, 39771, None),
    "Cinnyris chalybeus": ("Southern Double-collared Sunbird", 7340753, 145157, None),
    "Cinnyris venustus": ("Variable Sunbird", 7340636, 145188, None),
    "Colaptes auratus": ("Northern Flicker", 2478259, 18236, None),
    "Coloeus monedula": ("Eurasian Jackdaw", 6100954, 336399, None),
    "Columba livia": ("Rock Pigeon", 2495414, 3017, None),
    "Columba palumbus": ("Common Wood-Pigeon", 2495455, 3048, None),
    "Columbina inca": ("Inca Dove", 2495863, 3544, None),
    "Columbina talpacoti": ("Ruddy Ground Dove", 2495858, 3580, None),
    "Copsychus saularis": ("Oriental Magpie-Robin", 2492680, 204491, None),
    "Corvinella corvina": ("Yellow-billed Shrike", 5231300, 12057, None),
    "Corvus albus": ("Pied Crow", 2482519, 8038, None),
    "Corvus brachyrhynchos": ("American Crow", 2482507, 8021, None),
    "Corvus corax": ("Common Raven", 2482492, 8010, None),
    "Corvus cornix": ("Hooded Crow", 2482515, 144757, None),
    "Corvus corone": ("Carrion Crow", 9409796, 204496, None),
    "Corvus macrorhynchos": ("Large-billed Crow", 2482487, 8026, None),
    "Corvus splendens": ("House Crow", 2482499, 8031, None),
    "Crinifer piscator": ("Western Plantain-eater", 2475211, 7248, None),
    "Curaeus curaeus": ("Austral Blackbird", 2484424, 10307, None),
    "Cyanistes caeruleus": ("Eurasian Blue Tit", 2487879, 144849, None),
    "Cyanocitta cristata": ("Blue Jay", 2482593, 8229, None),
    "Cyanopica cyanus": ("Azure-winged Magpie", 7341881, 72785, None),
    "Dasypus mexicanus": ("Mexican Long-nosed Armadillo", 2440779, 1647419, "GBIF uses Dasypus novemcinctus, which iNaturalist splits"),
    "Desmognathus ochrophaeus": ("Allegheny Mountain Dusky Salamander", 2431199, 27390, None),
    "Desmognathus orestes": ("Blue Ridge Dusky Salamander", 2431207, 27405, None),
    "Didelphis albiventris": ("White-eared Opossum", 2439930, 42658, None),
    "Didelphis aurita": ("Big-eared Opossum", 2439928, 42657, None),
    "Didelphis virginiana": ("Virginia Opossum", 2439923, 42652, None),
    "Dryobates pubescens": ("Downy Woodpecker", 9149595, 792988, None),
    "Dryocopus pileatus": ("Pileated Woodpecker", 5228824, 17855, None),
    "Dryophytes cinereus": ("Green Treefrog", 10810025, 1668858, None),
    "Dryophytes japonicus": ("Japanese Tree Frog", 10857535, 1668965, None),
    "Duttaphrynus melanostictus": ("Asian Common Toad", 2422538, 62345, None),
    "Eidolon helvum": ("Straw-coloured Fruit Bat", 2432851, 40827, None),
    "Eptesicus fuscus": ("Big Brown Bat", 2432352, 40509, None),
    "Erethizon dorsatum": ("North American Porcupine", 6066824, 44026, "GBIF spells it Erethizon dorsatus"),
    "Erinaceus europaeus": ("Common Hedgehog", 5219616, 43042, None),
    "Erithacus rubecula": ("European Robin", 2492462, 13094, None),
    "Funambulus palmarum": ("Three-striped Palm Squirrel", 2437246, 45938, None),
    "Furnarius rufus": ("Rufous Hornero", 2485821, 11275, None),
    "Gekko japonicus": ("Japanese Giant Gecko", 2447295, 101316, None),
    "Geococcyx californianus": ("Greater Roadrunner", 2496459, 1986, None),
    "Geothlypis trichas": ("Common Yellowthroat", 2489670, 9721, None),
    "Glaucomys volans": ("Southern Flying Squirrel", 2437338, 46272, None),
    "Gymnorhina tibicen": ("Australian Magpie", 2489450, 8575, None),
    "Haemorhous mexicanus": ("House Finch", 8323485, 199840, None),
    "Haliaeetus leucocephalus": ("Bald Eagle", 2480446, 5305, None),
    "Hemidactylus frenatus": ("Asian House Gecko", 9537238, 51940, None),
    "Hemidactylus mabouia": ("Tropical House Gecko", 5959942, 68492, None),
    "Hemidactylus platyurus": ("Flat-tailed House Gecko", 5816059, 33376, None),
    "Hemidactylus turcicus": ("Mediterranean House Gecko", 5221528, 34435, None),
    "Hemiphaga novaeseelandiae": ("New Zealand Pigeon", 2495905, 204520, None),
    "Hypsipetes amaurotis": ("Brown-eared Bulbul", 7342055, 144910, None),
    "Ictidomys tridecemlineatus": ("Thirteen-lined Ground Squirrel", 7994322, 179988, None),
    "Ictinia mississippiensis": ("Mississippi Kite", 2480719, 5416, None),
    "Intellagama lesueurii": ("Australian Water Dragon", 8161292, 146186, None),
    "Junco hyemalis": ("Dark-eyed Junco", 9362842, 10094, None),
    "Lampropholis delicata": ("Dark-flecked Garden Sunskink", 5225256, 38293, None),
    "Larus delawarensis": ("Ring-billed Gull", 2481134, 4364, None),
    "Lasionycteris noctivagans": ("Silver-haired Bat", 2432341, 40629, None),
    "Lasiurus borealis": ("Eastern Red Bat", 5218543, 40522, None),
    "Leptocoma zeylonica": ("Purple-rumped Sunbird", 7340855, 145146, None),
    "Lepus americanus": ("Snowshoe Hare", 2436794, 43132, None),
    "Lepus californicus": ("Black-tailed Jackrabbit", 2436801, 43130, None),
    "Liolaemus tenuis": ("Blue-Green Smooth-throated Lizard", 2460411, 39111, None),
    "Lithobates pipiens": ("Northern Leopard Frog", 2427185, 66003, None),
    "Litoria peronii": ("Peron's Tree Frog", 2427831, 1633155, "iNaturalist uses Pengilleyia peronii"),
    "Lophoceros nasutus": ("African Gray Hornbill", 8101752, 512166, None),
    "Manorina melanocephala": ("Noisy Miner", 2487365, 12231, None),
    "Marmota monax": ("Groundhog", 2437368, 46095, None),
    "Melanerpes carolinus": ("Red-bellied Woodpecker", 2478106, 18205, None),
    "Melanerpes erythrocephalus": ("Red-headed Woodpecker", 2478130, 18204, None),
    "Meleagris gallopavo": ("Wild Turkey", 9606290, 906, None),
    "Melospiza melodia": ("Song Sparrow", 2492196, 9100, None),
    "Melozone fusca": ("Canyon Towhee", 7341622, 145289, None),
    "Mephitis mephitis": ("Striped Skunk", 5219380, 41880, None),
    "Milvago chimango": ("Chimango Caracara", 2481065, 1432781, "iNaturalist uses Daptrius chimango"),
    "Milvus migrans": ("Black Kite", 5229167, 5268, None),
    "Mimus polyglottos": ("Northern Mockingbird", 5231677, 14886, None),
    "Mimus saturninus": ("Chalk-browed Mockingbird", 5231675, 14878, None),
    "Mimus thenca": ("Chilean Mockingbird", 5231685, 14879, None),
    "Motacilla aguimp": ("African Pied Wagtail", 7405711, 13701, None),
    "Mus musculus": ("House Mouse", 7429082, 44705, None),
    "Myiopsitta monachus": ("Monk Parakeet", 2479407, 19349, None),
    "Myotis austroriparius": ("Southeastern Myotis", 2432451, 40323, None),
    "Myotis lucifugus": ("Little Brown Bat", 2432406, 40346, None),
    "Nerodia sipedon": ("Common Watersnake", 5223334, 29305, None),
    "Notophthalmus viridescens": ("Eastern Newt", 5218390, 27805, None),
    "Numida meleagris": ("Helmeted Guineafowl", 2473341, 1428, None),
    "Nyctereutes procyonoides": ("Mainland Raccoon Dog", 2434552, 855311, None),
    "Nyctereutes viverrinus": ("Japanese Raccoon Dog", 6164330, 855310, "GBIF treats it as Nyctereutes procyonoides viverrinus"),
    "Odocoileus hemionus": ("Mule Deer", 2440974, 42220, None),
    "Odocoileus virginianus": ("White-tailed Deer", 2440965, 42223, None),
    "Onychognathus morio": ("Red-winged Starling", 5230739, 204554, None),
    "Orthotomus sutorius": ("Common Tailorbird", 2493028, 15347, None),
    "Oryctolagus cuniculus": ("European Rabbit", 2436940, 43151, None),
    "Otospermophilus variegatus": ("Rock Squirrel", 7572569, 180008, None),
    "Parus major": ("Great Tit", 9705453, 203153, None),
    "Parus minor": ("Asian Tit", 5844847, 339691, "iNaturalist lumps it into Parus cinereus (Asian tit)"),
    "Passer domesticus": ("House Sparrow", 5231190, 13858, None),
    "Passer montanus": ("Eurasian Tree Sparrow", 5231198, 13851, None),
    "Passerina caerulea": ("Blue Grosbeak", 5230862, 73155, None),
    "Patagioenas picazuro": ("Picazuro Pigeon", 2495287, 3102, None),
    "Pelophylax nigromaculatus": ("Black-spotted Frog", 2426634, 66330, None),
    "Pelophylax perezi": ("Iberian Green Frog", 2426658, 66331, None),
    "Perimyotis subflavus": ("Tricolored Bat", 7665644, 183166, None),
    "Peromyscus leucopus": ("White-footed Mouse", 2438019, 44395, None),
    "Pica hudsonia": ("Black-billed Magpie", 5229487, 143853, None),
    "Pica pica": ("Eurasian Magpie", 5229490, 891696, None),
    "Pica serica": ("Oriental Magpie", 10704098, 827401, None),
    "Pipilo erythrophthalmus": ("Eastern Towhee", 2491205, 9424, None),
    "Pipilo maculatus": ("Spotted Towhee", 9709230, 9420, None),
    "Pipistrellus pipistrellus": ("Common Pipistrelle", 5218465, 40364, None),
    "Piranga rubra": ("Summer Tanager", 2488485, 9915, None),
    "Pitangus sulphuratus": ("Great Kiskadee", 2482755, 16956, None),
    "Pituophis catenifer": ("Gopher Snake", 2453826, 29044, None),
    "Plectrophenax nivalis": ("Snow Bunting", 2491719, 117059, None),
    "Plestiodon finitimus": ("Japanese five-lined skink", 8186233, 318747, None),
    "Plethodon glutinosus": ("Northern Slimy Salamander", 2431539, 27184, None),
    "Pleurodema thaul": ("Chilean Four-eyed Frog", 2423479, 23214, None),
    "Ploceus baglafecht": ("Baglafecht Weaver", 2494061, 13805, None),
    "Ploceus cucullatus": ("Village Weaver", 2494058, 13796, None),
    "Podarcis muralis": ("Common Wall Lizard", 2469188, 55990, None),
    "Podarcis siculus": ("Italian Wall Lizard", 9185677, 337045, None),
    "Poecile atricapillus": ("Black-capped Chickadee", 2487805, 144815, None),
    "Poecile carolinensis": ("Carolina Chickadee", 2487844, 144814, None),
    "Poecile gambeli": ("Mountain Chickadee", 2487825, 144816, None),
    "Procavia capensis": ("Rock Hyrax", 5219598, 43086, None),
    "Procyon lotor": ("Common Raccoon", 5218786, 41663, None),
    "Prosthemadera novaeseelandiae": ("Tūī", 2487029, 12580, None),
    "Pseudacris maculata": ("Boreal Chorus Frog", 2428169, 24255, None),
    "Pseudacris regilla": ("Pacific chorus frog", 2428132, 24259, None),
    "Psittacula krameri": ("Rose-ringed Parakeet", 2479226, 18911, None),
    "Pteropus medius": ("Indian Flying Fox", 5787518, 1641421, None),
    "Pteropus poliocephalus": ("Grey-headed Flying-fox", 5218655, 40905, None),
    "Pycnonotus aurigaster": ("Sooty-headed Bulbul", 2486121, 14626, None),
    "Pycnonotus barbatus": ("Common Bulbul", 2486147, 14588, None),
    "Pycnonotus capensis": ("Cape Bulbul", 2486138, 14594, None),
    "Pycnonotus jocosus": ("Red-whiskered Bulbul", 2486151, 14591, None),
    "Pyrocephalus rubinus": ("Vermilion Flycatcher", 2483647, 16447, None),
    "Quiscalus mexicanus": ("Great-tailed Grackle", 9476062, 9607, None),
    "Quiscalus quiscula": ("Common Grackle", 2484155, 9602, None),
    "Rana temporaria": ("European Common Frog", 2426805, 25591, None),
    "Ranoidea aurea": ("Green-and-Golden Bell Frog", 10595763, 517069, None),
    "Rattus norvegicus": ("Brown Rat", 2439261, 44576, None),
    "Rhinella arenarum": ("Argentine Toad", 5216921, 67093, None),
    "Rhinella ornata": ("Ornate Forest toad", 5216887, 67135, None),
    "Rhipidura fuliginosa": ("New Zealand Fantail", 5231730, 244276, None),
    "Salvator merianae": ("Argentine Black-and-white Tegu", 5227370, 318758, None),
    "Saucerottia beryllina": ("Berylline Hummingbird", 5788537, 1289657, None),
    "Sayornis phoebe": ("Eastern Phoebe", 2483606, 17008, None),
    "Sceloporus consobrinus": ("Prairie Lizard", 2451277, 146413, None),
    "Sceloporus cowlesi": ("Southwestern Fence Lizard", 7566793, 116137, None),
    "Sceloporus grammicus": ("Graphic Spiny Lizard", 2451167, 36262, None),
    "Sciurus aureogaster": ("Red-bellied Squirrel", 5219663, 46009, None),
    "Sciurus carolinensis": ("Eastern Gray Squirrel", 5219681, 46017, None),
    "Sciurus niger": ("Eastern Fox Squirrel", 5219683, 46020, None),
    "Sciurus vulgaris": ("Eurasian Red Squirrel", 8211070, 46001, None),
    "Sclerophrys gutturalis": ("Guttural Toad", 9456514, 517053, None),
    "Sclerophrys pantherina": ("Western Leopard Toad", 10851350, 517449, None),
    "Sclerophrys regularis": ("Egyptian Toad", 10698146, 517048, None),
    "Serinus serinus": ("European Serin", 2494200, 9236, None),
    "Sialia currucoides": ("Mountain Bluebird", 2490935, 12936, None),
    "Sialia sialis": ("Eastern Bluebird", 2490941, 12942, None),
    "Spilopelia chinensis": ("Spotted Dove", 6101224, 1455918, None),
    "Spilopelia senegalensis": ("Laughing Dove", 6101223, 1455922, None),
    "Spinus psaltria": ("Lesser Goldfinch", 5231647, 145308, None),
    "Spinus tristis": ("American Goldfinch", 5231640, 145310, None),
    "Spodiopsar cineraceus": ("White-cheeked Starling", 6100944, 547179, None),
    "Streptopelia orientalis": ("Oriental Turtle-Dove", 2495681, 2927, None),
    "Strix varia": ("Barred Owl", 2497541, 19893, None),
    "Sturnella neglecta": ("Western Meadowlark", 9596413, 9535, None),
    "Sturnus unicolor": ("Spotless Starling", 2489104, 14849, None),
    "Sturnus vulgaris": ("European Starling", 9809229, 14850, None),
    "Sylvilagus audubonii": ("Desert Cottontail", 2436910, 43115, None),
    "Sylvilagus floridanus": ("Eastern Cottontail", 2436886, 43111, None),
    "Tachycineta bicolor": ("Tree Swallow", 2489181, 11935, None),
    "Tadarida brasiliensis": ("Mexican Free-tailed Bat", 2433011, 41301, None),
    "Tamias sibiricus": ("Siberian Chipmunk", 2437450, 520585, "iNaturalist uses Eutamias sibiricus"),
    "Tamias striatus": ("Eastern Chipmunk", 2437438, 46217, None),
    "Tamiasciurus douglasii": ("Douglas's Squirrel", 2437281, 46259, None),
    "Tamiasciurus hudsonicus": ("American Red Squirrel", 2437282, 46260, None),
    "Tamiops mcclellandii": ("Himalayan Striped Squirrel", 7261516, 697692, None),
    "Tarentola mauritanica": ("Moorish Gecko", 2445034, 33602, None),
    "Terrapene carolina": ("Common Box Turtle", 2443173, 39814, None),
    "Terrapene triunguis": ("Three-toed Box Turtle", 8877412, 1544605, None),
    "Thamnophis elegans": ("Western Terrestrial Garter Snake", 2457545, 28398, None),
    "Thamnophis sirtalis": ("Common Garter Snake", 2457522, 28362, None),
    "Thraupis sayaca": ("Sayaca Tanager", 2488622, 10293, None),
    "Threskiornis molucca": ("Australian Ibis", 2480765, 3740, None),
    "Thryothorus ludovicianus": ("Carolina Wren", 2493801, 7513, None),
    "Tiliqua scincoides": ("Common Bluetongue", 2462503, 37456, None),
    "Todiramphus sanctus": ("Sacred Kingfisher", 2475802, 2464, None),
    "Toxostoma curvirostre": ("Curve-billed Thrasher", 5231688, 14912, None),
    "Toxostoma rufum": ("Brown Thrasher", 9479809, 14898, None),
    "Trichoglossus moluccanus": ("Rainbow Lorikeet", 6170530, 980095, "GBIF files it as a synonym of Trichoglossus haematodus"),
    "Trichosurus vulpecula": ("Common Brushtail Possum", 2440254, 42808, None),
    "Trioceros jacksonii": ("Jackson's Chameleon", 8371864, 32807, None),
    "Troglodytes troglodytes": ("Eurasian Wren", 5231438, 145363, None),
    "Turdus abyssinicus": ("Abyssinian Thrush", 7340241, 145081, None),
    "Turdus falcklandii": ("Austral Thrush", 2490775, 12751, None),
    "Turdus iliacus": ("Redwing", 2490781, 12749, None),
    "Turdus merula": ("Eurasian Blackbird", 2490719, 12716, None),
    "Turdus migratorius": ("American Robin", 9510564, 12727, None),
    "Turdus rufiventris": ("Rufous-bellied Thrush", 2490718, 12738, None),
    "Turdus rufopalliatus": ("Rufous-backed Robin", 2490741, 12714, None),
    "Tyrannus forficatus": ("Scissor-tailed Flycatcher", 5229687, 16783, None),
    "Tyrannus tyrannus": ("Eastern Kingbird", 5229688, 16782, None),
    "Tyrannus verticalis": ("Western Kingbird", 5229675, 16791, None),
    "Urocitellus armatus": ("Uinta Ground Squirrel", 8151861, 179994, None),
    "Urocitellus beldingi": ("Belding's Ground Squirrel", 8428945, 179995, None),
    "Urosaurus ornatus": ("Ornate Tree Lizard", 8538855, 36107, None),
    "Vanellus chilensis": ("Southern Lapwing", 5229146, 4867, None),
    "Vanellus miles": ("Masked Lapwing", 5229134, 4872, None),
    "Vulpes lagopus": ("Arctic Fox", 5219303, 233598, None),
    "Vulpes vulpes": ("Red Fox", 5219243, 42069, None),
    "Zenaida asiatica": ("White-winged Dove", 2495370, 3460, None),
    "Zenaida auriculata": ("Eared Dove", 2495358, 3439, None),
    "Zenaida macroura": ("Mourning Dove", 2495347, 3454, None),
    "Zonotrichia albicollis": ("White-throated Sparrow", 5231140, 9184, None),
    "Zonotrichia capensis": ("Rufous-collared Sparrow", 5231103, 9183, None),
    "Zosterops japonicus": ("Warbling White-eye", 9300456, 980262, None),
    "Zosterops lateralis": ("Silvereye", 2489396, 202505, None),
    "Zosterops virens": ("Cape White-eye", 7857709, 472770, None),
}

# National or regional data portals, only where we know one; always check
# each dataset's licence (eBird and many atlas downloads are not open).
ATLASES: dict[str, list[tuple[str, str]]] = {
    "AU": [("Atlas of Living Australia", "https://www.ala.org.au/")],
    "BR": [("SiBBr, Brazil's biodiversity information system", "https://www.sibbr.gov.br/")],
    "CA": [("iNaturalist.ca", "https://inaturalist.ca/")],
    "ES": [("GBIF Spain", "https://www.gbif.es/")],
    "FR": [("OpenObs (INPN)", "https://openobs.mnhn.fr/")],
    "IE": [("National Biodiversity Data Centre", "https://biodiversityireland.ie/")],
    "IN": [("India Biodiversity Portal", "https://indiabiodiversity.org/")],
    "MX": [("NaturaLista (CONABIO)", "https://www.naturalista.mx/")],
    "NZ": [("iNaturalist NZ", "https://inaturalist.nz/")],
    "US": [
        ("iNaturalist", "https://www.inaturalist.org/"),
        ("eBird bar charts, for species lists and seasons (eBird data are not openly licensed)", "https://ebird.org/"),
        ("USGS North American Breeding Bird Survey (public domain)", "https://www.pwrc.usgs.gov/bbs/"),
        ("USGS Nonindigenous Aquatic Species, to check whether a species is introduced (public domain)",
         "https://nas.er.usgs.gov/"),
    ],
}

PLOT_TEMPLATES = ("suburban-lot", "rural-lot", "rowhouse-garden", "street-block", "courtyard")


@dataclass(frozen=True)
class Place:
    id: str
    name: str
    continent: str
    country: str
    region: str  # ISO 3166-2 activity_region
    region_name: str
    lat: float
    lon: float
    tz: str
    koppen: str
    elevation_m: float | None
    wikidata: str
    wikipedia: str
    plot_template: str
    inat_region_place: int
    inat_city_place: int | None
    gadm_gid: str
    species: tuple[str, ...]
    notes: tuple[str, ...] = ()
    # Where the Köppen class comes from, when not the Wikipedia article's climate section.
    koppen_source: str | None = None
    # The species-list place when it is not a city (a county, a parish).
    species_place_name: str | None = None

    @property
    def title(self) -> str:
        return f"Locale: {self.name} ({self.id})"


PLACES: list[Place] = [
    Place(
        "berlin-de", "A Berlin courtyard", "europe", "DE", "DE-BE", "Berlin",
        52.52, 13.38, "Europe/Berlin", "Cfb", 34, "Q64", "Berlin", "courtyard", 12872, 29472, "DEU.3_1",
        ("Passer domesticus", "Turdus merula", "Corvus cornix", "Columba palumbus", "Sturnus vulgaris",
         "Parus major", "Cyanistes caeruleus", "Sciurus vulgaris", "Vulpes vulpes", "Erinaceus europaeus",
         "Procyon lotor", "Bufo bufo"),
        ("Berlin sits on the Cfb/Dfb boundary; Wikipedia gives Cfb.",
         "Raccoons (Procyon lotor) are introduced here; say so in the species record's notes."),
    ),
    Place(
        "setagaya-jp", "A Tokyo suburb", "asia", "JP", "JP-13", "Tokyo",
        35.65, 139.65, "Asia/Tokyo", "Cfa", None, "Q231645", "Setagaya", "suburban-lot", 10935, 34917,
        "JPN.41_1",
        ("Passer montanus", "Hypsipetes amaurotis", "Spodiopsar cineraceus", "Streptopelia orientalis",
         "Corvus macrorhynchos", "Parus minor", "Zosterops japonicus", "Corvus corone",
         "Nyctereutes viverrinus", "Bufo japonicus", "Plestiodon finitimus", "Gekko japonicus"),
        ("Wikidata has no elevation for Setagaya; take one from a public source and cite it.",),
    ),
    Place(
        "sydney-au", "A Sydney backyard", "oceania", "AU", "AU-NSW", "New South Wales",
        -33.87, 151.21, "Australia/Sydney", "Cfa", 6, "Q3130", "Sydney", "suburban-lot", 6825, 18684,
        "AUS.5_1",
        ("Threskiornis molucca", "Manorina melanocephala", "Cacatua galerita", "Gymnorhina tibicen",
         "Trichoglossus moluccanus", "Vanellus miles", "Trichosurus vulpecula", "Pteropus poliocephalus",
         "Intellagama lesueurii", "Tiliqua scincoides", "Litoria peronii"),
    ),
    Place(
        "capetown-za", "A Cape Town garden", "africa", "ZA", "ZA-WC", "Western Cape",
        -33.93, 18.42, "Africa/Johannesburg", "Csb", 5, "Q5465", "Cape_Town", "suburban-lot", 6987, 52355,
        "ZAF.9_1",
        ("Bostrychia hagedash", "Cinnyris chalybeus", "Onychognathus morio", "Pycnonotus capensis",
         "Numida meleagris", "Alopochen aegyptiaca", "Spilopelia senegalensis", "Zosterops virens",
         "Sciurus carolinensis", "Procavia capensis", "Sclerophrys pantherina", "Bradypodion pumilum"),
        ("Wikidata's elevation is the city centre at sea level; the suburbs climb Table Mountain's slopes.",),
    ),
    Place(
        "saopaulo-br", "A São Paulo courtyard", "south-america", "BR", "BR-SP", "São Paulo",
        -23.55, -46.63, "America/Sao_Paulo", "Cfa", 760, "Q174", "São_Paulo", "courtyard", 13334, 25311,
        "BRA.25_1",
        ("Turdus rufiventris", "Pitangus sulphuratus", "Furnarius rufus", "Brotogeris tirica",
         "Thraupis sayaca", "Columbina talpacoti", "Callithrix penicillata", "Callithrix jacchus",
         "Didelphis aurita", "Salvator merianae", "Hemidactylus mabouia", "Rhinella ornata"),
        ("São Paulo sits on the Cfa/Cwa boundary; Wikipedia gives Cfa.",),
    ),
    Place(
        "bangalore-in", "A Bangalore terrace", "asia", "IN", "IN-KA", "Karnataka",
        12.98, 77.59, "Asia/Kolkata", "Aw", 920, "Q1355", "Bengaluru", "rowhouse-garden", 7043, 32239,
        "IND.16_1",
        ("Milvus migrans", "Pycnonotus jocosus", "Leptocoma zeylonica", "Spilopelia chinensis",
         "Psittacula krameri", "Acridotheres tristis", "Copsychus saularis", "Corvus splendens",
         "Funambulus palmarum", "Pteropus medius", "Duttaphrynus melanostictus", "Hemidactylus frenatus"),
        ("There is no terrace template; `rowhouse-garden` is the closest generic plot.",),
    ),
    Place(
        "toronto-ca", "A Toronto lot", "north-america", "CA", "CA-ON", "Ontario",
        43.67, -79.39, "America/Toronto", "Dfa", 76, "Q172", "Toronto", "suburban-lot", 6883, 27608,
        "CAN.9_1",
        ("Cardinalis cardinalis", "Turdus migratorius", "Passer domesticus", "Dryobates pubescens",
         "Spinus tristis", "Poecile atricapillus", "Zenaida macroura", "Sciurus carolinensis",
         "Procyon lotor", "Tamias striatus", "Sylvilagus floridanus", "Anaxyrus americanus"),
    ),
    Place(
        "mexicocity-mx", "A Mexico City rooftop garden", "north-america", "MX", "MX-CMX", "Mexico City",
        19.35, -99.14, "America/Mexico_City", "Cwb", 2240, "Q1489", "Mexico_City", "courtyard", 59014,
        101739, "MEX.9_1",
        ("Passer domesticus", "Columbina inca", "Haemorhous mexicanus", "Quiscalus mexicanus",
         "Pyrocephalus rubinus", "Saucerottia beryllina", "Turdus rufopalliatus", "Melozone fusca",
         "Sciurus aureogaster", "Didelphis virginiana", "Bassariscus astutus", "Sceloporus grammicus"),
        ("There is no rooftop template; `courtyard` is the closest generic plot.",
         "Wikidata's coordinate lies south of the historic centre; any public city-level centroid is fine.",
         "The city iNaturalist place above is Coyoacán; use the subdivision place for activity curves."),
    ),
    Place(
        "nairobi-ke", "A Nairobi compound", "africa", "KE", "KE-30", "Nairobi City County",
        -1.29, 36.82, "Africa/Nairobi", "Cwb", 1661, "Q3870", "Nairobi", "suburban-lot", 10957, None,
        "KEN.30_1",
        ("Bostrychia hagedash", "Milvus migrans", "Turdus abyssinicus", "Ploceus baglafecht",
         "Cinnyris venustus", "Pycnonotus barbatus", "Motacilla aguimp", "Corvus albus",
         "Cercopithecus mitis", "Chlorocebus pygerythrus", "Sclerophrys gutturalis", "Trioceros jacksonii"),
        ("Many Nairobi observations come from Nairobi National Park; pick garden animals, not the park's big game.",),
    ),
    Place(
        "dublin-ie", "A Dublin garden", "europe", "IE", "IE-D", "County Dublin",
        53.35, -6.26, "Europe/Dublin", "Cfb", 20, "Q1761", "Dublin", "rowhouse-garden", 6719, None,
        "IRL.6_1",
        ("Turdus merula", "Erithacus rubecula", "Passer domesticus", "Cyanistes caeruleus", "Pica pica",
         "Corvus cornix", "Coloeus monedula", "Parus major", "Vulpes vulpes", "Sciurus carolinensis",
         "Erinaceus europaeus", "Rana temporaria"),
        ("Most of these species already exist, so this is a good first locale.",
         "Wikidata files Dublin under Leinster (IE-L); the county code IE-D matches the GADM gid above."),
    ),
    Place(
        "auckland-nz", "An Auckland garden", "oceania", "NZ", "NZ-AUK", "Auckland",
        -36.85, 174.77, "Pacific/Auckland", "Cfb", 196, "Q37100", "Auckland", "suburban-lot", 8345, None,
        "NZL.1_1",
        ("Prosthemadera novaeseelandiae", "Hemiphaga novaeseelandiae", "Rhipidura fuliginosa",
         "Todiramphus sanctus", "Zosterops lateralis", "Turdus merula", "Acridotheres tristis",
         "Passer domesticus", "Erinaceus europaeus", "Trichosurus vulpecula", "Lampropholis delicata",
         "Ranoidea aurea"),
        ("Wikidata's elevation (196 m) looks high for the city centre; confirm it against another public source.",
         "Hedgehogs, possums, mynas and the garden skink are introduced in New Zealand."),
    ),
    Place(
        "seoul-kr", "A Seoul apartment green", "asia", "KR", "KR-11", "Seoul",
        37.56, 126.99, "Asia/Seoul", "Dwa", 38, "Q8684", "Seoul", "courtyard", 11005, 35673, "KOR.16_1",
        ("Pica serica", "Hypsipetes amaurotis", "Streptopelia orientalis", "Passer montanus", "Parus minor",
         "Cyanopica cyanus", "Corvus macrorhynchos", "Sciurus vulgaris", "Nyctereutes procyonoides",
         "Tamias sibiricus", "Dryophytes japonicus", "Pelophylax nigromaculatus"),
        ("There is no apartment-green template; `courtyard` is the closest generic plot.",),
    ),
    Place(
        "buenosaires-ar", "A Buenos Aires patio", "south-america", "AR", "AR-C", "Buenos Aires City",
        -34.60, -58.38, "America/Argentina/Buenos_Aires", "Cfa", 25, "Q1486", "Buenos_Aires", "courtyard",
        10434, 14264, "ARG.5_1",
        ("Furnarius rufus", "Pitangus sulphuratus", "Turdus rufiventris", "Mimus saturninus",
         "Patagioenas picazuro", "Zenaida auriculata", "Passer domesticus", "Myiopsitta monachus",
         "Zonotrichia capensis", "Didelphis albiventris", "Salvator merianae", "Rhinella arenarum"),
    ),
    Place(
        "vancouver-ca", "A Vancouver lot", "north-america", "CA", "CA-BC", "British Columbia",
        49.26, -123.11, "America/Vancouver", "Cfb", 2, "Q24639", "Vancouver", "suburban-lot", 7085, 27530,
        "CAN.2_1",
        ("Corvus brachyrhynchos", "Melospiza melodia", "Turdus migratorius", "Pipilo maculatus",
         "Colaptes auratus", "Calypte anna", "Poecile atricapillus", "Sciurus carolinensis",
         "Procyon lotor", "Tamiasciurus douglasii", "Pseudacris regilla", "Thamnophis sirtalis"),
        ("Vancouver sits on the Cfb/Csb boundary; Wikipedia gives Cfb.",),
    ),
    Place(
        "madrid-es", "A Madrid courtyard", "europe", "ES", "ES-MD", "Community of Madrid",
        40.42, -3.70, "Europe/Madrid", "Csa", 663, "Q2807", "Madrid", "courtyard", 10543, 30028, "ESP.8_1",
        ("Passer domesticus", "Pica pica", "Turdus merula", "Columba palumbus", "Myiopsitta monachus",
         "Sturnus unicolor", "Apus apus", "Serinus serinus", "Parus major", "Erinaceus europaeus",
         "Tarentola mauritanica", "Pelophylax perezi"),
        ("Madrid sits on the Csa/BSk boundary; Wikipedia gives Csa.",),
    ),
    Place(
        "chiangmai-th", "A Chiang Mai garden", "asia", "TH", "TH-50", "Chiang Mai",
        18.79, 98.98, "Asia/Bangkok", "Aw", 310, "Q52028", "Chiang_Mai", "suburban-lot", 13320, 45315,
        "THA.10_1",
        ("Pycnonotus jocosus", "Pycnonotus aurigaster", "Spilopelia chinensis", "Acridotheres tristis",
         "Copsychus saularis", "Passer montanus", "Orthotomus sutorius", "Callosciurus finlaysonii",
         "Tamiops mcclellandii", "Duttaphrynus melanostictus", "Hemidactylus platyurus", "Calotes versicolor"),
    ),
    Place(
        "accra-gh", "An Accra compound", "africa", "GH", "GH-AA", "Greater Accra",
        5.56, -0.20, "Africa/Accra", "Aw", 61, "Q3761", "Accra", "suburban-lot", 10621, 30642, "GHA7_2",
        ("Crinifer piscator", "Corvinella corvina", "Spilopelia senegalensis", "Corvus albus",
         "Lophoceros nasutus", "Centropus senegalensis", "Bubulcus ibis", "Ploceus cucullatus",
         "Eidolon helvum", "Agama picticauda", "Sclerophrys regularis"),
        ("Observations are sparse here (tens per species on iNaturalist); `fetch_activity.py` may fall back "
         "to the country (GH) or mark curves low-confidence. Say so in the PR.",
         "Accra's climate is on the Aw/BSh boundary; confirm the class."),
    ),
    Place(
        "reykjavik-is", "A Reykjavík garden", "europe", "IS", "IS-1", "Capital Region",
        64.15, -21.94, "Atlantic/Reykjavik", "Cfc", 8, "Q1764", "Reykjavík", "suburban-lot", 10868, 33029,
        "ISL.3_1",
        ("Turdus iliacus", "Sturnus vulgaris", "Anas platyrhynchos", "Anser anser", "Chroicocephalus ridibundus",
         "Corvus corax", "Troglodytes troglodytes", "Acanthis flammea", "Plectrophenax nivalis",
         "Oryctolagus cuniculus", "Mus musculus", "Vulpes lagopus"),
        ("Iceland has no native amphibians or reptiles, so this list is birds and mammals.",
         "Arctic foxes are rare inside the city; list one only if a source supports it.",
         "Reykjavík sits on the Cfc/Dfc boundary; Wikipedia gives Cfc."),
    ),
    Place(
        "santiago-cl", "A Santiago garden", "south-america", "CL", "CL-RM", "Santiago Metropolitan Region",
        -33.44, -70.65, "America/Santiago", "Csb", 575, "Q2887", "Santiago", "suburban-lot", 12691, 27738,
        "CHL.14_1",
        ("Turdus falcklandii", "Zenaida auriculata", "Myiopsitta monachus", "Mimus thenca",
         "Zonotrichia capensis", "Milvago chimango", "Curaeus curaeus", "Passer domesticus",
         "Vanellus chilensis", "Tadarida brasiliensis", "Liolaemus tenuis", "Pleurodema thaul"),
    ),
    Place(
        "paris-fr", "A Paris courtyard", "europe", "FR", "FR-IDF", "Île-de-France",
        48.86, 2.35, "Europe/Paris", "Cfb", 48, "Q90", "Paris", "courtyard", 10577, 99545, "FRA.8_1",
        ("Columba palumbus", "Corvus corone", "Turdus merula", "Passer domesticus", "Cyanistes caeruleus",
         "Erithacus rubecula", "Psittacula krameri", "Parus major", "Erinaceus europaeus", "Podarcis muralis",
         "Pipistrellus pipistrellus", "Bufo bufo"),
    ),
    # United States, state by state: one request per queued place, in queue order (waves 5 to 8).
    # Each state's rotation covers rural, coastal (where there is a coast), suburban and urban settings.
    # `inat_city_place` is the county (or independent city) whose research-grade counts chose the species.
    Place(
        "nd-bismarck", "A Bismarck street", "north-america", "US", "US-ND", "North Dakota",
        46.81, -100.78, "America/Chicago", "Dfa", 514, "Q37066", "Bismarck,_North_Dakota", "street-block", 13,
        2962, "USA.35_1",
        ("Turdus migratorius", "Passer domesticus", "Zenaida macroura", "Bombycilla cedrorum", "Colaptes auratus",
         "Spinus tristis", "Poecile atricapillus", "Buteo jamaicensis", "Sciurus niger",
         "Ictidomys tridecemlineatus", "Lasionycteris noctivagans", "Lithobates pipiens"),
        ("Bismarck sits on the Dfa/Dfb boundary; Wikipedia gives Dfa/Dfb.",
         "Bat records are sparse here (2 research-grade silver-haired bat observations in the county); "
         "if `fetch_activity.py` widens to the country (US), say so in the PR."),
        species_place_name="Burleigh County",
    ),
    Place(
        "ga-atlanta", "A Midtown Atlanta street", "north-america", "US", "US-GA", "Georgia",
        33.79, -84.38, "America/New_York", "Cfa", None, "Q6843071", "Atlanta", "street-block", 23, 690,
        "USA.11_1",
        ("Cardinalis cardinalis", "Turdus migratorius", "Mimus polyglottos", "Thryothorus ludovicianus",
         "Baeolophus bicolor", "Columba livia", "Buteo lineatus", "Sciurus carolinensis", "Didelphis virginiana",
         "Tamias striatus", "Lasiurus borealis", "Anolis carolinensis"),
        ("The centroid is the Midtown neighbourhood item; the Köppen class comes from the Atlanta article.",),
        species_place_name="Fulton County",
    ),
    Place(
        "nm-mesilla", "A Las Cruces lot", "north-america", "US", "US-NM", "New Mexico",
        32.31, -106.78, "America/Denver", "BWk", 1191, "Q33264", "Las_Cruces,_New_Mexico", "suburban-lot", 9,
        2389, "USA.32_1",
        ("Zenaida asiatica", "Geococcyx californianus", "Callipepla gambelii", "Haemorhous mexicanus",
         "Toxostoma curvirostre", "Quiscalus mexicanus", "Melozone fusca", "Archilochus alexandri",
         "Sylvilagus audubonii", "Otospermophilus variegatus", "Antrozous pallidus", "Urosaurus ornatus"),
        ("Chihuahuan Desert: the garden is xeric (mesquite, creosote, yucca), irrigated only near the house.",
         "Oryx on iNaturalist here are introduced on the missile range, not garden animals; leave them out."),
        species_place_name="Doña Ana County",
    ),
    Place(
        "or-highdesert", "A Burns ranch lot", "north-america", "US", "US-OR", "Oregon",
        43.59, -119.05, "America/Los_Angeles", "BSk", 1264, "Q6178257", "Burns,_Oregon", "rural-lot", 10, 1849,
        "USA.38_1",
        ("Antigone canadensis", "Buteo jamaicensis", "Bubo virginianus", "Pica hudsonia", "Sialia currucoides",
         "Sturnella neglecta", "Tyrannus verticalis", "Odocoileus hemionus", "Urocitellus beldingi",
         "Lepus californicus", "Eptesicus fuscus", "Pituophis catenifer"),
        ("Sagebrush steppe at the edge of the Harney Basin wetlands; many county records come from Malheur "
         "National Wildlife Refuge, so prefer animals a ranch yard sees.",
         "Bat records are sparse here (2 research-grade big brown bat observations in the county)."),
        species_place_name="Harney County",
    ),
    Place(
        "ma-berkshires", "A Great Barrington woodland lot", "north-america", "US", "US-MA", "Massachusetts",
        42.20, -73.36, "America/New_York", "Dfb", 221, "Q1144518", "Great_Barrington,_Massachusetts",
        "rural-lot", 2, 821, "USA.22_1",
        ("Meleagris gallopavo", "Sayornis phoebe", "Poecile atricapillus", "Cyanocitta cristata", "Sialia sialis",
         "Strix varia", "Tamias striatus", "Erethizon dorsatum", "Vulpes vulpes", "Eptesicus fuscus",
         "Notophthalmus viridescens", "Anaxyrus americanus"),
        ("Black bears are common in the county but too large for most plots; list one only with a note.",),
        koppen_source="from the Beck et al. 2018 Köppen-Geiger map (CC BY 4.0, https://www.gloh2o.org/koppen/) "
        "for Great Barrington; the [Wikipedia](https://en.wikipedia.org/wiki/Great_Barrington,_Massachusetts) "
        "article gives no class",
        species_place_name="Berkshire County",
    ),
    Place(
        "in-brown", "A Brown County woods lot", "north-america", "US", "US-IN", "Indiana",
        39.21, -86.25, "America/Indiana/Indianapolis", "Cfa", 181, "Q1924785", "Nashville,_Indiana", "rural-lot",
        20, 282, "USA.15_1",
        ("Meleagris gallopavo", "Cardinalis cardinalis", "Baeolophus bicolor", "Melanerpes carolinus",
         "Sialia sialis", "Dryocopus pileatus", "Odocoileus virginianus", "Tamias striatus", "Glaucomys volans",
         "Lasiurus borealis", "Terrapene carolina", "Anaxyrus americanus"),
        ("Nashville sits on the Cfa/Dfa boundary; Wikipedia gives Cfa.",
         "Observations are thinner here (about 34,000 research-grade in the county), so check that the "
         "bat's county records support listing it."),
        species_place_name="Brown County",
    ),
    Place(
        "mo-stlouis", "A Tower Grove garden", "north-america", "US", "US-MO", "Missouri",
        38.60, -90.26, "America/Chicago", "Cfa", None, "Q14704506", "St._Louis", "rowhouse-garden", 28, 107095,
        "USA.26_1",
        ("Turdus migratorius", "Cardinalis cardinalis", "Zonotrichia albicollis", "Quiscalus quiscula",
         "Passer domesticus", "Buteo jamaicensis", "Sciurus carolinensis", "Sylvilagus floridanus",
         "Didelphis virginiana", "Mus musculus", "Lasiurus borealis", "Terrapene triunguis"),
        ("The centroid is the Tower Grove South neighbourhood item; the Köppen class comes from the St. Louis "
         "article, which sits on the Cfa/Dfa boundary.",
         "St. Louis is an independent city, so its iNaturalist place stands in for a county."),
        species_place_name="the City of St. Louis",
    ),
    Place(
        "al-birmingham", "A Birmingham street", "north-america", "US", "US-AL", "Alabama",
        33.52, -86.81, "America/Chicago", "Cfa", 187, "Q79867", "Birmingham,_Alabama", "street-block", 19, 343,
        "USA.1_1",
        ("Cardinalis cardinalis", "Melanerpes carolinus", "Thryothorus ludovicianus", "Baeolophus bicolor",
         "Poecile carolinensis", "Mimus polyglottos", "Buteo lineatus", "Sciurus carolinensis", "Procyon lotor",
         "Tamias striatus", "Perimyotis subflavus", "Anolis carolinensis"),
        koppen_source="[Wikipedia](https://en.wikipedia.org/wiki/Birmingham,_Alabama) (CC BY-SA) describes a "
        "humid subtropical climate without giving the code",
        species_place_name="Jefferson County",
    ),
    Place(
        "ok-tulsa", "A Tulsa street", "north-america", "US", "US-OK", "Oklahoma",
        36.13, -95.94, "America/Chicago", "Cfa", 223, "Q44989", "Tulsa,_Oklahoma", "street-block", 12, 2981,
        "USA.37_1",
        ("Mimus polyglottos", "Cardinalis cardinalis", "Quiscalus mexicanus", "Passer domesticus",
         "Cyanocitta cristata", "Tyrannus forficatus", "Ictinia mississippiensis", "Sciurus niger",
         "Didelphis virginiana", "Mus musculus", "Eptesicus fuscus", "Hemidactylus turcicus"),
        ("The Mediterranean house gecko is introduced here.",),
        species_place_name="Tulsa County",
    ),
    Place(
        "mi-annarbor", "An Ann Arbor lot", "north-america", "US", "US-MI", "Michigan",
        42.28, -83.75, "America/Detroit", "Dfa", 256, "Q485172", "Ann_Arbor,_Michigan", "suburban-lot", 29, 2649,
        "USA.23_1",
        ("Turdus migratorius", "Cardinalis cardinalis", "Cyanocitta cristata", "Poecile atricapillus",
         "Melanerpes carolinus", "Meleagris gallopavo", "Sciurus niger", "Tamias striatus", "Procyon lotor",
         "Eptesicus fuscus", "Thamnophis sirtalis", "Anaxyrus americanus"),
        species_place_name="Washtenaw County",
    ),
    Place(
        "pa-pittsburgh", "A Pittsburgh rowhouse garden", "north-america", "US", "US-PA", "Pennsylvania",
        40.46, -79.95, "America/New_York", "Dfa", None, "Q4928223", "Pittsburgh", "rowhouse-garden", 42, 913,
        "USA.39_1",
        ("Turdus migratorius", "Cardinalis cardinalis", "Melospiza melodia", "Passer domesticus", "Columba livia",
         "Buteo jamaicensis", "Sciurus carolinensis", "Marmota monax", "Tamias striatus", "Procyon lotor",
         "Eptesicus fuscus", "Anaxyrus americanus"),
        ("The centroid is the Bloomfield neighbourhood item; the Köppen class comes from the Pittsburgh "
         "article, which gives Dfa or Cfa depending on the isotherm used.",),
        species_place_name="Allegheny County",
    ),
    Place(
        "de-kent", "A Kent County farm lot", "north-america", "US", "US-DE", "Delaware",
        39.10, -75.50, "America/New_York", "Cfa", None, "Q128137", "Kent_County,_Delaware", "rural-lot", 4, 1741,
        "USA.8_1",
        ("Haliaeetus leucocephalus", "Ardea herodias", "Agelaius phoeniceus", "Passerina caerulea",
         "Cardinalis cardinalis", "Tyrannus tyrannus", "Vulpes vulpes", "Sylvilagus floridanus",
         "Peromyscus leucopus", "Lasiurus borealis", "Anaxyrus fowleri", "Chrysemys picta"),
        ("The centroid is the county's; the lot is farmland with a woodlot edge, not the Delaware Bay marshes, "
         "which supply many of the county's records.",),
        species_place_name="Kent County",
    ),
    Place(
        "wv-highlands", "A Canaan Valley lot", "north-america", "US", "US-WV", "West Virginia",
        39.13, -79.38, "America/New_York", "Dfb", None, "Q5029191", "Davis,_West_Virginia", "rural-lot", 33, 752,
        "USA.49_1",
        ("Junco hyemalis", "Poecile atricapillus", "Turdus migratorius", "Bombycilla cedrorum",
         "Geothlypis trichas", "Meleagris gallopavo", "Odocoileus virginianus", "Tamiasciurus hudsonicus",
         "Lepus americanus", "Eptesicus fuscus", "Desmognathus ochrophaeus", "Notophthalmus viridescens"),
        ("A high valley (about 1,000 m) of wet meadow and spruce; the Köppen class comes from the Davis article.",
         "Bat records are sparse here (2 research-grade big brown bat observations in the county)."),
        species_place_name="Tucker County",
    ),
    Place(
        "ms-jackson", "A Jackson, Mississippi street", "north-america", "US", "US-MS", "Mississippi",
        32.30, -90.18, "America/Chicago", "Cfa", 85, "Q28198", "Jackson,_Mississippi", "street-block", 37, 427,
        "USA.25_1",
        ("Cardinalis cardinalis", "Mimus polyglottos", "Thryothorus ludovicianus", "Toxostoma rufum",
         "Buteo lineatus", "Zenaida macroura", "Sciurus carolinensis", "Didelphis virginiana",
         "Dasypus mexicanus", "Myotis austroriparius", "Anolis carolinensis", "Hemidactylus turcicus"),
        ("Observations are sparse here (about 14,000 research-grade in the county); the activity curves "
         "use the state (US-MS), and if `fetch_activity.py` widens to the country, say so in the PR.",
         "The Mediterranean house gecko is introduced here."),
        species_place_name="Hinds County",
    ),
    Place(
        "nc-mountains", "A Boone mountain lot", "north-america", "US", "US-NC", "North Carolina",
        36.22, -81.67, "America/New_York", "Dfb", 1015.9, "Q893055", "Boone,_North_Carolina", "rural-lot", 30,
        216, "USA.34_1",
        ("Junco hyemalis", "Melospiza melodia", "Meleagris gallopavo", "Cyanocitta cristata",
         "Pipilo erythrophthalmus", "Archilochus colubris", "Odocoileus virginianus", "Tamias striatus",
         "Glaucomys volans", "Eptesicus fuscus", "Desmognathus orestes", "Thamnophis sirtalis"),
        ("The southern Appalachians are a salamander hotspot; a dusky salamander is the plot's amphibian.",),
        species_place_name="Watauga County",
    ),
    Place(
        "vt-burlington", "A Burlington street", "north-america", "US", "US-VT", "Vermont",
        44.48, -73.21, "America/New_York", "Dfa", 61, "Q31058", "Burlington,_Vermont", "street-block", 47, 1370,
        "USA.46_1",
        ("Turdus migratorius", "Poecile atricapillus", "Cardinalis cardinalis", "Melospiza melodia",
         "Larus delawarensis", "Corvus brachyrhynchos", "Passer domesticus", "Sciurus carolinensis",
         "Procyon lotor", "Tamias striatus", "Eptesicus fuscus", "Thamnophis sirtalis"),
        ("Burlington sits on the Dfa/Dfb boundary; Wikipedia gives Dfa.",),
        species_place_name="Chittenden County",
    ),
    Place(
        "tn-cumberland", "A Sewanee woods lot", "north-america", "US", "US-TN", "Tennessee",
        35.20, -85.92, "America/Chicago", "Cfa", 588, "Q1987614", "Sewanee,_Tennessee", "rural-lot", 45, 1063,
        "USA.43_1",
        ("Sialia sialis", "Dryocopus pileatus", "Strix varia", "Cyanocitta cristata", "Piranga rubra",
         "Meleagris gallopavo", "Odocoileus virginianus", "Dasypus mexicanus", "Tamias striatus",
         "Perimyotis subflavus", "Terrapene carolina", "Plethodon glutinosus"),
        ("Oak-hickory forest on the Cumberland Plateau top.",
         "Observations are sparse here (about 18,000 research-grade in the county); the activity curves "
         "use the state (US-TN), and if `fetch_activity.py` widens to the country, say so in the PR."),
        species_place_name="Franklin County",
    ),
    Place(
        "oh-sandusky", "A Sandusky shore lot", "north-america", "US", "US-OH", "Ohio",
        41.45, -82.71, "America/New_York", "Dfa", 182, "Q608207", "Sandusky,_Ohio", "suburban-lot", 31, 2775,
        "USA.36_1",
        ("Haliaeetus leucocephalus", "Ardea herodias", "Larus delawarensis", "Agelaius phoeniceus",
         "Tachycineta bicolor", "Melanerpes erythrocephalus", "Blarina brevicauda", "Sciurus niger",
         "Procyon lotor", "Lasiurus borealis", "Nerodia sipedon", "Chrysemys picta"),
        ("A coastal lot on Sandusky Bay, Lake Erie: `suburban-lot` with the shore along one edge.",
         "The Lake Erie islands' water snakes are a protected subspecies of the common watersnake.",
         "iNaturalist's \"Sandusky\" search finds Sandusky County first; Sandusky city is in Erie County."),
        species_place_name="Erie County",
    ),
    Place(
        "nj-jerseycity", "A Jersey City rowhouse garden", "north-america", "US", "US-NJ", "New Jersey",
        40.75, -74.05, "America/New_York", "Cfa", None, "Q7739304", "Jersey_City,_New_Jersey", "rowhouse-garden",
        51, 3020, "USA.31_1",
        ("Columba livia", "Passer domesticus", "Sturnus vulgaris", "Mimus polyglottos", "Turdus migratorius",
         "Zenaida macroura", "Cardinalis cardinalis", "Sciurus carolinensis", "Mephitis mephitis",
         "Rattus norvegicus", "Lasiurus borealis", "Podarcis siculus"),
        ("The centroid is The Heights neighbourhood item; the Köppen class comes from the Jersey City article.",
         "Rock pigeons, house sparrows, starlings, brown rats and the Italian wall lizard are introduced here."),
        species_place_name="Hudson County",
    ),
    Place(
        "ar-fortsmith", "A Fort Smith street", "north-america", "US", "US-AR", "Arkansas",
        35.35, -94.37, "America/Chicago", "Cfa", 141, "Q79535", "Fort_Smith,_Arkansas", "street-block", 36, 2016,
        "USA.4_1",
        ("Turdus migratorius", "Cardinalis cardinalis", "Mimus polyglottos", "Cyanocitta cristata",
         "Thryothorus ludovicianus", "Tyrannus forficatus", "Passer domesticus", "Sciurus niger",
         "Didelphis virginiana", "Mephitis mephitis", "Eptesicus fuscus", "Terrapene triunguis"),
        ("Bat records are sparse here (single research-grade observations of four species in the county).",),
        koppen_source="[Wikipedia](https://en.wikipedia.org/wiki/Fort_Smith,_Arkansas) (CC BY-SA) describes a "
        "humid subtropical climate without giving the code",
        species_place_name="Sebastian County",
    ),
    Place(
        "co-coloradosprings", "A Colorado Springs street", "north-america", "US", "US-CO", "Colorado",
        38.86, -104.79, "America/Denver", "BSk", 1839, "Q49258", "Colorado_Springs,_Colorado", "street-block",
        34, 2894, "USA.6_1",
        ("Pica hudsonia", "Aphelocoma woodhouseii", "Haemorhous mexicanus", "Turdus migratorius",
         "Colaptes auratus", "Junco hyemalis", "Sciurus niger", "Procyon lotor", "Sylvilagus audubonii",
         "Eptesicus fuscus", "Sceloporus consobrinus", "Thamnophis elegans"),
        ("Use `BSk`: the maintainers' import has no template yet for the dry-winter classes (`Dwa`, `Cwa`) "
         "Wikipedia gives.",
         "Eastern fox squirrels are introduced in Colorado."),
        koppen_source="from the Beck et al. 2018 Köppen-Geiger map (CC BY 4.0, https://www.gloh2o.org/koppen/) "
        "for Colorado Springs; [Wikipedia](https://en.wikipedia.org/wiki/Colorado_Springs,_Colorado) gives "
        "Dwa/Cwa",
        species_place_name="El Paso County",
    ),
    Place(
        "wy-jackson", "A Jackson Hole lot", "north-america", "US", "US-WY", "Wyoming",
        43.48, -110.77, "America/Denver", "Dfb", 1901, "Q871285", "Jackson,_Wyoming", "suburban-lot", 15, 1784,
        "USA.51_1",
        ("Corvus corax", "Pica hudsonia", "Sialia currucoides", "Turdus migratorius", "Poecile gambeli",
         "Junco hyemalis", "Odocoileus hemionus", "Urocitellus armatus", "Tamiasciurus hudsonicus",
         "Myotis lucifugus", "Thamnophis elegans", "Pseudacris maculata"),
        ("Most county records are the national parks' big game (bison, elk, moose, bears); pick what a lot in "
         "the town sees.",
         "Bat records are sparse here (a few research-grade myotis observations in the county)."),
        species_place_name="Teton County",
    ),
    Place(
        "la-shreveport", "A Shreveport lot", "north-america", "US", "US-LA", "Louisiana",
        32.51, -93.76, "America/Chicago", "Cfa", 46, "Q80517", "Shreveport,_Louisiana", "suburban-lot", 27, 1450,
        "USA.19_1",
        ("Mimus polyglottos", "Cardinalis cardinalis", "Sialia sialis", "Ictinia mississippiensis",
         "Thryothorus ludovicianus", "Melanerpes carolinus", "Sciurus carolinensis", "Didelphis virginiana",
         "Dasypus mexicanus", "Eptesicus fuscus", "Anolis carolinensis", "Dryophytes cinereus"),
        ("Bat records are very sparse here (one research-grade observation in the parish); if "
         "`fetch_activity.py` widens to the country (US), say so in the PR.",),
        species_place_name="Caddo Parish",
    ),
    Place(
        "nm-albuquerque", "An Albuquerque courtyard", "north-america", "US", "US-NM", "New Mexico",
        35.08, -106.60, "America/Denver", "BSk", None, "Q7045560", "Albuquerque,_New_Mexico", "courtyard", 9,
        2390, "USA.32_1",
        ("Geococcyx californianus", "Haemorhous mexicanus", "Columba livia", "Zenaida asiatica",
         "Toxostoma curvirostre", "Spinus psaltria", "Archilochus alexandri", "Astur cooperii",
         "Sylvilagus audubonii", "Otospermophilus variegatus", "Tadarida brasiliensis", "Sceloporus cowlesi"),
        ("The centroid is the Nob Hill neighbourhood item; the Köppen class comes from the Albuquerque article, "
         "which gives BSk or BWk depending on the period.",),
        species_place_name="Bernalillo County",
    ),
]


def slug_of(scientific_name: str) -> str:
    return scientific_name.lower().replace(" ", "-")


# Which species existed under `species/` when the issues were written. The
# bodies use this snapshot, not the live directory, so a later species PR
# does not make the committed bodies stale. Refresh both together.
SPECIES_SNAPSHOT_DATE = "2026-09-26"
SPECIES_SNAPSHOT = frozenset({
    "apodemus-sylvaticus", "bufo-bufo", "carduelis-carduelis", "columba-livia", "columba-palumbus",
    "cyanistes-caeruleus", "erinaceus-europaeus", "erithacus-rubecula", "parus-major", "passer-domesticus",
    "pica-pica", "psittacula-krameri", "sciurus-carolinensis", "troglodytes-troglodytes", "turdus-merula",
    "vulpes-vulpes",
})


def fmt_coord(value: float) -> str:
    return f"{value:.2f}"


def render_body(place: Place) -> str:
    """The issue body for one place. Pure: depends only on `place`, TAXA and
    SPECIES_SNAPSHOT."""
    existing = [n for n in place.species if slug_of(n) in SPECIES_SNAPSHOT]
    wikidata_url = f"https://www.wikidata.org/wiki/{place.wikidata}"
    wikipedia_url = f"https://en.wikipedia.org/wiki/{place.wikipedia}"
    inat_region = f"https://www.inaturalist.org/places/{place.inat_region_place}"
    gbif_gadm = f"https://www.gbif.org/occurrence/search?gadm_gid={place.gadm_gid}"
    if place.elevation_m is None:
        elevation = f"to confirm (Wikidata [{place.wikidata}]({wikidata_url}) has no elevation)"
    else:
        elevation = f"{place.elevation_m:g} m, from Wikidata [{place.wikidata}]({wikidata_url}) `P2044` (CC0)"

    lines = [
        f"**{place.name}**: a locale for the [live ecological simulation]({LIVE_URL})'s rotation. "
        f"Whoever takes this (often a coding agent) writes `locales/{place.id}/locale.json` and any "
        f"missing species, following \"Contribute a locale\" in [AGENTS.md]({REPO_URL}/blob/main/AGENTS.md). "
        f"The worked example is [`locales/london-uk/`]({REPO_URL}/tree/main/locales/london-uk).",
        "",
        "### Suggested manifest values",
        "",
        "| Field | Suggestion |",
        "|---|---|",
        f"| `id` | `{place.id}` |",
        f"| `name` | {place.name} |",
        f"| `country` | `{place.country}` |",
        f"| `activity_region` | `{place.region}` ({place.region_name}) |",
        f"| `public_lat`, `public_lon` | {fmt_coord(place.lat)}, {fmt_coord(place.lon)}: the public city "
        f"centroid from Wikidata [{place.wikidata}]({wikidata_url}) `P625` (CC0), rounded to 2 decimals |",
        f"| `tz` | `{place.tz}` |",
        f"| `koppen` | `{place.koppen}`, "
        + (place.koppen_source or f"from the climate section of [Wikipedia]({wikipedia_url}) (CC BY-SA)")
        + "; confirm |",
        f"| `elevation_m` | {elevation} |",
        f"| `plot_template` | `{place.plot_template}` |",
        "",
        "Use the city or district centroid only: never a street address, a house, or your own garden.",
        "",
        "### Data pointers",
        "",
        f"- iNaturalist place for the activity region: [{place.inat_region_place}]({inat_region})",
    ]
    if place.inat_city_place is not None:
        where = f"{place.species_place_name}, for species lists" if place.species_place_name else "the city (species lists)"
        lines.append(
            f"- iNaturalist place for {where}: "
            f"[{place.inat_city_place}](https://www.inaturalist.org/places/{place.inat_city_place})"
        )
    lines += [
        f"- GBIF GADM gid for the activity region: [`{place.gadm_gid}`]({gbif_gadm})",
        f"- GBIF country page: https://www.gbif.org/country/{place.country}/summary",
    ]
    for label, url in ATLASES.get(place.country, []):
        lines.append(f"- {label}: {url} (check each dataset's licence)")
    lines += [
        f"- Climate normals: the maintainers' import derives weather from climate normals at the centroid, "
        f"so you do not supply them. For the Köppen class, see "
        + ("the source named in the table above" if place.koppen_source
           else f"the climate table on [Wikipedia]({wikipedia_url})")
        + " or the WMO 1991-2020 normals at https://www.ncei.noaa.gov/products/wmo-climate-normals",
        "",
        "Activity curves for this region, per species:",
        "",
        "```",
        f"uv run tools/fetch_activity.py <slug> --region {place.region} "
        f"--inat-place-id {place.inat_region_place} --gbif-gadm-gid {place.gadm_gid} --write",
        "```",
        "",
        f"### Candidate species ({len(place.species)}; list at least 8; aim for 12 or more)",
        "",
        f"On {SPECIES_SNAPSHOT_DATE}, {len(existing)} of these existed under `species/`"
        + (f" ({', '.join(f'`{slug_of(n)}`' for n in existing)}); they still need a curve for "
           f"`{place.region}`." if existing else ".")
        + " Check `species/` for any added since.",
        "Add the rest by the species flow in AGENTS.md; a locale PR may carry the species it needs. "
        "Search open `species-request` issues first, and claim any you take.",
        "",
        f"| Species | Common name | In `species/` on {SPECIES_SNAPSHOT_DATE} | GBIF | iNaturalist | Note |",
        "|---|---|---|---|---|---|",
    ]
    for name in place.species:
        common, gbif_key, inat_id, note = TAXA[name]
        in_repo = f"yes (`{slug_of(name)}`)" if name in existing else "no"
        lines.append(
            f"| *{name}* | {common} | {in_repo} | [{gbif_key}](https://www.gbif.org/species/{gbif_key}) | "
            f"[{inat_id}](https://www.inaturalist.org/taxa/{inat_id}) | {note or ''} |"
        )
    if place.notes:
        lines += ["", "### Notes", ""]
        lines += [f"- {note}" for note in place.notes]
    lines += [
        "",
        "### Plants",
        "",
        f"Ship `locales/{place.id}/flora-catalog.json`: at least 8 plant taxa, at least 2 of them "
        f"evergreen, each `taxon` chosen from [`schema/v0.1/flora-taxa.json`]({REPO_URL}/blob/main/"
        "schema/v0.1/flora-taxa.json) (the plants the simulation can draw), naming the local species it "
        f"stands in for. See \"Writing `flora-catalog.json`\" in [`docs/locale-richness.md`]({REPO_URL}/"
        f"blob/main/docs/locale-richness.md), and copy [`locales/london-uk/flora-catalog.json`]({REPO_URL}/"
        "blob/main/locales/london-uk/flora-catalog.json) as a starting point. Without a catalog the garden "
        "gets a generic set of a few large trees for its Köppen class. Note any local plant no drawable "
        "taxon resembles in the manifest's `flora_wishlist`, by name only.",
        "",
        "### Definition of done",
        "",
        "- [ ] Claimed here first: `Claiming this: <agent/person>, ETA <date>`",
        f"- [ ] `locales/{place.id}/locale.json` with a sourced centroid, climate, `blurb` and `facts` "
        "(allow-listed licences, attribution unless CC0 or public domain)",
        f"- [ ] At least 8 species, each under `species/` with a 12-month activity curve for `{place.region}`",
        f"- [ ] `locales/{place.id}/flora-catalog.json` with at least 8 plant taxa, at least 2 evergreen, "
        "each `taxon` from `schema/v0.1/flora-taxa.json`",
        f"- [ ] `uv run tools/validate.py --locale {place.id} --report > report.md` passes",
        "- [ ] `uv run tools/validate.py --self-check` passes; any warning (for example an activity curve "
        "`fetch_activity.py` recorded under CC BY-NC) is justified in the PR body",
        "- [ ] The `validate` CI workflow is green on the PR",
        f"- [ ] PR titled `locale: {place.name} ({place.id})`, with the report and `Closes #<this issue>`",
        "",
        "Once a maintainer merges it and the maintainers' import succeeds, the locale enters the live rotation "
        f"automatically, and the PR gets a comment saying when it first appears on the [stream]({LIVE_URL}). "
        f"See the locales page: {SITE_URL}locales.html",
        "",
    ]
    return "\n".join(lines)


def _load_validate():
    spec = importlib.util.spec_from_file_location("speeeecies_validate", REPO_ROOT / "tools" / "validate.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def lint_bodies(bodies: dict[str, str]) -> list[str]:
    """Run validate.py's public-safety text lint over each body."""
    validate = _load_validate()
    problems = []
    for rel, text in bodies.items():
        problems += [f.line() for f in validate.lint_text(text, rel)]
    return problems


def render_all() -> dict[str, str]:
    """`tools/issues/out/<id>.md` (repo-relative) -> issue Markdown, title first."""
    return {
        f"tools/issues/out/{p.id}.md": f"<!-- title: {p.title} -->\n{render_body(p)}" for p in PLACES
    }


Runner = Callable[[list[str]], str]


def gh(args: list[str]) -> str:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=True).stdout


def post(runner: Runner, dry_run: bool) -> list[str]:
    """Create each missing issue. Idempotent: any issue (open or closed)
    whose title already exists is skipped. Returns a log of actions."""
    log = []
    # GitHub label names are case-insensitive.
    labels = {row["name"].lower() for row in json.loads(runner(["label", "list", "--limit", "200", "--json", "name"]))}
    wanted = {LABEL: (LABEL_COLOR, LABEL_DESCRIPTION)}
    wanted.update({p.continent: CONTINENT_LABELS[p.continent] for p in PLACES})
    for name, (color, description) in wanted.items():
        if name not in labels:
            log.append(f"create label {name}")
            if not dry_run:
                runner(["label", "create", name, "--color", color, "--description", description])
    titles = {
        row["title"]
        for row in json.loads(runner(["issue", "list", "--state", "all", "--limit", "1000", "--json", "title"]))
    }
    for place in PLACES:
        if place.title in titles:
            log.append(f"skip (exists): {place.title}")
            continue
        log.append(f"create: {place.title}")
        if not dry_run:
            runner([
                "issue", "create", "--title", place.title, "--body", render_body(place),
                "--label", LABEL, "--label", place.continent,
            ])
    return log


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if tools/issues/out/ is stale; write nothing")
    parser.add_argument("--post", action="store_true", help="create missing issues on GitHub with gh")
    parser.add_argument("--dry-run", action="store_true", help="with --post: print what would be created")
    args = parser.parse_args(argv)

    rendered = render_all()
    problems = lint_bodies(rendered)
    if problems:
        print("public-safety lint failed; nothing written or posted:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return 1

    if args.check:
        stale = [rel for rel, text in rendered.items()
                 if not (REPO_ROOT / rel).is_file() or (REPO_ROOT / rel).read_text(encoding="utf-8") != text]
        extra = sorted({f"tools/issues/out/{p.name}" for p in OUT_DIR.glob("*.md")} - set(rendered))
        for rel in stale + extra:
            print(f"stale: {rel} (rerun uv run tools/issues/locale_requests.py)", file=sys.stderr)
        return 1 if stale or extra else 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for rel, text in rendered.items():
        (REPO_ROOT / rel).write_text(text, encoding="utf-8")
    print(f"wrote {len(rendered)} issue bodies to tools/issues/out/")

    if args.post:
        for line in post(gh, args.dry_run):
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
