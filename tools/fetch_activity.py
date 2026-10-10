# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build a 12-month observation-based activity curve for one species/region.

Queries iNaturalist (observations histogram) and GBIF (occurrence search facets),
normalises each source's monthly counts (for birds and mammals, against the same
source's counts for the species' class, an "effort" baseline that removes
observer-effort seasonality; for ectotherms, raw counts, because their class
totals collapse in winter), and combines the two into one curve. Licence tiers widen from the
most permissive (CC0 + CC BY) only when a source's total count is too thin.

See PLAN.md ("Monthly activity") for the full method. This module is
stdlib-only so it runs as a PEP 723 `uv run` script.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

USER_AGENT = "speeeecies-fetch-activity/0.1 (+https://github.com/eeeearth/speeeecies)"
INAT_MIN_INTERVAL_SECONDS = 1.0
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 1.5
HTTP_TIMEOUT_SECONDS = 30

MONTHS = list(range(1, 13))

# Licence tiers, most permissive first. GBIF has no share-alike tier, so its
# tier "B" is identical to "A" and is skipped entirely rather than re-queried.
INAT_TIER_LICENSES = {
    "A": ["cc0", "cc-by"],
    "B": ["cc0", "cc-by", "cc-by-sa"],
    "C": ["cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"],
}
INAT_TIERS_ORDER = ["A", "B", "C"]

GBIF_TIER_LICENSES = {
    "A": ["CC0_1_0", "CC_BY_4_0"],
    "C": ["CC0_1_0", "CC_BY_4_0", "CC_BY_NC_4_0"],
}
GBIF_TIERS_ORDER = ["A", "C"]

# SPDX id to record on the generated Source, keyed by the widest tier used.
TIER_SPDX = {"A": "CC-BY-4.0", "B": "CC-BY-SA-4.0", "C": "CC-BY-NC-4.0"}

# Human-readable licence lists for attribution strings.
INAT_TIER_HUMAN = {
    "A": "CC0/CC BY",
    "B": "CC0/CC BY/CC BY-SA",
    "C": "CC0/CC BY/CC BY-SA/CC BY-NC/CC BY-NC-SA",
}
GBIF_TIER_HUMAN = {
    "A": "CC0 1.0 and CC BY 4.0",
    "C": "CC0 1.0, CC BY 4.0 and CC BY-NC 4.0",
}


class FetchError(RuntimeError):
    """Raised when an HTTP request fails (network error, HTTP error, or missing
    cache entry in --offline mode)."""


def today_str() -> str:
    return dt.date.today().isoformat()


# --------------------------------------------------------------------------
# HTTP + cache
# --------------------------------------------------------------------------


def default_cache_dir() -> Path:
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / "speeeecies"


def cache_key(url: str) -> str:
    return hashlib.sha256(url.encode("utf-8")).hexdigest()


def cache_path(cache_dir: Path, url: str) -> Path:
    return cache_dir / f"{cache_key(url)}.json"


@dataclasses.dataclass
class HttpClient:
    cache_dir: Path
    offline: bool = False
    user_agent: str = USER_AGENT
    _last_request_ts: dict = dataclasses.field(default_factory=dict)

    def get_json(self, url: str) -> Any:
        path = cache_path(self.cache_dir, url)
        if self.offline:
            if not path.exists():
                raise FetchError(f"offline: no cached response for {url}")
            return json.loads(path.read_text(encoding="utf-8"))

        data = self._http_get_with_retries(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return data

    def _polite_wait(self, host: str) -> None:
        if not host or "inaturalist" not in host:
            return
        last = self._last_request_ts.get(host)
        now = time.monotonic()
        if last is not None:
            elapsed = now - last
            if elapsed < INAT_MIN_INTERVAL_SECONDS:
                time.sleep(INAT_MIN_INTERVAL_SECONDS - elapsed)
        self._last_request_ts[host] = time.monotonic()

    def _http_get_with_retries(self, url: str) -> Any:
        host = urllib.parse.urlsplit(url).hostname or ""
        self._polite_wait(host)
        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self.user_agent, "Accept": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as resp:
                    body = resp.read()
                return json.loads(body)
            except urllib.error.HTTPError as e:
                if e.code in RETRY_STATUSES and attempt <= MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE**attempt)
                    continue
                raise FetchError(f"HTTP {e.code} for {url}: {e.reason}") from e
            except urllib.error.URLError as e:
                if attempt <= MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_BASE**attempt)
                    continue
                raise FetchError(f"network error for {url}: {e.reason}") from e


