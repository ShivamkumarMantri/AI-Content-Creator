import json
import os
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are an elite short-form video creative director and AI scriptwriter.
Your job is to transform any user idea into a viral, high-retention video production plan.

You must return ONLY valid, well-structured JSON matching this exact schema:
{
  "title": "Engaging Video Title",
  "hook": "Strong, attention-grabbing opening hook line (1 sentence)",
  "script": "Complete cohesive voiceover script spanning all scenes",
  "platform": "Selected Platform (e.g., Instagram Reels, TikTok, YouTube Shorts, LinkedIn)",
  "style": "Visual style direction",
  "total_duration": 30,
  "scenes": [
    {
      "duration": 5,
      "narration": "Exact spoken narration for this scene",
      "visual": "Detailed visual description of camera angle, background, action, and lighting",
      "on_screen_text": "PUNCHY 2-5 WORD ON-SCREEN TEXT"
    }
  ]
}

Guidelines:
- Scene durations must sum up approximately to the requested total duration (minimum 3s per scene).
- Tailor the pacing, hook, and call to action to the target platform (e.g., TikTok is snappy & energetic, LinkedIn is insightful & professional, YouTube Shorts is punchy & educational).
- On-screen text must be high-contrast, uppercase, and punchy.
- Return ONLY pure JSON without markdown code fences or conversational filler.
"""

def _fallback(topic: str, style: str, duration: int, platform: str = "Instagram Reels") -> Dict[str, Any]:
    """
    Intelligent local fallback generator that creates platform-tailored,
    structured short-form content plans without requiring external API keys.
    """
    clean_topic = topic.strip().rstrip(".").title()
    
    # Calculate scene count and durations based on total duration
    if duration <= 15:
        scene_count = 3
        per_scene = 5
    elif duration <= 30:
        scene_count = 5
        per_scene = 6
    elif duration <= 45:
        scene_count = 5
        per_scene = 9
    else:
        scene_count = 6
        per_scene = 10

    # Platform-specific tone presets
    platform_lower = platform.lower()
    if "tiktok" in platform_lower:
        hook_prefix = "Stop scrolling if you want to know how"
        cta_text = "Drop a comment and follow for more daily breakdowns."
        cta_headline = "FOLLOW FOR MORE"
    elif "linkedin" in platform_lower:
        hook_prefix = "Most professionals overlook this critical insight about"
        cta_text = "Save this framework for your team's next sprint."
        cta_headline = "KEY TAKEAWAY"
    elif "youtube" in platform_lower:
        hook_prefix = "Here is the number one secret behind"
        cta_text = "Subscribe for more rapid-fire deep dives."
        cta_headline = "SUBSCRIBE NOW"
    else:
        # Instagram Reels default
        hook_prefix = "Stop scrolling: here is the real truth about"
        cta_text = "Save this reel and share it with someone who needs to see this."
        cta_headline = "SAVE THIS REEL"

    hook = f"{hook_prefix} {clean_topic}."

    # Build progressive scene flow: Hook -> The Problem -> Core Insight -> Execution -> Actionable CTA
    scenes: List[Dict[str, Any]] = [
        {
            "duration": per_scene,
            "narration": hook,
            "visual": f"Dynamic {style} opening shot, fast zoom on {clean_topic}, high-contrast cinematic lighting with bold typography",
            "on_screen_text": clean_topic.upper()
        },
        {
            "duration": per_scene,
            "narration": f"The biggest mistake people make with {clean_topic} is overcomplicating the initial approach without clear strategy.",
            "visual": f"Split screen or problem illustration in {style} aesthetic, subtle chromatic aberration and tension lighting",
            "on_screen_text": "THE BIG MISTAKE"
        },
        {
            "duration": per_scene,
            "narration": f"Here is the proven framework: break down {clean_topic} into focused, measurable micro-steps you can execute immediately.",
            "visual": f"Clean {style} motion diagram, transformation effect with glowing UI accent cards highlighting solution flow",
            "on_screen_text": "THE FRAMEWORK"
        },
        {
            "duration": per_scene,
            "narration": "When you focus on consistent repetition rather than perfection, your compounding velocity multiplies effortlessly.",
            "visual": f"Modern motion graphics with animated progress telemetry, high-end {style} depth of field and smooth lighting shifts",
            "on_screen_text": "COMPOUND RESULTS"
        },
        {
            "duration": per_scene,
            "narration": cta_text,
            "visual": f"Confident closing card with {style} glowing neon accents, clean brand icon, and memorable exit animation",
            "on_screen_text": cta_headline
        }
    ]

    # Adjust to requested scene count
    if scene_count == 3:
        scenes = [scenes[0], scenes[2], scenes[4]]
        for s in scenes:
            s["duration"] = round(duration / 3)

    full_script = " ".join(s["narration"] for s in scenes)
    total_dur = sum(s["duration"] for s in scenes)

    return {
        "title": clean_topic,
        "hook": hook,
        "script": full_script,
        "platform": platform,
        "style": style,
        "total_duration": total_dur,
        "scenes": scenes,
        "engine": "local-fallback"
    }

def generate_content_plan(
    topic: str,
    style: str = "cinematic",
    duration: int = 30,
    platform: str = "Instagram Reels",
    api_key: str = None,
    model: str = None
) -> Dict[str, Any]:
    """
    Generate a production-ready structured short video plan.
    Uses OpenAI API if key is available in environment or arguments;
    otherwise seamlessly provides a platform-tailored local fallback plan.
    """
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback(topic, style, duration, platform)

    try:
        from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError
        client = OpenAI(api_key=api_key)
        model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        user_prompt = (
            f"Topic: {topic}\n"
            f"Visual Style: {style}\n"
            f"Target Duration: {duration} seconds\n"
            f"Platform: {platform}\n\n"
            f"Generate a compelling, high-converting short-form video plan with title, hook, full script, and scene breakdown."
        )

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        text = response.choices[0].message.content.strip()
        data = json.loads(text)

        # Normalize schema guarantees
        if "scenes" not in data or not isinstance(data["scenes"], list):
            fallback_plan = _fallback(topic, style, duration, platform)
            fallback_plan["ai_note"] = "OpenAI response schema incomplete. Local fallback generated."
            return fallback_plan

        data["platform"] = platform
        data["style"] = style
        if "script" not in data:
            data["script"] = " ".join(s.get("narration", "") for s in data["scenes"])
        if "total_duration" not in data:
            data["total_duration"] = sum(int(s.get("duration", 5)) for s in data["scenes"])
        data["engine"] = f"openai ({model})"
        data["ai_status"] = "success"
        return data

    except AuthenticationError:
        fallback_data = _fallback(topic, style, duration, platform)
        fallback_data["ai_note"] = "Invalid OpenAI API Key provided. Switched to local offline fallback engine."
        fallback_data["ai_status"] = "invalid_key_fallback"
        return fallback_data
    except RateLimitError:
        fallback_data = _fallback(topic, style, duration, platform)
        fallback_data["ai_note"] = "OpenAI Rate limit / Quota exceeded. Switched to local offline fallback engine."
        fallback_data["ai_status"] = "quota_fallback"
        return fallback_data
    except APIConnectionError:
        fallback_data = _fallback(topic, style, duration, platform)
        fallback_data["ai_note"] = "OpenAI network connection failed. Switched to local offline fallback engine."
        fallback_data["ai_status"] = "network_fallback"
        return fallback_data
    except Exception as exc:
        # Sanitize exception message so keys are never leaked
        clean_err = str(exc).replace(str(api_key), "[REDACTED_API_KEY]") if api_key else str(exc)
        fallback_data = _fallback(topic, style, duration, platform)
        fallback_data["ai_note"] = f"OpenAI error ({clean_err}). Local offline fallback applied."
        fallback_data["ai_status"] = "generic_fallback"
        return fallback_data
