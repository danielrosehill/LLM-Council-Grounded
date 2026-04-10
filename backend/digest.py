"""Digest generation: Typst PDF report and podcast script with Edge TTS."""

import os
import json
import subprocess
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from .config import OUTPUT_DIR, COUNCIL_MODEL
from .openrouter import query_model


def ensure_output_dir():
    """Ensure the output directory exists."""
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(OUTPUT_DIR, "reports")).mkdir(parents=True, exist_ok=True)
    Path(os.path.join(OUTPUT_DIR, "podcasts")).mkdir(parents=True, exist_ok=True)


def generate_typst_source(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]]
) -> str:
    """Generate a Typst document source for the council findings."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Escape special Typst characters
    def esc(text: str) -> str:
        return (text
                .replace("\\", "\\\\")
                .replace("#", "\\#")
                .replace("$", "\\$")
                .replace("@", "\\@")
                .replace("<", "\\<")
                .replace(">", "\\>")
                .replace("_", "\\_")
                .replace("*", "\\*"))

    # Build stage 1 sections
    stage1_sections = ""
    for result in stage1_results:
        name = esc(result.get('name', result['model']))
        response = esc(result['response'])
        stage1_sections += f"""
=== {name}

{response}

"""

    # Build aggregate rankings table
    rankings_table = ""
    if aggregate_rankings:
        rankings_table = """
#table(
  columns: (auto, 1fr, auto, auto),
  [*Rank*], [*Council Member*], [*Avg Score*], [*Votes*],
"""
        for i, agg in enumerate(aggregate_rankings):
            rank = str(i + 1)
            model = esc(agg['model'])
            avg = str(agg['average_rank'])
            count = str(agg['rankings_count'])
            rankings_table += f"  [{rank}], [{model}], [{avg}], [{count}],\n"
        rankings_table += ")\n"

    # Build stage 2 sections
    stage2_sections = ""
    for result in stage2_results:
        name = esc(result.get('name', result['model']))
        ranking = esc(result['ranking'])
        stage2_sections += f"""
=== {name}'s Evaluation

{ranking}

"""

    # Chairman synthesis
    chairman_name = esc(stage3_result.get('name', 'Chairman'))
    chairman_response = esc(stage3_result['response'])

    typst_source = f"""#set document(
  title: "LLM Council Report",
  date: datetime.today(),
)

#set page(
  paper: "a4",
  margin: (x: 2.5cm, y: 2.5cm),
  header: align(right, text(size: 9pt, fill: gray)[LLM Council Report -- {timestamp}]),
  footer: align(center, text(size: 9pt, fill: gray)[Page #counter(page).display()]),
)

#set text(font: "IBM Plex Sans", size: 11pt)
#set heading(numbering: "1.1")
#set par(justify: true)

#align(center)[
  #text(size: 24pt, weight: "bold")[LLM Council Report]

  #v(0.5em)
  #text(size: 12pt, fill: gray)[Generated {timestamp}]
]

#v(1em)

#rect(fill: rgb("#f0f7ff"), stroke: rgb("#d0e7ff"), radius: 4pt, width: 100%, inset: 12pt)[
  #text(weight: "bold")[Query:]
  #v(0.3em)
  {esc(user_query)}
]

#v(1em)

= Stage 1: Individual Perspectives

Each council member approaches the question from their unique thinking style.

{stage1_sections}

= Stage 2: Peer Rankings

Council members evaluated each other's responses anonymously.

== Aggregate Rankings

{rankings_table}

{stage2_sections}

= Stage 3: Chairman's Synthesis

The Chairman synthesized all perspectives and rankings into a final answer.

