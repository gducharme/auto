from __future__ import annotations

from auto.instagram_adapter import (
    DEFAULT_ADAPTER_VERSION,
    adapt_instagram_publish_payload,
    normalize_instagram_hashtags,
)


def _canonical_payload(publish_format: str) -> dict[str, object]:
    return {
        "post_id": "post-1",
        "network": "instagram",
        "format": publish_format,
        "hook": "Fasting basics",
        "caption_seed": "Start with 12:12 before extending your window.",
        "hashtags": ["#Longevity", "fasting", "FASTING", "clean-eating"],
        "alt_text": "Longevity fasting overview",
        "cta_strategy": "save_and_share",
        "asset_plan": {
            "visual_rhythm": ["hook", "insight", "proof", "cta"],
            "source_link": "https://example.com",
            "source_title": "Fasting post",
        },
    }


def test_normalize_instagram_hashtags_deduplicates_and_sanitizes():
    tags = normalize_instagram_hashtags(
        ["#Longevity", "fasting", "FASTING", "bad-tag!"]
    )
    assert tags == ["#longevity", "#fasting", "#badtag"]


def test_adapt_instagram_publish_payload_carousel_contract():
    payload = adapt_instagram_publish_payload(_canonical_payload("carousel"))

    assert payload["adapter_version"] == DEFAULT_ADAPTER_VERSION
    assert payload["publish_format"] == "carousel"
    assert payload["format"] == "carousel"
    assert payload["caption_final"]
    assert payload["caption"] == payload["caption_final"]
    assert isinstance(payload["media_items"], list)
    assert len(payload["media_items"]) == 4
    assert payload["accessibility"]["alt_text_by_media"]


def test_adapt_instagram_publish_payload_reel_contract():
    payload = adapt_instagram_publish_payload(_canonical_payload("reel"))

    assert payload["publish_format"] == "reel"
    assert len(payload["media_items"]) == 1
    assert payload["media_items"][0]["media_type"] == "video"


def test_adapt_instagram_publish_payload_single_image_fallback():
    payload = adapt_instagram_publish_payload(_canonical_payload("single_image"))

    assert payload["publish_format"] == "single_image"
    assert len(payload["media_items"]) == 1
    assert payload["media_items"][0]["media_type"] == "image"
