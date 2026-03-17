"""
LLM Witness Implementations for TruthCert

Provides witness extraction using Claude (Anthropic) and Z.AI APIs.
Requires API keys stored in .env file.
"""

import os
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Try to load dotenv
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# Try to load anthropic
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Try to load openai (for Z.AI compatibility)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class WitnessExtraction:
    """Result from a single witness extraction."""
    witness_id: str
    model_name: str
    model_family: str  # "anthropic", "zai", "openai", etc.
    extractions: Dict[str, Any]
    confidence_scores: Dict[str, float]
    tokens_used: int
    cost_usd: float
    raw_response: Optional[str] = None
    error: Optional[str] = None


def load_api_keys(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load API keys from .env file.

    Args:
        env_path: Path to .env file. If None, searches in standard locations.

    Returns:
        Dictionary of API keys found.
    """
    if not HAS_DOTENV:
        print("Warning: python-dotenv not installed. Using environment variables only.")
        print("Install with: pip install python-dotenv")
    else:
        # Search for .env file
        search_paths = [
            env_path,
            Path.cwd() / ".env",
            Path(__file__).parent.parent / ".env",
            Path.home() / ".truthcert" / ".env",
        ]

        for path in search_paths:
            if path and path.exists():
                load_dotenv(path)
                print(f"Loaded API keys from: {path}")
                break

    keys = {}

    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        keys["anthropic"] = os.getenv("ANTHROPIC_API_KEY")
        print("[OK] ANTHROPIC_API_KEY found")
    else:
        print("[--] ANTHROPIC_API_KEY not found")

    # Z.AI
    if os.getenv("ZAI_API_KEY"):
        keys["zai"] = os.getenv("ZAI_API_KEY")
        keys["zai_base_url"] = os.getenv("ZAI_BASE_URL", "https://api.z.ai/v1")
        print("[OK] ZAI_API_KEY found")
    else:
        print("[--] ZAI_API_KEY not found")

    # OpenAI (optional)
    if os.getenv("OPENAI_API_KEY"):
        keys["openai"] = os.getenv("OPENAI_API_KEY")
        print("[OK] OPENAI_API_KEY found")

    return keys


class BaseWitness(ABC):
    """Base class for LLM witnesses."""

    EXTRACTION_PROMPT = """You are a precise data extraction assistant for meta-analysis verification.

Given the following document content and extraction scope, extract the requested values.

SCOPE:
- Endpoint: {endpoint}
- Entities: {entities}
- Units: {units}
- Timepoint: {timepoint}

DOCUMENT:
{content}

INSTRUCTIONS:
1. Extract numerical values exactly as they appear in the document
2. For each value, provide a confidence score (0.0-1.0)
3. If a value is not found, set it to null
4. Do not infer or calculate values not explicitly stated

Return a JSON object with this structure:
{{
    "extractions": {{
        "effect_estimate": <number or null>,
        "standard_error": <number or null>,
        "ci_lower": <number or null>,
        "ci_upper": <number or null>,
        "p_value": <number or null>,
        "sample_size": <number or null>,
        "k": <number or null>,
        "tau": <number or null>,
        "tau_squared": <number or null>,
        "i_squared": <number or null>
    }},
    "confidence": {{
        "effect_estimate": <0.0-1.0>,
        "standard_error": <0.0-1.0>,
        ...
    }},
    "notes": "<any relevant observations>"
}}

Return ONLY the JSON, no other text."""

    def __init__(self, model_name: str, model_family: str):
        self.model_name = model_name
        self.model_family = model_family
        self._witness_counter = 0

    @abstractmethod
    def extract(
        self,
        content: str,
        scope: Dict[str, Any],
    ) -> WitnessExtraction:
        """Extract values from content using the LLM."""
        pass

    def _build_prompt(self, content: str, scope: Dict[str, Any]) -> str:
        """Build the extraction prompt."""
        return self.EXTRACTION_PROMPT.format(
            endpoint=scope.get("endpoint", ""),
            entities=", ".join(scope.get("entities", [])),
            units=scope.get("units", ""),
            timepoint=scope.get("timepoint", ""),
            content=content[:10000],  # Limit content length
        )

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse JSON response from LLM."""
        try:
            # Try to find JSON in the response
            text = response_text.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text)
        except json.JSONDecodeError:
            return {
                "extractions": {},
                "confidence": {},
                "notes": f"Failed to parse response: {response_text[:200]}",
            }

    def _generate_witness_id(self) -> str:
        """Generate unique witness ID."""
        self._witness_counter += 1
        return f"{self.model_family}_{self.model_name}_{self._witness_counter:04d}"


class ClaudeWitness(BaseWitness):
    """Witness using Anthropic's Claude API."""

    # Cost per 1M tokens (as of 2024)
    COST_PER_1M_INPUT = 3.00   # Claude 3.5 Sonnet
    COST_PER_1M_OUTPUT = 15.00

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-sonnet-4-20250514",
    ):
        super().__init__(model_name, "anthropic")

        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)

    def extract(
        self,
        content: str,
        scope: Dict[str, Any],
    ) -> WitnessExtraction:
        """Extract values using Claude."""
        witness_id = self._generate_witness_id()
        prompt = self._build_prompt(content, scope)

        try:
            start_time = time.time()

            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            elapsed = time.time() - start_time

            # Parse response
            response_text = response.content[0].text
            parsed = self._parse_response(response_text)

            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens

            cost = (
                (input_tokens / 1_000_000) * self.COST_PER_1M_INPUT +
                (output_tokens / 1_000_000) * self.COST_PER_1M_OUTPUT
            )

            return WitnessExtraction(
                witness_id=witness_id,
                model_name=self.model_name,
                model_family=self.model_family,
                extractions=parsed.get("extractions", {}),
                confidence_scores=parsed.get("confidence", {}),
                tokens_used=total_tokens,
                cost_usd=cost,
                raw_response=response_text,
            )

        except Exception as e:
            return WitnessExtraction(
                witness_id=witness_id,
                model_name=self.model_name,
                model_family=self.model_family,
                extractions={},
                confidence_scores={},
                tokens_used=0,
                cost_usd=0,
                error=str(e),
            )


