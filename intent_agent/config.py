"""
config.py - Intent Agent configuration
"""

import logging
import os
from typing import Optional, Sequence

from dotenv import find_dotenv, load_dotenv
from langchain_core.runnables import RunnableLambda

# Load environment variables for direct module imports such as
# `uvicorn app.main:app`, where `run.py` is bypassed.
load_dotenv(find_dotenv(), override=False)

# Model Configuration
MODEL_NAME = "gemini-2.5-flash-lite"
MODEL_CANDIDATES = [
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-2.0-flash-lite",
]
TEMPERATURE = 0
MODEL_RETRIES = 0

# System Configuration
FALLBACK_SYSTEM = "ibm"

# Entity Configuration
ENTITY_PRIORITY_ORDER = ["shopping", "transaction", "account", "customer"]

# Task Thresholds
HIGH_PRIORITY_TASKS = ["compare", "analyze"]
MEDIUM_PRIORITY_TASKS = ["fetch", "reconcile", "transform"]
LOW_PRIORITY_TASKS = []

# Confidence Thresholds
MIN_CONFIDENCE_SCORE = 0.3


def build_llm_model(
    logger: Optional[logging.Logger] = None,
    model_candidates: Optional[Sequence[str]] = None,
):
    """
    Build a Gemini model with ordered runtime fallback across candidate models.
    Returns None if no candidate can be initialized.
    """
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
    except Exception as exc:
        if logger:
            logger.warning(f"Gemini client import failed: {exc}")
        return None

    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
        if logger:
            logger.warning(
                "Gemini API key not found in environment. "
                "Set GOOGLE_API_KEY or GEMINI_API_KEY."
            )
        return None

    candidates = list(model_candidates or MODEL_CANDIDATES)
    if not candidates:
        return None

    initialized_models = []
    for model_name in candidates:
        try:
            initialized_models.append(
                (
                    model_name,
                    ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=TEMPERATURE,
                        retries=MODEL_RETRIES,
                    ),
                )
            )
        except Exception as exc:
            if logger:
                logger.warning(f"Gemini model init failed for {model_name}: {exc}")

    if not initialized_models:
        return None

    def _invoke_with_fallback(input_value):
        last_error = None
        for model_name, model in initialized_models:
            try:
                if logger:
                    logger.info(f"Using Gemini model {model_name}")
                return model.invoke(input_value)
            except Exception as exc:
                last_error = exc
                if logger:
                    logger.warning(f"Gemini invoke failed for {model_name}: {exc}")
                continue
        if last_error:
            raise last_error
        raise RuntimeError("No Gemini models available")

    runnable = RunnableLambda(_invoke_with_fallback)
    setattr(runnable, "model_name", initialized_models[0][0])
    setattr(runnable, "model_candidates", [name for name, _ in initialized_models])
    return runnable
