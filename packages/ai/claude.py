"""Claude API integration for reasoning and drafting."""

from typing import Any

import structlog
from anthropic import Anthropic

from src.core.config import get_settings
from src.core.models import DraftRequest, DraftResponse, MessageType, Source

logger = structlog.get_logger()
settings = get_settings()


# System prompts for different draft types
SYSTEM_PROMPTS = {
    MessageType.CHAT: """You are Dale's AI assistant, drafting Slack messages in his style.

Dale's communication style:
- Lowercase, concise, no fluff
- Technical but approachable
- Always actionable - next steps are clear
- Uses casual phrases like "awesome", "sounds good", "let me know"
- Professional but friendly tone
- Avoids emojis unless the context calls for it

When drafting:
1. Match the urgency and tone of the original message
2. Be direct and helpful
3. Include specific next steps when relevant
4. Keep it brief - if it can be said in fewer words, do it
""",

    MessageType.EMAIL: """You are Dale's AI assistant, drafting emails in his style.

Dale's email style:
- Clear subject lines that summarize the point
- Brief greeting, straight to the point
- Bullet points for multiple items
- Explicit action items or asks
- Professional but not stuffy
- Signs off simply: "Best," or "Thanks,"

When drafting:
1. Start with context if needed, then the ask
2. Use formatting to make it scannable
3. End with clear next steps
4. Keep paragraphs short (2-3 sentences max)
""",

    MessageType.PR_REVIEW: """You are Dale's AI assistant, drafting code review feedback in his style.

Dale's code review style:
- Constructive and specific
- Explains the "why" behind suggestions
- Uses phrases like "consider...", "what if we...", "minor: ..."
- Acknowledges good patterns when seen
- Focuses on maintainability and clarity
- References best practices or docs when relevant

When reviewing:
1. Start with overall impression if substantial
2. Be specific about line numbers and suggestions
3. Distinguish between blocking issues and nitpicks
4. Offer solutions, not just problems
""",

    MessageType.UPDATE: """You are Dale's AI assistant, drafting status updates in his style.

Dale's update style:
- Structured: what was done, what's next, blockers
- Concrete progress markers
- Honest about challenges
- Forward-looking
- No unnecessary padding

Format updates as:
- Done: [specific accomplishments]
- Next: [clear next steps]
- Blockers: [if any, otherwise omit]
""",
}


class ClaudeClient:
    """Client for Claude API interactions."""

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        self.model = "claude-sonnet-4-20250514"

    async def draft(
        self,
        request: DraftRequest,
        context: list[str],
    ) -> DraftResponse:
        """
        Generate a draft response using Claude.

        Args:
            request: The draft request with context and type
            context: Relevant context retrieved from RAG
        """
        if not self.client:
            raise ValueError("Claude client not configured - missing API key")

        # Build the system prompt
        base_prompt = SYSTEM_PROMPTS.get(request.draft_type, SYSTEM_PROMPTS[MessageType.CHAT])

        if request.tone:
            base_prompt += f"\n\nTone adjustment: {request.tone}"

        # Build context section
        context_section = ""
        if context:
            context_section = "\n\nRelevant context from past communications:\n" + "\n---\n".join(context[:5])

        # Build the user message
        user_message = f"""Draft a response to this:

{request.context}

{f"Additional context: {request.additional_context}" if request.additional_context else ""}
{context_section}

Generate a draft that Dale would send. Just the draft, no meta-commentary."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=base_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            draft_content = response.content[0].text

            # Calculate confidence based on context availability
            confidence = min(0.9, 0.5 + (len(context) * 0.1))

            return DraftResponse(
                draft_id=response.id,
                content=draft_content,
                confidence=confidence,
                sources_used=[],  # TODO: Include actual source IDs
                requires_approval=True,
            )

        except Exception as e:
            logger.error("Claude API error", error=str(e))
            raise

    async def analyze_patterns(self, messages: list[str]) -> dict[str, Any]:
        """
        Analyze a set of messages to extract communication patterns.

        This is used for learning and improving the drafting system.
        """
        if not self.client:
            raise ValueError("Claude client not configured")

        prompt = f"""Analyze these messages from a single author and extract communication patterns:

Messages:
{chr(10).join(f"- {m[:500]}" for m in messages[:20])}

Extract:
1. Common phrases and greetings
2. Sentence structure patterns
3. Tone characteristics
4. Common sign-offs
5. Formatting preferences (bullets, paragraphs, etc.)

Return as structured observations."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )

        return {
            "analysis": response.content[0].text,
            "message_count": len(messages),
        }