class ZAIWitness(BaseWitness):
    """Witness using Z.AI API (OpenAI-compatible)."""

    # Default cost estimates (adjust based on actual Z.AI pricing)
    COST_PER_1M_INPUT = 1.00
    COST_PER_1M_OUTPUT = 2.00

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.z.ai/v1",
        model_name: str = "default",  # Adjust to actual Z.AI model name
    ):
        super().__init__(model_name, "zai")

        if not HAS_OPENAI:
            raise ImportError("openai package not installed. Run: pip install openai")

        self.client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    def extract(
        self,
        content: str,
        scope: Dict[str, Any],
    ) -> WitnessExtraction:
        """Extract values using Z.AI."""
        witness_id = self._generate_witness_id()
        prompt = self._build_prompt(content, scope)

        try:
            start_time = time.time()

            response = self.client.chat.completions.create(
                model=self.model_name,
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            elapsed = time.time() - start_time

            # Parse response
            response_text = response.choices[0].message.content
            parsed = self._parse_response(response_text)

            # Calculate cost
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            total_tokens = input_tokens + output_tokens

            cost = (
                (input_tokens / 1_000_000) * self.COST_PER_1M_INPUT +
                (output_tokens / 1_000_000) * self.COST_PER_1M_OUTPUT
            )

            return WitnessExtraction(
                witness_id=witness_id,
                model_name=self.model_name,
                model_family=self.model_family,
                extractions=parsed.get("extractions", {}),
                confidence_scores=parsed.get("confidence", {}),
                tokens_used=total_tokens,
                cost_usd=cost,
                raw_response=response_text,
            )

        except Exception as e:
            return WitnessExtraction(
                witness_id=witness_id,
                model_name=self.model_name,
                model_family=self.model_family,
                extractions={},
                confidence_scores={},
                tokens_used=0,
                cost_usd=0,
                error=str(e),
            )


def create_witnesses(
    api_keys: Optional[Dict[str, str]] = None,
    claude_model: str = "claude-sonnet-4-20250514",
    zai_model: str = "default",
) -> List[BaseWitness]:
    """
    Create witness instances from available API keys.

    Args:
        api_keys: Dict of API keys. If None, loads from .env
        claude_model: Claude model to use
        zai_model: Z.AI model to use

    Returns:
        List of configured witness instances
    """
    if api_keys is None:
        api_keys = load_api_keys()

    witnesses = []

    # Create Claude witness
    if "anthropic" in api_keys and HAS_ANTHROPIC:
        try:
            witness = ClaudeWitness(
                api_key=api_keys["anthropic"],
                model_name=claude_model,
            )
            witnesses.append(witness)
            print(f"[OK] Created Claude witness ({claude_model})")
        except Exception as e:
            print(f"[ERROR] Failed to create Claude witness: {e}")

    # Create Z.AI witness
    if "zai" in api_keys and HAS_OPENAI:
        try:
            witness = ZAIWitness(
                api_key=api_keys["zai"],
                base_url=api_keys.get("zai_base_url", "https://api.z.ai/v1"),
                model_name=zai_model,
            )
            witnesses.append(witness)
            print(f"[OK] Created Z.AI witness ({zai_model})")
        except Exception as e:
            print(f"[ERROR] Failed to create Z.AI witness: {e}")

    if not witnesses:
        print("\nNo witnesses created. Check your API keys in .env file.")
        print("Required packages: pip install python-dotenv anthropic openai")

    return witnesses


def test_witnesses():
    """Test witness extraction with a simple example."""
    print("=" * 60)
    print("TruthCert Witness Test")
    print("=" * 60)

    # Load keys
    api_keys = load_api_keys()

    if not api_keys:
        print("\nNo API keys found. Please edit .env file:")
        print(f"  {Path(__file__).parent.parent / '.env'}")
        return

    # Create witnesses
    witnesses = create_witnesses(api_keys)

    if not witnesses:
        return

    # Test content
    test_content = """
    Meta-Analysis Results

    Overall Survival Analysis

    The pooled hazard ratio was 0.85 (95% CI: 0.72 to 0.99).
    Standard error: 0.036
    p-value: 0.038

    Heterogeneity:
    Number of studies: k = 13
    τ = 0.025
    τ² = 0.000625
    I² = 25.3%

    Sample size: n = 1,500 patients
    """

    test_scope = {
        "endpoint": "overall survival",
        "entities": ["treatment", "control"],
        "units": "months",
        "timepoint": "12 months",
    }

    print("\nTest content:")
    print("-" * 40)
    print(test_content[:500])
    print("-" * 40)

    print("\nRunning extractions...")
    for witness in witnesses:
        print(f"\n{witness.model_family}/{witness.model_name}:")
        result = witness.extract(test_content, test_scope)

        if result.error:
            print(f"  Error: {result.error}")
        else:
            print(f"  Tokens: {result.tokens_used}")
            print(f"  Cost: ${result.cost_usd:.4f}")
            print(f"  Extractions:")
            for key, value in result.extractions.items():
                conf = result.confidence_scores.get(key, 0)
                print(f"    {key}: {value} (conf: {conf:.2f})")


if __name__ == "__main__":
    test_witnesses()
