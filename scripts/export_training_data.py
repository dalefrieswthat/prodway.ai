#!/usr/bin/env python3
"""
Export training data from cursor-context and agent transcripts.

Creates fine-tuning datasets in JSONL format suitable for:
- Anthropic Claude fine-tuning
- OpenAI fine-tuning
- Local model training (Llama, Mistral)

Usage:
    python scripts/export_training_data.py --output training_data.jsonl
    python scripts/export_training_data.py --format openai --output openai_training.jsonl
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Generator

# Paths relative to repo root
REPO_ROOT = Path(__file__).parent.parent
CURSOR_CONTEXT = REPO_ROOT / "cursor-context"
AGENT_TRANSCRIPTS = Path.home() / ".cursor/projects/Users-daleyarborough-Code-prodway/agent-transcripts"


def extract_markdown_sections(content: str) -> dict:
    """Extract sections from a markdown file."""
    sections = {}
    current_section = "preamble"
    current_content = []

    for line in content.split("\n"):
        if line.startswith("## "):
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def extract_qa_pairs_from_transcript(content: str) -> Generator:
    """
    Extract (instruction, response) pairs from agent transcripts.

    Looks for patterns like:
    - user: <question>
    - assistant: <response>
    """
    # Simple pattern: user followed by assistant
    user_pattern = re.compile(r"^user:\s*(.+?)(?=^assistant:|^user:|^tool:|$)", re.MULTILINE | re.DOTALL)
    assistant_pattern = re.compile(r"^assistant:\s*(.+?)(?=^user:|^tool:|$)", re.MULTILINE | re.DOTALL)

    users = user_pattern.findall(content)
    assistants = assistant_pattern.findall(content)

    # Pair them up
    for user_msg, assistant_msg in zip(users, assistants):
        user_msg = user_msg.strip()
        assistant_msg = assistant_msg.strip()

        # Skip if either is too short (likely noise)
        if len(user_msg) < 10 or len(assistant_msg) < 50:
            continue

        # Skip if assistant response is just a tool call
        if assistant_msg.startswith("[Tool call]"):
            continue

        yield {
            "instruction": user_msg,
            "response": assistant_msg,
            "source": "transcript"
        }


def extract_sow_examples(cursor_context: Path) -> Generator:
    """
    Extract SOW generation examples from specs and templates.
    """
    sow_spec = cursor_context / "spec" / "SOWFLOW_SPEC.md"
    if sow_spec.exists():
        content = sow_spec.read_text()
        sections = extract_markdown_sections(content)

        # Look for example inputs/outputs
        if "Examples" in sections or "Usage" in sections:
            yield {
                "instruction": "Generate a SOW for a Kubernetes migration project",
                "response": sections.get("Examples", sections.get("Usage", "")),
                "source": "sow_spec"
            }


def extract_architecture_decisions(cursor_context: Path) -> Generator:
    """
    Extract architecture decisions and their rationale.
    """
    for md_file in cursor_context.glob("**/*.md"):
        try:
            content = md_file.read_text()
            sections = extract_markdown_sections(content)

            # Look for decision-related sections
            for section_name, section_content in sections.items():
                if any(kw in section_name.lower() for kw in ["decision", "why", "architecture", "design"]):
                    if len(section_content) > 100:  # Skip tiny sections
                        yield {
                            "instruction": f"Explain the {section_name} for {md_file.stem}",
                            "response": section_content,
                            "source": str(md_file.relative_to(cursor_context))
                        }
        except Exception:
            continue


def format_for_anthropic(example: dict) -> dict:
    """Format example for Anthropic fine-tuning format."""
    return {
        "prompt": f"Human: {example['instruction']}\n\nAssistant:",
        "completion": f" {example['response']}"
    }


def format_for_openai(example: dict) -> dict:
    """Format example for OpenAI fine-tuning format."""
    return {
        "messages": [
            {"role": "system", "content": "You are a senior software consultant helping with technical decisions and service delivery."},
            {"role": "user", "content": example["instruction"]},
            {"role": "assistant", "content": example["response"]}
        ]
    }


def format_for_alpaca(example: dict) -> dict:
    """Format example for Alpaca/Llama fine-tuning format."""
    return {
        "instruction": example["instruction"],
        "input": "",
        "output": example["response"]
    }


def main():
    parser = argparse.ArgumentParser(description="Export training data for model fine-tuning")
    parser.add_argument("--output", "-o", default="training_data.jsonl", help="Output file path")
    parser.add_argument("--format", "-f", choices=["anthropic", "openai", "alpaca"], default="anthropic",
                        help="Output format for fine-tuning")
    parser.add_argument("--min-response-length", type=int, default=100,
                        help="Minimum response length to include")
    args = parser.parse_args()

    # Select formatter
    formatters = {
        "anthropic": format_for_anthropic,
        "openai": format_for_openai,
        "alpaca": format_for_alpaca
    }
    formatter = formatters[args.format]

    examples = []

    # 1. Extract from cursor-context
    if CURSOR_CONTEXT.exists():
        print(f"Processing cursor-context at {CURSOR_CONTEXT}...")
        for example in extract_architecture_decisions(CURSOR_CONTEXT):
            if len(example["response"]) >= args.min_response_length:
                examples.append(example)

        for example in extract_sow_examples(CURSOR_CONTEXT):
            if len(example["response"]) >= args.min_response_length:
                examples.append(example)

    # 2. Extract from agent transcripts
    if AGENT_TRANSCRIPTS.exists():
        print(f"Processing agent transcripts at {AGENT_TRANSCRIPTS}...")
        for transcript_file in AGENT_TRANSCRIPTS.glob("*.txt"):
            try:
                content = transcript_file.read_text()
                for example in extract_qa_pairs_from_transcript(content):
                    if len(example["response"]) >= args.min_response_length:
                        examples.append(example)
            except Exception as e:
                print(f"  Warning: Could not process {transcript_file.name}: {e}")

    # 3. Write output
    output_path = Path(args.output)
    with output_path.open("w") as f:
        for example in examples:
            formatted = formatter(example)
            f.write(json.dumps(formatted) + "\n")

    print(f"\nExported {len(examples)} training examples to {output_path}")
    print(f"Format: {args.format}")

    # Summary by source
    sources = {}
    for ex in examples:
        src = ex.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    print("\nBy source:")
    for src, count in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")


if __name__ == "__main__":
    main()
