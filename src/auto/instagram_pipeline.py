from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .models import (
    InstagramPipelineConcept,
    InstagramPipelineRun,
    Post,
    PostStatus,
)
from .instagram_adapter import adapt_instagram_publish_payload
from .socials.registry import get_registry
from .utils import project_root


def _build_instagram_hashtag_seed(post: Post) -> list[str]:
    tokens = [word.strip(".,!?;:()[]{}\"'").lower() for word in post.title.split()]
    cleaned = [token for token in tokens if len(token) > 3]
    seeded = [f"#{token}" for token in cleaned[:6]]
    if not seeded:
        seeded = ["#creator", "#ideas", "#strategy"]
    return seeded


def generate_instagram_native_concepts(post: Post) -> list[dict[str, Any]]:
    """Build deterministic Instagram-native concept candidates for ``post``."""
    base_summary = (post.summary or post.title or "").strip()
    base_content = (post.content or "").strip()
    source_excerpt = (base_content or base_summary)[:220]

    hashtag_seed = _build_instagram_hashtag_seed(post)
    return [
        {
            "concept_key": "carousel_storyline",
            "format": "carousel",
            "hook": f"3 ideas from: {post.title}",
            "visual_rhythm": ["hook", "insight", "proof", "cta"],
            "caption_seed": f"{source_excerpt}\n\nSave this for later.",
            "hashtags": hashtag_seed[:5],
            "alt_text": f"Carousel summary for {post.title}",
            "cta_strategy": "save_and_share",
        },
        {
            "concept_key": "reel_pov",
            "format": "reel",
            "hook": f"If you only remember one thing from {post.title}",
            "visual_rhythm": ["pattern_interrupt", "key_point", "application"],
            "caption_seed": f"{source_excerpt}\n\nComment your take.",
            "hashtags": hashtag_seed[:4],
            "alt_text": f"Reel concept for {post.title}",
            "cta_strategy": "comment_prompt",
        },
        {
            "concept_key": "quote_card",
            "format": "single_image",
            "hook": f"Quote worth sharing: {post.title}",
            "visual_rhythm": ["quote", "context", "cta"],
            "caption_seed": f"{source_excerpt}\n\nShare with someone who needs this.",
            "hashtags": hashtag_seed[:3],
            "alt_text": f"Quote card for {post.title}",
            "cta_strategy": "share_prompt",
        },
    ]


def score_instagram_concept_weighted(
    concept: dict[str, Any],
    *,
    visual_weight: float = 0.45,
    engagement_weight: float = 0.4,
    risk_weight: float = 0.15,
) -> dict[str, float]:
    """Compute deterministic weighted scores for one concept."""
    format_name = str(concept.get("format", ""))
    rhythm = concept.get("visual_rhythm") or []
    hashtag_count = len(concept.get("hashtags") or [])

    visual_map = {
        "carousel": 0.9,
        "reel": 0.86,
        "single_image": 0.74,
    }
    visual_score = visual_map.get(format_name, 0.6)
    if len(rhythm) >= 4:
        visual_score = min(1.0, visual_score + 0.05)

    engagement_score = 0.6
    cta_strategy = str(concept.get("cta_strategy", ""))
    if cta_strategy in {"save_and_share", "comment_prompt", "share_prompt"}:
        engagement_score += 0.15
    engagement_score += min(0.1, hashtag_count * 0.02)
    engagement_score = min(1.0, engagement_score)

    risk_score = 0.95
    caption_seed = str(concept.get("caption_seed", ""))
    if len(caption_seed) > 1100:
        risk_score -= 0.15
    if hashtag_count > 10:
        risk_score -= 0.2
    risk_score = max(0.0, min(1.0, risk_score))

    total = (
        visual_weight * visual_score
        + engagement_weight * engagement_score
        + risk_weight * risk_score
    )

    return {
        "visual": round(visual_score, 4),
        "engagement": round(engagement_score, 4),
        "risk": round(risk_score, 4),
        "total": round(total, 4),
    }


