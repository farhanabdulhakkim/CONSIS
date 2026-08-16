"""
CONSIS v2.0 — Revision Engine
-------------------------------
Generates ONE day's Dual-Pattern Interleaving revision block via Groq,
chained off yesterday's output so the week actually builds instead of
repeating itself. Reads/writes core/revision_state.json (committed back
to the repo by the GitHub Action, same pattern as score.txt today).
"""

import os
import json
import time
from datetime import datetime, timezone

from groq import Groq
from core.roadmap import get_day_context

STATE_PATH = "core/revision_state.json"

# ---- fields each "focus" type must return, so downstream HTML never KeyErrors ----
FOCUS_SCHEMAS = {
    "anchor_deep_dive": ["visual_trigger", "plain_rule", "worked_micro_example"],
    "anchor_drill": ["trigger_variant", "gotcha", "one_liner"],
    "subsidiary_deep_dive": ["visual_trigger", "plain_rule", "worked_micro_example"],
    "connection_bridge": ["connection_bridge", "boundary_switch"],
    "mixed_problem": ["problem_statement", "which_pattern_first", "solution_sketch"],
    "recall_test": ["quiz_question", "quiz_answer", "confidence_tip"],
    "next_week_preview": ["teaser_line", "why_it_follows"],
}


def _load_state():
    if not os.path.exists(STATE_PATH):
        return {"cycle_day_index": 0, "streak": 0, "best_streak": 0,
                "last_run_date": None, "history": []}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def _yesterday_entry(state):
    return state["history"][-1] if state["history"] else None


def _build_prompt(ctx, yesterday):
    """
    Builds the exact system + user prompt sent to Groq for today's block.
    This is the 'final setup' piece — everything Groq needs to stay
    consistent with the Dual-Pattern Interleaving method AND continue
    from what was taught yesterday, instead of repeating itself.
    """
    system_prompt = (
        "You are a senior DSA coach who teaches using the 'Dual-Pattern "
        "Interleaving' method: every week pairs one Primary/Anchor pattern "
        "(70% weight) with one Subsidiary/Support pattern (30% weight) that "
        "commonly combines with or contrasts against it. Your job is NOT to "
        "dump theory — it is to produce ONE short, high-density revision "
        "block per day for a student who already knows the basics and is "
        "revising for placement interviews. Use the Feynman technique: "
        "plain English, no jargon-as-decoration, always ground abstract "
        "rules in a tiny concrete example. You must return ONLY valid JSON, "
        "no markdown fences, no preamble, no commentary — the caller parses "
        "your raw response directly."
    )

    continuity_block = "This is Day 1 of this pattern pair — no prior context."
    if yesterday:
        continuity_block = (
            f"Yesterday's focus was '{yesterday['focus']}' on the same "
            f"pair ({yesterday['primary']} / {yesterday['subsidiary']}). "
            f"Yesterday's key takeaway was: {yesterday.get('headline_takeaway', 'N/A')}. "
            "Do NOT repeat that content. Build on it, go deeper, or pivot "
            "to today's focus type using it as a reference point."
        )

    required_fields = FOCUS_SCHEMAS[ctx["focus"]]

    user_prompt = f"""
Today's context:
- Week {ctx['week_number']} of the 8-week roadmap (cycle #{ctx['cycle_number']})
- Day {ctx['day_in_week']} of 7 this week
- Primary/Anchor pattern: {ctx['primary']}
- Subsidiary/Support pattern: {ctx['subsidiary']}
- Default connection bridge (only use if today's focus needs it, otherwise
  write a sharper one yourself): "{ctx['default_bridge']}"
- Next week's upcoming Primary pattern (only relevant if focus is
  'next_week_preview'): {ctx['next_primary']}
- Today's FOCUS TYPE: {ctx['focus']}

{continuity_block}

Return a single JSON object with EXACTLY these keys:
- "headline_takeaway": one sentence (max 18 words) — the single thing to
  remember from today, written so tomorrow's prompt can reference it.
- {', '.join(f'"{f}"' for f in required_fields)}: fill these in following
  the definitions below for focus type "{ctx['focus']}".
- "diagram_hint": a short instruction (max 12 words) describing what a
  simple node/box diagram of today's content would look like, e.g.
  "two arrows converging on a shared middle index" — this drives an SVG
  rendered on the page, so keep it concrete and spatial, not abstract.

Field definitions by focus type:
- anchor_deep_dive / subsidiary_deep_dive: visual_trigger (what shape of
  problem should make the student's brain go "this is THIS pattern",
  1 sentence), plain_rule (no-jargon mechanism, 1-2 sentences), 
  worked_micro_example (a tiny 3-4 line walkthrough on a toy input).
- anchor_drill: trigger_variant (a twist on the usual trigger that still
  needs this pattern), gotcha (the #1 mistake people make applying it),
  one_liner (a memorable phrase to recall it under pressure).
- connection_bridge: connection_bridge (1-2 sentence Feynman sentence
  linking Primary and Subsidiary, better/sharper than the default given
  above), boundary_switch (1-2 sentences: "if X changes in the problem,
  switch from Primary to Subsidiary").
- mixed_problem: problem_statement (a short original LeetCode-style
  problem, 2-4 sentences, that genuinely needs BOTH patterns or a choice
  between them), which_pattern_first (1 sentence reasoning), 
  solution_sketch (3-5 line high-level approach, no full code).
- recall_test: quiz_question (references this WEEK's content, testable
  without looking anything up), quiz_answer (concise correct answer),
  confidence_tip (1 sentence: how to self-check if you truly know this
  or are pattern-matching blindly).
- next_week_preview: teaser_line (1 sentence hooking interest in next
  week's Primary pattern: {ctx['next_primary']}), why_it_follows (1
  sentence on why this ordering makes sense after this week).

Respond with ONLY the JSON object.
""".strip()

    return system_prompt, user_prompt