# --------------------------------------------------------------------------
# Pure counting / curve math (no network)
# --------------------------------------------------------------------------


def counts_from_inat_histogram(data: dict) -> dict[int, int]:
    hist = data.get("results", {}).get("month_of_year", {})
    return {int(k): int(v) for k, v in hist.items()}


def counts_from_gbif_facets(data: dict) -> dict[int, int]:
    facets = data.get("facets", [])
    month_facet = next((f for f in facets if f.get("field", "").upper() == "MONTH"), None)
    if not month_facet:
        return {}
    out = {}
    for c in month_facet.get("counts", []):
        name = c.get("name", "")
        if str(name).isdigit():
            out[int(name)] = int(c.get("count", 0))
    return out


def monthly_list(counts: dict[int, int]) -> list[int]:
    return [counts.get(m, 0) for m in MONTHS]


def share_curve(species_monthly: list[int], baseline_monthly: list[int]) -> list[float]:
    """share[m] = species[m] / baseline[m] (0 where baseline is 0), normalised to peak 1."""
    share = [
        (s / b) if b else 0.0
        for s, b in zip(species_monthly, baseline_monthly)
    ]
    peak = max(share) if share else 0.0
    if peak <= 0:
        return [0.0] * len(share)
    return [x / peak for x in share]


# Endotherm classes are observed all year, so dividing by the class's monthly
# total removes observer-effort seasonality. Ectotherm class totals collapse in
# winter, and that division inflates winter months for dormant species, so
# every other class uses raw counts normalised to the peak month.
EFFORT_SHARE_CLASSES = {"Aves", "Mammalia"}


def choose_curve_kind(requested: str, species_class: str) -> str:
    """Resolve `--curve auto` to "share" (endotherms) or "raw" (everything else)."""
    if requested != "auto":
        return requested
    return "share" if species_class in EFFORT_SHARE_CLASSES else "raw"


def raw_curve(species_monthly: list[int]) -> list[float]:
    """Monthly counts normalised to peak 1, with no effort baseline."""
    return share_curve(species_monthly, [1] * len(species_monthly))


def finalize_curve(curve: list[float]) -> list[float]:
    """Renormalise to peak exactly 1.0, round to 0.01."""
    peak = max(curve) if curve else 0.0
    if peak <= 0:
        return [0.0] * len(curve)
    return [round(x / peak, 2) for x in curve]


def mean_curves(a: list[float], b: list[float]) -> list[float]:
    return [(x + y) / 2 for x, y in zip(a, b)]


# --------------------------------------------------------------------------
# Source outcomes
# --------------------------------------------------------------------------


@dataclasses.dataclass
class SourceOutcome:
    name: str  # "inat" or "gbif"
    tier: Optional[str] = None
    total: int = 0
    monthly_species: Optional[list] = None
    monthly_baseline: Optional[list] = None
    share: Optional[list] = None
    usable: bool = False
    url: Optional[str] = None
    baseline_url: Optional[str] = None
    place_id: Optional[int] = None
    area: Optional[tuple] = None  # ("country", "GB") or ("gadmGid", "...")
    skipped_reason: Optional[str] = None
    error: Optional[str] = None
    attempts: list = dataclasses.field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.usable and self.share is not None

    @property
    def has_some_data(self) -> bool:
        return self.share is not None and self.total > 0