#rect(fill: rgb("#f0fff0"), stroke: rgb("#c8e6c8"), radius: 4pt, width: 100%, inset: 12pt)[
  #text(weight: "bold")[{chairman_name}'s Final Answer:]

  #v(0.5em)
  {chairman_response}
]
"""
    return typst_source


async def generate_pdf_report(
    conversation_id: str,
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]]
) -> str:
    """
    Generate a PDF report from council findings using Typst.

    Returns the path to the generated PDF file.
    """
    ensure_output_dir()

    typst_source = generate_typst_source(
        user_query, stage1_results, stage2_results,
        stage3_result, aggregate_rankings
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    typst_path = os.path.join(OUTPUT_DIR, "reports", f"council_{timestamp}.typ")
    pdf_path = os.path.join(OUTPUT_DIR, "reports", f"council_{timestamp}.pdf")

    with open(typst_path, 'w') as f:
        f.write(typst_source)

    try:
        result = subprocess.run(
            ["typst", "compile", typst_path, pdf_path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"Typst compilation error: {result.stderr}")
            return typst_path  # Return .typ path as fallback
    except FileNotFoundError:
        print("Typst not installed. Returning .typ source file.")
        return typst_path
    except subprocess.TimeoutExpired:
        print("Typst compilation timed out.")
        return typst_path

    return pdf_path


async def generate_podcast_script(
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]]
) -> str:
    """
    Use an LLM to write a personal podcast script summarizing the council findings.
    The script is written as if narrated directly to the user.
    """
    council_summary = "\n\n".join([
        f"**{r.get('name', r['model'])}** said:\n{r['response'][:500]}..."
        if len(r['response']) > 500 else f"**{r.get('name', r['model'])}** said:\n{r['response']}"
        for r in stage1_results
    ])

    rankings_summary = ""
    if aggregate_rankings:
        rankings_summary = "Rankings (best to worst): " + ", ".join([
            f"{a['model']} (avg {a['average_rank']})"
            for a in aggregate_rankings
        ])

    chairman_summary = stage3_result.get('response', '')[:1000]

    script_prompt = f"""You are a podcast script writer. Write a short, engaging personal podcast episode
(2-3 minutes when read aloud) that summarizes the findings of an LLM Council deliberation.

The podcast is addressed directly to the listener (the person who submitted the query).
Use a warm, conversational tone -- like a knowledgeable friend giving you a briefing.

Structure:
1. Brief intro: "Here's your council briefing on [topic]..."
2. Highlight the most interesting perspectives from the council members
3. Note where they agreed and disagreed
4. Share the aggregate rankings and what they reveal
5. Deliver the chairman's synthesized answer as the key takeaway
6. Brief sign-off

Original question: {user_query}

Council member perspectives:
{council_summary}

{rankings_summary}

Chairman's synthesis:
{chairman_summary}

Write the podcast script now. Use natural spoken language, not written prose.
Include [PAUSE] markers where natural pauses should occur."""

    messages = [
        {"role": "system", "content": (
            "You are a podcast scriptwriter who creates engaging audio briefings. "
            "Write in natural spoken English with clear pacing. The listener is the "
            "person who asked the original question."
        )},
        {"role": "user", "content": script_prompt}
    ]

    response = await query_model(COUNCIL_MODEL, messages)

    if response is None:
        return "Error: Unable to generate podcast script."

    return response.get('content', '')


async def generate_podcast_audio(script: str, conversation_id: str) -> str:
    """
    Generate audio from the podcast script using Microsoft Edge TTS.

    Returns the path to the generated audio file.
    """
    ensure_output_dir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    audio_path = os.path.join(OUTPUT_DIR, "podcasts", f"council_{timestamp}.mp3")
    script_path = os.path.join(OUTPUT_DIR, "podcasts", f"council_{timestamp}.txt")

    # Clean script for TTS: remove [PAUSE] markers, replace with periods for natural pauses
    clean_script = script.replace("[PAUSE]", "...")

    # Save script
    with open(script_path, 'w') as f:
        f.write(script)

    try:
        # Use edge-tts CLI
        process = await asyncio.create_subprocess_exec(
            "edge-tts",
            "--voice", "en-US-AriaNeural",
            "--text", clean_script,
            "--write-media", audio_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)

        if process.returncode != 0:
            print(f"Edge TTS error: {stderr.decode()}")
            return script_path  # Return script as fallback

    except FileNotFoundError:
        print("edge-tts not installed. Install with: pip install edge-tts")
        return script_path
    except asyncio.TimeoutError:
        print("Edge TTS generation timed out.")
        return script_path

    return audio_path


async def generate_full_digest(
    conversation_id: str,
    user_query: str,
    stage1_results: List[Dict[str, Any]],
    stage2_results: List[Dict[str, Any]],
    stage3_result: Dict[str, Any],
    aggregate_rankings: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Generate both PDF report and podcast from council findings.

    Returns dict with paths to generated files.
    """
    # Run PDF and podcast script generation in parallel
    pdf_task = generate_pdf_report(
        conversation_id, user_query, stage1_results,
        stage2_results, stage3_result, aggregate_rankings
    )
    script_task = generate_podcast_script(
        user_query, stage1_results, stage2_results,
        stage3_result, aggregate_rankings
    )

    pdf_path, podcast_script = await asyncio.gather(pdf_task, script_task)

    # Generate audio from script
    audio_path = await generate_podcast_audio(podcast_script, conversation_id)

    return {
        "pdf_path": pdf_path,
        "podcast_script": podcast_script,
        "audio_path": audio_path,
    }