def _call_groq(system_prompt, user_prompt, max_retries=2):
    api_key = os.environ.get("GROQ_API_KEY", "")
    client = Groq(api_key=api_key)
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content
            return json.loads(raw)
        except Exception as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Groq revision call failed after retries: {last_err}")


def generate_today_revision():
    """
    Main entry point. Called once per day from main.py.
    Returns a dict ready to drop into the email template AND writes
    docs/revision.json for the GitHub Pages viewer.
    Advances streak/state and commits are handled by the workflow's git step.
    """
    state = _load_state()
    ctx = get_day_context(state.get("cycle_day_index", 0))
    yesterday = _yesterday_entry(state)

    system_prompt, user_prompt = _build_prompt(ctx, yesterday)

    try:
        ai_content = _call_groq(system_prompt, user_prompt)
    except Exception as e:
        ai_content = {
            "headline_takeaway": f"(offline fallback) Review {ctx['primary']} vs {ctx['subsidiary']} manually today.",
            "diagram_hint": "two labeled boxes with a dashed connecting line",
            "_error": str(e),
        }

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {
        "date": today_str,
        "week_number": ctx["week_number"],
        "day_in_week": ctx["day_in_week"],
        "cycle_number": ctx["cycle_number"],
        "primary": ctx["primary"],
        "subsidiary": ctx["subsidiary"],
        "focus": ctx["focus"],
        **ai_content,
    }

    # --- streak logic: only advances on a genuine new day, never double-counts ---
    if state.get("last_run_date") != today_str:
        state["streak"] = state.get("streak", 0) + 1 if state.get("last_run_date") else 1
        state["best_streak"] = max(state.get("best_streak", 1), state["streak"])
        state["cycle_day_index"] = state.get("cycle_day_index", 0) + 1
        state["last_run_date"] = today_str
        if "history" not in state:
            state["history"] = []
        state["history"].append(entry)
        state["history"] = state["history"][-56:]  # keep one full cycle of history

    state["today"] = entry
    state["roadmap_position"] = {
        "week_number": ctx["week_number"],
        "day_in_week": ctx["day_in_week"],
        "cycle_number": ctx["cycle_number"],
    }
    _save_state(state)

    # publish for the GitHub Pages viewer (both docs/ and root for compatibility)
    payload = {
        "today": entry,
        "streak": state["streak"],
        "best_streak": state["best_streak"],
        "roadmap_position": {
            "week_number": ctx["week_number"],
            "day_in_week": ctx["day_in_week"],
            "cycle_number": ctx["cycle_number"],
        },
        "history": state["history"][-14:],  # last 2 weeks for the page
    }
    os.makedirs("docs", exist_ok=True)
    with open("docs/revision.json", "w") as f:
        json.dump(payload, f, indent=2)
    with open("revision.json", "w") as f:
        json.dump(payload, f, indent=2)

    return entry
