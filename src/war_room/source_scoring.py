"""Source credibility scoring and source-class tagging - deterministic, domain-based."""

from __future__ import annotations

import re
from urllib.parse import urlparse

# --- Domain classification dictionaries ---

OFFICIAL_DOMAINS: set[str] = {
    ".gov",
    "courts.state",
    "uscourts.gov",
    "noaa.gov",
    "weather.gov",
    "nws.noaa.gov",
    "scc.virginia.gov",
    "floir.com",           # FL Office of Insurance Regulation
    "tdi.texas.gov",       # TX Dept of Insurance
    "doi.sc.gov",
    "insurance.ca.gov",
    "dfs.ny.gov",
    "flcourts.gov",        # FL state courts
    "courtlistener.com",   # Free case-law repository (CourtListener)
}

PROFESSIONAL_DOMAINS: set[str] = {
    "law.com",
    "reuters.com",
    "bloomberglaw.com",
    "insurancejournal.com",
    "ambest.com",
    "naic.org",
    "propertyinsurancecoveragelaw.com",
    "merlinlawgroup.com",
    "law.cornell.edu",
    "scholar.google.com",
    "casetext.com",
    "justia.com",
    "leagle.com",
    "jdsupra.com",
    "propublica.org",
    "citizensfla.com",
}

PAYWALLED_DOMAINS: set[str] = {
    "westlaw.com",
    "thomsonreuters.com",
    "lexisnexis.com",
    "heinonline.org",
    "next.westlaw.com",
    "advance.lexis.com",
}

PRIMARY_CASELAW_DOMAINS: set[str] = {
    "courtlistener.com",
    "scholar.google.com",
    "casetext.com",
    "justia.com",
    "leagle.com",
}

COMMENTARY_DOMAINS: set[str] = {
    "propertyinsurancecoveragelaw.com",
    "merlinlawgroup.com",
    "jdsupra.com",
    "law.com",
}

NEWS_DOMAINS: set[str] = {
    "reuters.com",
    "insurancejournal.com",
    "propublica.org",
}

STATUTE_PATH_HINTS = (
    "/cfr",
    "/code",
    "/rules",
    "/statute",
    "/statutes",
    "/usc",
)

COURT_OPINION_PATH_HINTS = (
    "/case",
    "/cases",
    "/opinion",
    "/opinions",
)

COMMENTARY_TITLE_TERMS = (
    "blog",
    "faq",
    "guide",
    "how to",
    "jd supra",
    "lessons",
    "must know",
    "overview",
    "what homeowners must know",
)

_CASE_TITLE_RE = re.compile(r"(?:^|\s)(v\.|vs\.|in re|ex rel\.)(?:\s|$)", re.IGNORECASE)

_BADGES = {
    "official": "green",
    "professional": "yellow",
    "unvetted": "red",
    "paywalled": "locked",
}

_LABELS = {
    "official": "Official source",
    "professional": "Professional source",
    "unvetted": "Unvetted source",
    "paywalled": "Paywalled - verify with subscription access",
}

_SOURCE_CLASS_LABELS = {
    "court_opinion": "Court opinion / primary law",
    "statute_regulation": "Statute / regulation",
    "government_guidance": "Agency / government guidance",
    "commentary": "Commentary / legal analysis",
    "news": "News / reporting",
    "other": "Other source",
}

_PRIMARY_SOURCE_CLASSES = {"court_opinion", "statute_regulation"}


def _classify_domain(hostname: str) -> str:
    """Classify a hostname into a scoring tier."""
    hostname = hostname.lower().removeprefix("www.")

    # Check paywalled first (takes priority)
    for domain in PAYWALLED_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return "paywalled"

    # Check official
    for domain in OFFICIAL_DOMAINS:
        if hostname.endswith(domain):
            return "official"

    # Check professional
    for domain in PROFESSIONAL_DOMAINS:
        if hostname == domain or hostname.endswith("." + domain):
            return "professional"

    return "unvetted"


def classify_source(url: str, title: str = "") -> dict:
    """Classify a URL into a reusable source class for ranking and review."""
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower().removeprefix("www.")
        path = (parsed.path or "").lower()
    except Exception:
        hostname = ""
        path = ""
    normalized_title = title.lower()

    source_class = "other"
    if any(hostname == domain or hostname.endswith("." + domain) for domain in PRIMARY_CASELAW_DOMAINS):
        source_class = "court_opinion"
    elif hostname.endswith(".gov") or hostname in {"courtlistener.com", "law.cornell.edu"}:
        court_host = "court" in hostname or hostname.endswith("uscourts.gov")
        opinion_like_path = any(hint in path for hint in COURT_OPINION_PATH_HINTS)
        opinion_like_title = bool(_CASE_TITLE_RE.search(title))
        if (court_host and (opinion_like_path or opinion_like_title)) or opinion_like_path:
            source_class = "court_opinion"
        elif any(hint in path for hint in STATUTE_PATH_HINTS):
            source_class = "statute_regulation"
        else:
            source_class = "government_guidance"
    elif any(hostname == domain or hostname.endswith("." + domain) for domain in NEWS_DOMAINS):
        source_class = "news"
    elif any(hostname == domain or hostname.endswith("." + domain) for domain in COMMENTARY_DOMAINS):
        source_class = "commentary"
    elif any(term in normalized_title for term in COMMENTARY_TITLE_TERMS):
        source_class = "commentary"

    return {
        "source_class": source_class,
        "source_class_label": _SOURCE_CLASS_LABELS[source_class],
        "is_primary_authority": source_class in _PRIMARY_SOURCE_CLASSES,
    }


def score_url(url: str, title: str = "") -> dict:
    """Score a URL for source credibility.

    Returns:
        dict with keys: url, hostname, tier, badge, label, source_class, source_class_label,
        is_primary_authority
    """
    try:
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
    except Exception:
        hostname = ""

    tier = _classify_domain(hostname)
    source_profile = classify_source(url, title)

    return {
        "url": url,
        "hostname": hostname,
        "tier": tier,
        "badge": _BADGES[tier],
        "label": _LABELS[tier],
        **source_profile,
    }


def format_badge(score: dict) -> str:
    """Format a score dict as a display string."""
    return f"[{score['badge']}] {score['label']} ({score['hostname']})"