def build_inat_url(taxon_id: int, place_id: int, tier: str) -> str:
    lic = ",".join(INAT_TIER_LICENSES[tier])
    q = (
        f"taxon_id={taxon_id}&place_id={place_id}&interval=month_of_year"
        f"&date_field=observed&verifiable=true&license={lic}"
    )
    return f"https://api.inaturalist.org/v1/observations/histogram?{q}"


def build_gbif_url(taxon_key: int, area: tuple, tier: str) -> str:
    params: list[tuple[str, str]] = [("taxonKey", str(taxon_key))]
    params.append((area[0], str(area[1])))
    params += [
        ("facet", "month"),
        ("facetLimit", "12"),
        ("limit", "0"),
        ("occurrenceStatus", "PRESENT"),
        ("hasGeospatialIssue", "false"),
    ]
    for lic in GBIF_TIER_LICENSES[tier]:
        params.append(("license", lic))
    return "https://api.gbif.org/v1/occurrence/search?" + urllib.parse.urlencode(params)


def resolve_inat_class_taxon(client: HttpClient, species_taxon_id: int) -> tuple[int, Optional[str]]:
    url = f"https://api.inaturalist.org/v1/taxa/{species_taxon_id}"
    data = client.get_json(url)
    results = data.get("results", [])
    if not results:
        raise FetchError(f"no iNaturalist taxon found for id {species_taxon_id}")
    for a in results[0].get("ancestors", []):
        if a.get("rank") == "class":
            return a["id"], a.get("name")
    raise FetchError(f"no class ancestor found for iNaturalist taxon {species_taxon_id}")


def resolve_gbif_class_key(client: HttpClient, gbif_usage_key: int) -> int:
    url = f"https://api.gbif.org/v1/species/{gbif_usage_key}"
    data = client.get_json(url)
    class_key = data.get("classKey")
    if class_key is None:
        raise FetchError(f"no classKey found for GBIF usageKey {gbif_usage_key}")
    return class_key


def resolve_inat_country_place_id(client: HttpClient, iso2: str) -> tuple[Optional[int], Optional[str]]:
    """Resolve an ISO 3166-1 alpha-2 country code to an iNaturalist place id.

    Looks up the country's title via the GBIF country enumeration, then
    resolves it with the iNaturalist places autocomplete, taking the result
    with admin_level 0 (country). Some GBIF titles ("United Kingdom of Great
    Britain and Northern Ireland", "United States of America") do not match
    directly in iNaturalist's autocomplete, so this also tries the part of
    the title before " of " or before a comma.
    """
    countries = client.get_json("https://api.gbif.org/v1/enumeration/country")
    title = next((c["title"] for c in countries if c.get("iso2") == iso2), None)
    if title is None:
        return None, f"unknown ISO 3166-1 alpha-2 code {iso2!r} in GBIF country enumeration"

    candidates = [title]
    if " of " in title:
        candidates.append(title.split(" of ")[0].strip())
    if "," in title:
        candidates.append(title.split(",")[0].strip())

    for q in candidates:
        url = f"https://api.inaturalist.org/v1/places/autocomplete?q={urllib.parse.quote(q)}"
        data = client.get_json(url)
        for r in data.get("results", []):
            if r.get("admin_level") == 0:
                return r["id"], None
    return None, f"no admin_level 0 iNaturalist place found for {title!r}"


def _widen_tiers(
    client: HttpClient,
    tiers: list[str],
    build_url,
    extract_counts,
    min_obs: int,
    total_from,
) -> tuple[Optional[dict], list[dict]]:
    """Try tiers in order, stopping at the first tier whose total >= min_obs.
    Returns (chosen_attempt_or_None, all_attempts). chosen is None only when
    every tier raised a FetchError."""
    attempts: list[dict] = []
    chosen: Optional[dict] = None
    for tier in tiers:
        url = build_url(tier)
        try:
            data = client.get_json(url)
        except FetchError as e:
            attempts.append({"tier": tier, "url": url, "error": str(e)})
            break
        counts = extract_counts(data)
        monthly = monthly_list(counts)
        total = total_from(data, monthly)
        attempt = {"tier": tier, "url": url, "monthly": monthly, "total": total}
        attempts.append(attempt)
        chosen = attempt
        if total >= min_obs:
            break
    return chosen, attempts