def select_instagram_publish_candidate(
    scored_concepts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return scored concepts sorted from highest to lowest total score."""
    return sorted(
        scored_concepts,
        key=lambda c: (
            float(c.get("score_total") or 0.0),
            str(c.get("concept_key") or ""),
        ),
        reverse=True,
    )


def build_instagram_canonical_payload(
    post: Post,
    concept: dict[str, Any],
) -> dict[str, Any]:
    """Build canonical payload before adaptation to platform-specific schema."""

    return {
        "post_id": post.id,
        "network": "instagram",
        "format": concept.get("format"),
        "hook": concept.get("hook"),
        "caption_seed": concept.get("caption_seed"),
        "hashtags": concept.get("hashtags") or [],
        "alt_text": concept.get("alt_text"),
        "cta_strategy": concept.get("cta_strategy"),
        "asset_plan": {
            "visual_rhythm": concept.get("visual_rhythm") or [],
            "source_link": post.link,
            "source_title": post.title,
        },
    }


async def execute_instagram_pipeline_run(
    session: Session,
    *,
    post_id: str,
    network: str,
    pipeline_version: str,
    auto_publish: bool,
    quality_threshold: float,
    banned_terms: set[str],
    pipeline_enabled: bool,
    export_enabled: bool,
    export_dir: str,
) -> InstagramPipelineRun:
    """Execute one full Instagram-native pipeline run with deterministic steps."""
    post = session.get(Post, post_id)
    if post is None:
        raise ValueError(f"post not found: {post_id}")

    run = _find_or_create_instagram_pipeline_run(
        session,
        post_id=post_id,
        network=network,
        pipeline_version=pipeline_version,
    )

    if run.status == "published":
        return run

    concepts = generate_instagram_native_concepts(post)
    scored_concepts: list[dict[str, Any]] = []
    for concept in concepts:
        scores = score_instagram_concept_weighted(concept)
        scored_concepts.append(
            {
                **concept,
                "score_total": scores["total"],
                "score_breakdown": {
                    "visual": scores["visual"],
                    "engagement": scores["engagement"],
                    "risk": scores["risk"],
                },
            }
        )

    ranked_concepts = select_instagram_publish_candidate(scored_concepts)
    _replace_instagram_run_concepts(
        session, run_id=run.id, ranked_concepts=ranked_concepts
    )

    top_concept = ranked_concepts[0]
    top_model = (
        session.query(InstagramPipelineConcept)
        .filter(
            InstagramPipelineConcept.run_id == run.id,
            InstagramPipelineConcept.concept_key == top_concept["concept_key"],
        )
        .first()
    )
    if top_model is None:
        raise RuntimeError("failed to persist selected concept")

    canonical_payload = build_instagram_canonical_payload(post, top_concept)
    publish_payload = adapt_instagram_publish_payload(canonical_payload)
    run.selected_concept_id = top_model.id
    run.score_summary = json.dumps(
        {
            "selected": top_concept["concept_key"],
            "score_total": top_concept["score_total"],
            "quality_threshold": quality_threshold,
        },
        sort_keys=True,
    )
    run.publish_payload = json.dumps(publish_payload, sort_keys=True)

    low_quality = float(top_concept["score_total"]) < quality_threshold
    policy_blocked = contains_instagram_banned_terms(
        str(
            publish_payload.get("caption_final") or publish_payload.get("caption") or ""
        ),
        banned_terms,
    )

    if not pipeline_enabled:
        run.status = "disabled"
        run.last_error = "instagram pipeline disabled by environment"
        session.flush()
        if export_enabled:
            export_instagram_pipeline_artifacts(
                run=run,
                ranked_concepts=ranked_concepts,
                publish_payload=publish_payload,
                export_dir=export_dir,
            )
        return run

    if low_quality or policy_blocked:
        run.status = "needs_review"
        run.last_error = (
            "quality threshold not met"
            if low_quality
            else "banned terms found in publish payload"
        )
        session.flush()
        if export_enabled:
            export_instagram_pipeline_artifacts(
                run=run,
                ranked_concepts=ranked_concepts,
                publish_payload=publish_payload,
                export_dir=export_dir,
            )
        return run

    run.status = "ready"
    run.last_error = None

    if auto_publish:
        await _publish_instagram_pipeline_payload(session, run)

    session.flush()
    if export_enabled:
        export_instagram_pipeline_artifacts(
            run=run,
            ranked_concepts=ranked_concepts,
            publish_payload=publish_payload,
            export_dir=export_dir,
        )
    return run


def contains_instagram_banned_terms(text: str, banned_terms: set[str]) -> bool:
    """Return ``True`` when any configured banned term appears in ``text``."""
    normalized = text.lower()
    for term in banned_terms:
        token = term.strip().lower()
        if token and token in normalized:
            return True
    return False


def export_instagram_pipeline_artifacts(
    *,
    run: InstagramPipelineRun,
    ranked_concepts: list[dict[str, Any]],
    publish_payload: dict[str, Any],
    export_dir: str,
) -> Path:
    """Write pipeline artifacts to disk for inspection and debugging."""
    export_root = Path(export_dir).expanduser()
    if not export_root.is_absolute():
        export_root = project_root() / export_root

    safe_post_id = _safe_path_token(run.post_id)
    safe_network = _safe_path_token(run.network)
    safe_version = _safe_path_token(run.pipeline_version)

    artifact_dir = (
        export_root / safe_post_id / safe_network / safe_version / f"run_{run.id}"
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    run_doc = {
        "id": run.id,
        "post_id": run.post_id,
        "network": run.network,
        "pipeline_version": run.pipeline_version,
        "status": run.status,
        "selected_concept_id": run.selected_concept_id,
        "score_summary": json.loads(run.score_summary or "{}"),
        "published_at": run.published_at.isoformat() if run.published_at else None,
        "last_error": run.last_error,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }

    concepts_doc = [
        {
            "rank": idx,
            "concept_key": concept.get("concept_key"),
            "score_total": concept.get("score_total"),
            "score_breakdown": concept.get("score_breakdown") or {},
            "concept": {
                "format": concept.get("format"),
                "hook": concept.get("hook"),
                "visual_rhythm": concept.get("visual_rhythm") or [],
                "caption_seed": concept.get("caption_seed"),
                "hashtags": concept.get("hashtags") or [],
                "alt_text": concept.get("alt_text"),
                "cta_strategy": concept.get("cta_strategy"),
            },
        }
        for idx, concept in enumerate(ranked_concepts, start=1)
    ]

    (artifact_dir / "run.json").write_text(
        json.dumps(run_doc, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (artifact_dir / "concepts_ranked.json").write_text(
        json.dumps(concepts_doc, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (artifact_dir / "publish_payload.json").write_text(
        json.dumps(publish_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    preview_md = render_instagram_pipeline_preview_markdown(
        run=run,
        ranked_concepts=concepts_doc,
        publish_payload=publish_payload,
    )
    (artifact_dir / "preview.md").write_text(preview_md, encoding="utf-8")
    (artifact_dir / "preview.html").write_text(
        render_instagram_pipeline_preview_html(preview_md),
        encoding="utf-8",
    )

    return artifact_dir


def render_instagram_pipeline_preview_markdown(
    *,
    run: InstagramPipelineRun,
    ranked_concepts: list[dict[str, Any]],
    publish_payload: dict[str, Any],
) -> str:
    lines = [
        f"# Instagram Pipeline Preview: {run.post_id}",
        "",
        f"- Run ID: {run.id}",
        f"- Status: {run.status}",
        f"- Network: {run.network}",
        f"- Pipeline Version: {run.pipeline_version}",
        f"- Adapter Version: {publish_payload.get('adapter_version', '')}",
        "",
        "## Selected Draft",
        "",
        f"- Format: {publish_payload.get('publish_format', publish_payload.get('format', ''))}",
        f"- Hook: {publish_payload.get('hook', '')}",
        f"- CTA Strategy: {publish_payload.get('cta_strategy', '')}",
        f"- Alt Text: {publish_payload.get('alt_text', '')}",
        f"- Media Items: {len(publish_payload.get('media_items') or [])}",
        "",
        "### Caption Preview",
        "",
        publish_payload.get("caption_final", publish_payload.get("caption", "")),
        "",
        "## Ranked Concepts",
        "",
        "| Rank | Key | Score | Format | CTA |",
        "|---|---|---:|---|---|",
    ]

    for item in ranked_concepts:
        concept = item.get("concept") or {}
        lines.append(
            f"| {item.get('rank')} | {item.get('concept_key')} | "
            f"{item.get('score_total')} | {concept.get('format')} | "
            f"{concept.get('cta_strategy')} |"
        )

    return "\n".join(lines) + "\n"


def render_instagram_pipeline_preview_html(markdown_preview: str) -> str:
    escaped = (
        markdown_preview.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
        "  <title>Instagram Pipeline Preview</title>\n"
        "  <style>\n"
        "    body { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; "
        "max-width: 900px; margin: 2rem auto; padding: 0 1rem; }\n"
        "    pre { white-space: pre-wrap; line-height: 1.35; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        "  <pre>"
        f"{escaped}"
        "</pre>\n"
        "</body>\n"
        "</html>\n"
    )


def _safe_path_token(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)


def _find_or_create_instagram_pipeline_run(
    session: Session,
    *,
    post_id: str,
    network: str,
    pipeline_version: str,
) -> InstagramPipelineRun:
    run = (
        session.query(InstagramPipelineRun)
        .filter(
            InstagramPipelineRun.post_id == post_id,
            InstagramPipelineRun.network == network,
            InstagramPipelineRun.pipeline_version == pipeline_version,
        )
        .first()
    )
    if run is not None:
        return run

    run = InstagramPipelineRun(
        post_id=post_id,
        network=network,
        pipeline_version=pipeline_version,
        status="pending",
    )
    session.add(run)
    session.flush()
    return run


def _replace_instagram_run_concepts(
    session: Session,
    *,
    run_id: int,
    ranked_concepts: list[dict[str, Any]],
) -> None:
    session.query(InstagramPipelineConcept).filter(
        InstagramPipelineConcept.run_id == run_id
    ).delete()

    for idx, concept in enumerate(ranked_concepts, start=1):
        model = InstagramPipelineConcept(
            run_id=run_id,
            concept_key=str(concept["concept_key"]),
            concept_payload=json.dumps(
                {
                    "format": concept.get("format"),
                    "hook": concept.get("hook"),
                    "visual_rhythm": concept.get("visual_rhythm") or [],
                    "caption_seed": concept.get("caption_seed"),
                    "hashtags": concept.get("hashtags") or [],
                    "alt_text": concept.get("alt_text"),
                    "cta_strategy": concept.get("cta_strategy"),
                },
                sort_keys=True,
            ),
            score_total=float(concept.get("score_total") or 0.0),
            score_breakdown=json.dumps(
                concept.get("score_breakdown") or {}, sort_keys=True
            ),
            rank=idx,
        )
        session.add(model)
    session.flush()


async def _publish_instagram_pipeline_payload(
    session: Session,
    run: InstagramPipelineRun,
) -> None:
    plugin = get_registry().get(run.network)
    if plugin is None:
        raise ValueError(f"Unsupported network {run.network}")

    payload = json.loads(run.publish_payload or "{}")
    caption = str(payload.get("caption_final") or payload.get("caption") or "").strip()
    if not caption:
        raise ValueError("publish payload missing caption")

    status = session.get(PostStatus, {"post_id": run.post_id, "network": run.network})
    if status is None:
        status = PostStatus(
            post_id=run.post_id,
            network=run.network,
            scheduled_at=datetime.now(timezone.utc),
        )
        session.add(status)

    # Idempotency guard: once published for this post/network, skip duplicate plugin calls.
    if status.status == "published" and run.published_at is not None:
        return

    # Current plugin interface supports text + visibility.
    # Keep publish path deterministic and side-effect free in tests via fake plugins.
    await plugin.post(caption, visibility="unlisted")

    status.status = "published"
    status.last_error = None
    run.status = "published"
    run.last_error = None
    run.published_at = datetime.now(timezone.utc)
    status.attempts = (status.attempts or 0) + 1
