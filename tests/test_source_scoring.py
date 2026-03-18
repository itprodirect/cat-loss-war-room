"""Tests for source_scoring module."""

from war_room.source_scoring import format_badge, score_url


def test_gov_is_official():
    result = score_url("https://www.weather.gov/reports/milton")
    assert result["tier"] == "official"
    assert result["badge"] == "green"


def test_noaa_is_official():
    result = score_url("https://nws.noaa.gov/data/storm-report")
    assert result["tier"] == "official"
    assert result["badge"] == "green"


def test_fema_is_official():
    result = score_url("https://www.fema.gov/disaster/4834")
    assert result["tier"] == "official"
    assert result["badge"] == "green"


def test_law_firm_is_professional():
    result = score_url("https://www.merlinlawgroup.com/blog/post")
    assert result["tier"] == "professional"
    assert result["badge"] == "yellow"


def test_insurance_journal_is_professional():
    result = score_url("https://www.insurancejournal.com/article/123")
    assert result["tier"] == "professional"
    assert result["badge"] == "yellow"


def test_citizensfla_is_professional():
    result = score_url("https://www.citizensfla.com/documents/20702/460724/brochure.pdf")
    assert result["tier"] == "professional"
    assert result["badge"] == "yellow"


def test_random_blog_is_unvetted():
    result = score_url("https://random-insurance-blog.wordpress.com/post")
    assert result["tier"] == "unvetted"
    assert result["badge"] == "red"


def test_westlaw_is_paywalled():
    result = score_url("https://next.westlaw.com/Document/I123")
    assert result["tier"] == "paywalled"
    assert result["badge"] == "locked"


def test_lexis_is_paywalled():
    result = score_url("https://advance.lexis.com/document/123")
    assert result["tier"] == "paywalled"
    assert result["badge"] == "locked"


def test_format_badge_output():
    result = score_url("https://www.weather.gov/report")
    badge = format_badge(result)
    assert "[green]" in badge
    assert "Official source" in badge


def test_malformed_url_returns_unvetted():
    result = score_url("not-a-url")
    assert result["tier"] == "unvetted"


def test_www_weather_gov_not_mangled():
    """Regression: lstrip('www.') would mangle 'weather.gov' -> 'eather.gov'."""
    result = score_url("https://www.weather.gov/report")
    assert result["tier"] == "official"
    assert "weather.gov" in result["hostname"]


def test_flcourts_gov_is_official():
    result = score_url("https://www.flcourts.gov/case/123")
    assert result["tier"] == "official"
    assert result["badge"] == "green"


def test_courtlistener_is_official():
    result = score_url("https://www.courtlistener.com/opinion/12345/")
    assert result["tier"] == "official"
    assert result["badge"] == "green"