def fetch_inat(
    client: HttpClient,
    species_taxon_id: int,
    place_id: int,
    min_obs: int,
    curve_kind: str = "share",
) -> SourceOutcome:
    def build_url(tier: str) -> str:
        return build_inat_url(species_taxon_id, place_id, tier)

    def total_from(data, monthly):
        return sum(monthly)

    chosen, attempts = _widen_tiers(
        client, INAT_TIERS_ORDER, build_url, counts_from_inat_histogram, min_obs, total_from
    )
    if chosen is None:
        err = attempts[-1]["error"] if attempts else "no attempts made"
        return SourceOutcome(name="inat", error=err, attempts=attempts, place_id=place_id)

    tier_used = chosen["tier"]
    usable = chosen["total"] >= min_obs
    outcome = SourceOutcome(
        name="inat",
        tier=tier_used,
        total=chosen["total"],
        monthly_species=chosen["monthly"],
        usable=usable,
        url=chosen["url"],
        place_id=place_id,
        attempts=attempts,
    )

    if curve_kind == "raw":
        outcome.share = raw_curve(chosen["monthly"])
        return outcome

    try:
        class_taxon_id, _class_name = resolve_inat_class_taxon(client, species_taxon_id)
        baseline_url = build_inat_url(class_taxon_id, place_id, tier_used)
        bdata = client.get_json(baseline_url)
        bmonthly = monthly_list(counts_from_inat_histogram(bdata))
        outcome.baseline_url = baseline_url
        outcome.monthly_baseline = bmonthly
        outcome.share = share_curve(chosen["monthly"], bmonthly)
    except FetchError as e:
        outcome.error = f"effort baseline unavailable: {e}"
        outcome.usable = False

    return outcome


def fetch_gbif(
    client: HttpClient,
    taxon_key: int,
    area: tuple,
    min_obs: int,
    curve_kind: str = "share",
) -> SourceOutcome:
    def build_url(tier: str) -> str:
        return build_gbif_url(taxon_key, area, tier)

    def total_from(data, monthly):
        # `count` is GBIF's authoritative total for the filters; the month
        # facet can omit records with no month recorded.
        return int(data.get("count", sum(monthly)))

    chosen, attempts = _widen_tiers(
        client, GBIF_TIERS_ORDER, build_url, counts_from_gbif_facets, min_obs, total_from
    )
    if chosen is None:
        err = attempts[-1]["error"] if attempts else "no attempts made"
        return SourceOutcome(name="gbif", error=err, attempts=attempts, area=area)

    tier_used = chosen["tier"]
    usable = chosen["total"] >= min_obs
    outcome = SourceOutcome(
        name="gbif",
        tier=tier_used,
        total=chosen["total"],
        monthly_species=chosen["monthly"],
        usable=usable,
        url=chosen["url"],
        area=area,
        attempts=attempts,
    )

    if curve_kind == "raw":
        outcome.share = raw_curve(chosen["monthly"])
        return outcome

    try:
        class_key = resolve_gbif_class_key(client, taxon_key)
        baseline_url = build_gbif_url(class_key, area, tier_used)
        bdata = client.get_json(baseline_url)
        bmonthly = monthly_list(counts_from_gbif_facets(bdata))
        outcome.baseline_url = baseline_url
        outcome.monthly_baseline = bmonthly
        outcome.share = share_curve(chosen["monthly"], bmonthly)
    except FetchError as e:
        outcome.error = f"effort baseline unavailable: {e}"
        outcome.usable = False

    return outcome


# --------------------------------------------------------------------------
# Fallback / combination logic
# --------------------------------------------------------------------------


