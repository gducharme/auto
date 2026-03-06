from __future__ import annotations

from typing import Any

DEFAULT_ADAPTER_VERSION = "ig-adapter-v1"


def normalize_instagram_hashtags(
    hashtags: list[str],
    *,
    max_count: int = 8,
) -> list[str]:
    """Normalize hashtags to Instagram style and remove duplicates."""
    normalized: list[str] = []
    seen: set[str] = set()

    for raw in hashtags:
        token = str(raw or "").strip().lower()
        if not token:
            continue
        if token.startswith("#"):
            token = token[1:]

        cleaned = "".join(ch for ch in token if ch.isalnum() or ch == "_")
        if not cleaned:
            continue
        tag = f"#{cleaned}"
        if tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
        if len(normalized) >= max_count:
            break

    return normalized


def build_instagram_caption_blocks(
    *,
    hook: str,
    caption_seed: str,
    cta_strategy: str,
    hashtags: list[str],
) -> dict[str, str]:
    """Build caption and optional first comment from canonical content."""
    cta_map = {
        "save_and_share": "Save this and share with a friend.",
        "comment_prompt": "Comment your take below.",
        "share_prompt": "Share this with someone who needs it.",
    }
    cta_line = cta_map.get(cta_strategy, "Save this for later.")

    hook_line = hook.strip()
    seed = caption_seed.strip()
    body_lines = [part for part in [hook_line, seed, cta_line] if part]
    body = "\n\n".join(body_lines)

    hashtag_line = " ".join(hashtags).strip()
    if not hashtag_line:
        return {"caption_final": body, "first_comment_hashtags": ""}

    max_caption_len = 2200
    with_tags = f"{body}\n\n{hashtag_line}".strip()
    if len(with_tags) <= max_caption_len:
        return {
            "caption_final": with_tags,
            "first_comment_hashtags": "",
        }

    # Overflow strategy: keep body in caption, push tags to first comment.
    return {
        "caption_final": body,
        "first_comment_hashtags": hashtag_line,
    }


def derive_instagram_alt_text_bundle(
    *,
    publish_format: str,
    base_alt_text: str,
    visual_rhythm: list[str],
) -> dict[str, Any]:
    """Derive accessibility metadata for adapted publish payload."""
    if publish_format == "carousel":
        slides = [
            {
                "index": idx + 1,
                "alt_text": f"{base_alt_text} ({slot})",
            }
            for idx, slot in enumerate(visual_rhythm or ["hook", "insight", "cta"])
        ]
        return {
            "alt_text_primary": base_alt_text,
            "alt_text_by_media": slides,
        }

    return {
        "alt_text_primary": base_alt_text,
        "alt_text_by_media": [{"index": 1, "alt_text": base_alt_text}],
    }


def adapt_instagram_carousel_payload(
    *,
    canonical_payload: dict[str, Any],
    adapter_version: str,
) -> dict[str, Any]:
    rhythm = canonical_payload["asset_plan"]["visual_rhythm"]
    media_items = [
        {
            "position": idx + 1,
            "media_type": "image",
            "intent": slot,
            "uri": None,
        }
        for idx, slot in enumerate(rhythm)
    ]

    hashtags = normalize_instagram_hashtags(canonical_payload.get("hashtags") or [])
    captions = build_instagram_caption_blocks(
        hook=str(canonical_payload.get("hook") or ""),
        caption_seed=str(canonical_payload.get("caption_seed") or ""),
        cta_strategy=str(canonical_payload.get("cta_strategy") or ""),
        hashtags=hashtags,
    )
    alt_bundle = derive_instagram_alt_text_bundle(
        publish_format="carousel",
        base_alt_text=str(canonical_payload.get("alt_text") or ""),
        visual_rhythm=rhythm,
    )

    return {
        "adapter_version": adapter_version,
        "post_id": canonical_payload["post_id"],
        "network": canonical_payload["network"],
        "publish_format": "carousel",
        "hook": canonical_payload.get("hook"),
        "cta_strategy": canonical_payload.get("cta_strategy"),
        "media_items": media_items,
        "caption_final": captions["caption_final"],
        "first_comment_hashtags": captions["first_comment_hashtags"],
        "hashtags": hashtags,
        "accessibility": alt_bundle,
        "source": canonical_payload.get("asset_plan"),
    }