@dataclasses.dataclass
class CurveResult:
    monthly: list
    method: str
    used: list  # subset of ["inat", "gbif"]
    observations: int


def combine_sources(
    inat: SourceOutcome, gbif: SourceOutcome, curve_kind: str = "share"
) -> tuple[Optional[CurveResult], list[str]]:
    notes: list[str] = []
    if inat.skipped_reason:
        notes.append(f"iNaturalist skipped: {inat.skipped_reason}")
    if inat.error:
        notes.append(f"iNaturalist error: {inat.error}")
    if gbif.skipped_reason:
        notes.append(f"GBIF skipped: {gbif.skipped_reason}")
    if gbif.error:
        notes.append(f"GBIF error: {gbif.error}")

    def why_not_used(o: SourceOutcome) -> str:
        if o.skipped_reason:
            return o.skipped_reason
        if o.error:
            return o.error
        if o.tier:
            return f"only {o.total} records at tier {o.tier} (< min-obs)"
        return "no data"

    if inat.ok and gbif.ok:
        combined = mean_curves(inat.share, gbif.share)
        return (
            CurveResult(
                monthly=finalize_curve(combined),
                method=f"mean(inat_{curve_kind}, gbif_{curve_kind})",
                used=["inat", "gbif"],
                observations=inat.total + gbif.total,
            ),
            notes,
        )

    if gbif.ok:
        notes.append(f"iNaturalist not used: {why_not_used(inat)}")
        return (
            CurveResult(
                monthly=finalize_curve(gbif.share),
                method=f"gbif_{curve_kind}",
                used=["gbif"],
                observations=gbif.total,
            ),
            notes,
        )

    if inat.ok:
        notes.append(f"GBIF not used: {why_not_used(gbif)}")
        return (
            CurveResult(
                monthly=finalize_curve(inat.share),
                method=f"inat_{curve_kind}",
                used=["inat"],
                observations=inat.total,
            ),
            notes,
        )

    candidates = [o for o in (inat, gbif) if o.has_some_data]
    if not candidates:
        return None, notes

    best = max(candidates, key=lambda o: o.total)
    notes.append(
        f"WARNING: no source reached --min-obs; using best available "
        f"({best.name}, n={best.total}, tier {best.tier})"
    )
    return (
        CurveResult(
            monthly=finalize_curve(best.share),
            method=f"{best.name}_{curve_kind}",
            used=[best.name],
            observations=best.total,
        ),
        notes,
    )


# --------------------------------------------------------------------------
# species.json merge
# --------------------------------------------------------------------------


def build_source_record(
    source_id: str,
    url: str,
    title: str,
    tier: str,
    attribution: str,
    accessed: str,
) -> dict:
    return {
        "id": source_id,
        "url": url,
        "title": title,
        "license": TIER_SPDX[tier],
        "attribution": attribution,
        "accessed": accessed,
        "kind": "api",
    }


def inat_attribution(tier: str) -> str:
    return f"iNaturalist contributors; observations licensed {INAT_TIER_HUMAN[tier]}, via the iNaturalist API"


def gbif_attribution(tier: str, accessed: str) -> str:
    return f"GBIF.org ({accessed}) GBIF Occurrence Search, records licensed {GBIF_TIER_HUMAN[tier]}"