def adapt_instagram_reel_payload(
    *,
    canonical_payload: dict[str, Any],
    adapter_version: str,
) -> dict[str, Any]:
    hashtags = normalize_instagram_hashtags(canonical_payload.get("hashtags") or [])
    captions = build_instagram_caption_blocks(
        hook=str(canonical_payload.get("hook") or ""),
        caption_seed=str(canonical_payload.get("caption_seed") or ""),
        cta_strategy=str(canonical_payload.get("cta_strategy") or ""),
        hashtags=hashtags,
    )
    alt_bundle = derive_instagram_alt_text_bundle(
        publish_format="reel",
        base_alt_text=str(canonical_payload.get("alt_text") or ""),
        visual_rhythm=canonical_payload["asset_plan"]["visual_rhythm"],
    )

    return {
        "adapter_version": adapter_version,
        "post_id": canonical_payload["post_id"],
        "network": canonical_payload["network"],
        "publish_format": "reel",
        "hook": canonical_payload.get("hook"),
        "cta_strategy": canonical_payload.get("cta_strategy"),
        "media_items": [
            {
                "position": 1,
                "media_type": "video",
                "intent": "primary",
                "uri": None,
            }
        ],
        "caption_final": captions["caption_final"],
        "first_comment_hashtags": captions["first_comment_hashtags"],
        "hashtags": hashtags,
        "accessibility": alt_bundle,
        "source": canonical_payload.get("asset_plan"),
    }


def adapt_instagram_single_image_payload(
    *,
    canonical_payload: dict[str, Any],
    adapter_version: str,
) -> dict[str, Any]:
    hashtags = normalize_instagram_hashtags(canonical_payload.get("hashtags") or [])
    captions = build_instagram_caption_blocks(
        hook=str(canonical_payload.get("hook") or ""),
        caption_seed=str(canonical_payload.get("caption_seed") or ""),
        cta_strategy=str(canonical_payload.get("cta_strategy") or ""),
        hashtags=hashtags,
    )
    alt_bundle = derive_instagram_alt_text_bundle(
        publish_format="single_image",
        base_alt_text=str(canonical_payload.get("alt_text") or ""),
        visual_rhythm=canonical_payload["asset_plan"]["visual_rhythm"],
    )

    return {
        "adapter_version": adapter_version,
        "post_id": canonical_payload["post_id"],
        "network": canonical_payload["network"],
        "publish_format": "single_image",
        "hook": canonical_payload.get("hook"),
        "cta_strategy": canonical_payload.get("cta_strategy"),
        "media_items": [
            {
                "position": 1,
                "media_type": "image",
                "intent": "primary",
                "uri": None,
            }
        ],
        "caption_final": captions["caption_final"],
        "first_comment_hashtags": captions["first_comment_hashtags"],
        "hashtags": hashtags,
        "accessibility": alt_bundle,
        "source": canonical_payload.get("asset_plan"),
    }


def adapt_instagram_publish_payload(
    canonical_payload: dict[str, Any],
    *,
    adapter_version: str = DEFAULT_ADAPTER_VERSION,
) -> dict[str, Any]:
    """Adapt canonical pipeline payload into Instagram-native publish contract."""
    publish_format = str(canonical_payload.get("format") or "single_image")

    if publish_format == "carousel":
        adapted = adapt_instagram_carousel_payload(
            canonical_payload=canonical_payload,
            adapter_version=adapter_version,
        )
    elif publish_format == "reel":
        adapted = adapt_instagram_reel_payload(
            canonical_payload=canonical_payload,
            adapter_version=adapter_version,
        )
    else:
        adapted = adapt_instagram_single_image_payload(
            canonical_payload=canonical_payload,
            adapter_version=adapter_version,
        )

    # Backward compatibility with current scheduler publish path.
    adapted["caption"] = adapted.get("caption_final", "")
    adapted["format"] = adapted.get("publish_format")
    adapted["alt_text"] = adapted.get("accessibility", {}).get("alt_text_primary", "")
    adapted["asset_plan"] = canonical_payload.get("asset_plan")
    return adapted