def build_monthly_activity_entry(
    region: str,
    result: CurveResult,
    inat: SourceOutcome,
    gbif: SourceOutcome,
    min_obs: int,
) -> dict:
    query: dict = {"min_obs": min_obs}
    if inat.skipped_reason:
        query["inat"] = {"skipped": inat.skipped_reason}
    elif inat.error and inat.tier is None:
        query["inat"] = {"error": inat.error}
    else:
        query["inat"] = {
            "tier": inat.tier,
            "place_id": inat.place_id,
            "url": inat.url,
            "baseline_url": inat.baseline_url,
            "total": inat.total,
            "usable": inat.usable,
        }
    if gbif.skipped_reason:
        query["gbif"] = {"skipped": gbif.skipped_reason}
    elif gbif.error and gbif.tier is None:
        query["gbif"] = {"error": gbif.error}
    else:
        query["gbif"] = {
            "tier": gbif.tier,
            "area": list(gbif.area) if gbif.area else None,
            "url": gbif.url,
            "baseline_url": gbif.baseline_url,
            "total": gbif.total,
            "usable": gbif.usable,
        }
    query["used"] = result.used

    ids = [f"{name}-activity-{region.lower()}" for name in result.used]

    return {
        "region": region,
        "monthly": result.monthly,
        "method": result.method,
        "observations": result.observations,
        "sources": ids,
        "query": query,
    }


def merge_into_species(
    data: dict,
    region: str,
    entry: dict,
    source_records: list[dict],
) -> dict:
    """Mutate `data` in place: replace/insert the activity.regions entry for
    `region` (keeping other region entries), and add/update the given source
    records (keeping their position if they already exist)."""
    sources_list = data.setdefault("sources", [])
    by_id = {s.get("id"): i for i, s in enumerate(sources_list)}
    for rec in source_records:
        idx = by_id.get(rec["id"])
        if idx is None:
            sources_list.append(rec)
            by_id[rec["id"]] = len(sources_list) - 1
        else:
            sources_list[idx] = rec

    activity = data.setdefault("activity", {"regions": []})
    regions = activity.setdefault("regions", [])
    idx = next((i for i, r in enumerate(regions) if r.get("region") == region), None)
    if idx is None:
        regions.append(entry)
    else:
        regions[idx] = entry

    return data


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="fetch_activity.py",
        description="Build a monthly activity curve for a species/region from iNaturalist and GBIF.",
    )
    p.add_argument("slug", help="species/<slug> directory name")
    p.add_argument("--region", required=True, help="ISO 3166-1 alpha-2 or ISO 3166-2 region code")
    p.add_argument("--inat-place-id", type=int, default=None)
    p.add_argument("--gbif-gadm-gid", type=str, default=None)
    p.add_argument("--min-obs", type=int, default=300)
    p.add_argument(
        "--curve",
        choices=["auto", "share", "raw"],
        default="auto",
        help="share: divide by the class's monthly counts (effort-corrected); raw: counts only; "
        "auto (default): share for birds and mammals, raw for everything else",
    )
    p.add_argument("--write", action="store_true")
    p.add_argument("--cache-dir", type=Path, default=None)
    p.add_argument("--offline", action="store_true")
    p.add_argument("--root", type=Path, default=None)
    return p.parse_args(argv)


def print_summary(region: str, inat: SourceOutcome, gbif: SourceOutcome, result: CurveResult, notes: list[str]) -> None:
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    print(f"\nSummary for region {region}:")
    if inat.monthly_species is not None:
        print(f"  iNaturalist: tier {inat.tier}, total {inat.total} (place_id={inat.place_id}, usable={inat.usable})")
        print("    " + " ".join(f"{m}={c}" for m, c in zip(month_names, inat.monthly_species)))
    else:
        print(f"  iNaturalist: no data ({inat.skipped_reason or inat.error or 'unknown'})")
    if gbif.monthly_species is not None:
        print(f"  GBIF: tier {gbif.tier}, total {gbif.total} (area={gbif.area}, usable={gbif.usable})")
        print("    " + " ".join(f"{m}={c}" for m, c in zip(month_names, gbif.monthly_species)))
    else:
        print(f"  GBIF: no data ({gbif.skipped_reason or gbif.error or 'unknown'})")
    print(f"  Curve method: {result.method} (used: {', '.join(result.used)}, observations={result.observations})")
    for n in notes:
        print(f"  - {n}")


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    root = args.root or Path.cwd()
    cache_dir = args.cache_dir or default_cache_dir()
    client = HttpClient(cache_dir=cache_dir, offline=args.offline)

    species_path = root / "species" / args.slug / "species.json"
    try:
        data = json.loads(species_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"error: {species_path} not found", file=sys.stderr)
        return 1

    try:
        gbif_key = data["external"]["gbif_usage_key"]
        inat_taxon_id = data["external"]["inat_taxon_id"]
        species_class = data["taxonomy"]["class"]
        species_name = data["id"]
    except KeyError as e:
        print(f"error: species.json missing required field {e}", file=sys.stderr)
        return 1

    curve_kind = choose_curve_kind(args.curve, species_class)
    region = args.region
    is_subdivision = "-" in region

    # --- resolve iNat place ---
    inat_place_id = args.inat_place_id
    inat_skip_reason = None
    if inat_place_id is None:
        if is_subdivision:
            inat_skip_reason = (
                "ISO 3166-2 region given without --inat-place-id; pass --inat-place-id <id> "
                "(look it up at https://www.inaturalist.org/places) to query iNaturalist for this subdivision"
            )
        else:
            try:
                inat_place_id, resolve_note = resolve_inat_country_place_id(client, region)
            except FetchError as e:
                inat_place_id, resolve_note = None, str(e)
            if inat_place_id is None:
                inat_skip_reason = f"could not resolve iNaturalist place id for {region}: {resolve_note}"

    # --- resolve GBIF area ---
    gbif_area = None
    gbif_skip_reason = None
    if is_subdivision:
        if args.gbif_gadm_gid:
            gbif_area = ("gadmGid", args.gbif_gadm_gid)
        else:
            gbif_skip_reason = (
                "ISO 3166-2 region given without --gbif-gadm-gid; pass --gbif-gadm-gid <GADM GID> "
                "(look it up at https://gadm.org) to query GBIF for this subdivision"
            )
    else:
        gbif_area = ("country", region)

    # --- fetch ---
    if inat_skip_reason:
        inat_outcome = SourceOutcome(name="inat", skipped_reason=inat_skip_reason)
    else:
        try:
            inat_outcome = fetch_inat(client, inat_taxon_id, inat_place_id, args.min_obs, curve_kind)
        except FetchError as e:
            inat_outcome = SourceOutcome(name="inat", error=str(e))

    if gbif_skip_reason:
        gbif_outcome = SourceOutcome(name="gbif", skipped_reason=gbif_skip_reason)
    else:
        try:
            gbif_outcome = fetch_gbif(client, gbif_key, gbif_area, args.min_obs, curve_kind)
        except FetchError as e:
            gbif_outcome = SourceOutcome(name="gbif", error=str(e))

    result, notes = combine_sources(inat_outcome, gbif_outcome, curve_kind)
    if result is None:
        print(f"error: no usable observation data for {species_name} in {region}", file=sys.stderr)
        for n in notes:
            print(f"  - {n}", file=sys.stderr)
        return 1

    entry = build_monthly_activity_entry(region, result, inat_outcome, gbif_outcome, args.min_obs)

    print(json.dumps(entry, indent=2))
    print_summary(region, inat_outcome, gbif_outcome, result, notes)

    if args.write:
        accessed = today_str()
        source_records = []
        if "inat" in result.used:
            source_records.append(
                build_source_record(
                    f"inat-activity-{region.lower()}",
                    inat_outcome.url,
                    f"iNaturalist observations histogram for {species_name} in {region}",
                    inat_outcome.tier,
                    inat_attribution(inat_outcome.tier),
                    accessed,
                )
            )
        if "gbif" in result.used:
            source_records.append(
                build_source_record(
                    f"gbif-activity-{region.lower()}",
                    gbif_outcome.url,
                    f"GBIF occurrence search for {species_name} in {region}",
                    gbif_outcome.tier,
                    gbif_attribution(gbif_outcome.tier, accessed),
                    accessed,
                )
            )
        merge_into_species(data, region, entry, source_records)
        species_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nWrote {species_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
