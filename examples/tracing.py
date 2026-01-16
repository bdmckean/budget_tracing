"""
Langfuse client setup utilities for budget project tracing.

This module provides helper functions to initialize and configure
the Langfuse client for different projects.
"""

import os
from typing import Optional
from langfuse import Langfuse


def get_langfuse_client(project_name: str, langfuse_host: str = "http://localhost:3001") -> Langfuse:
    """
    Initialize a Langfuse client with project-specific API keys.

    Args:
        project_name: Name of the project ("budget_claude" or "budget_cursor")
        langfuse_host: Langfuse server URL (default: localhost for development)

    Returns:
        Initialized Langfuse client

    Raises:
        ValueError: If API keys are not found for the project

    Example:
        >>> from tracing import get_langfuse_client
        >>> langfuse = get_langfuse_client("budget_claude")
        >>> trace = langfuse.trace(name="categorize_transaction")
    """
    # Construct environment variable names
    public_key_var = f"{project_name.upper()}_PUBLIC_KEY"
    secret_key_var = f"{project_name.upper()}_SECRET_KEY"

    # Get API keys from environment
    public_key = os.getenv(public_key_var)
    secret_key = os.getenv(secret_key_var)

    if not public_key or not secret_key:
        raise ValueError(
            f"Missing Langfuse API keys for project '{project_name}'. "
            f"Please set {public_key_var} and {secret_key_var} in your .env file."
        )

    # Initialize and return Langfuse client
    return Langfuse(
        public_key=public_key,
        secret_key=secret_key,
        host=langfuse_host,
    )


def create_trace(
    langfuse: Langfuse,
    name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> object:
    """
    Create a new trace with optional metadata and user information.

    Args:
        langfuse: Langfuse client instance
        name: Name of the trace (e.g., "categorize_transaction")
        user_id: Optional user ID for tracking
        session_id: Optional session ID for grouping related traces
        metadata: Optional dictionary of metadata to attach

    Returns:
        Trace object for adding observations

    Example:
        >>> trace = create_trace(
        ...     langfuse,
        ...     name="categorize_transaction",
        ...     user_id="user_123",
        ...     metadata={"category": "expense", "amount": 50.00}
        ... )
    """
    return langfuse.trace(
        name=name,
        user_id=user_id,
        session_id=session_id,
        metadata=metadata or {},
    )


def add_generation(
    trace: object,
    name: str,
    model: str,
    input_: str,
    output: str,
    usage: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Add a generation observation to a trace (for LLM calls).

    Args:
        trace: Trace object to add observation to
        name: Name of the generation (e.g., "llm_categorization")
        model: Model name (e.g., "llama3.1:8b")
        input_: Input/prompt sent to the model
        output: Output/completion from the model
        usage: Optional dict with "prompt_tokens" and "completion_tokens"
        metadata: Optional dict with additional metadata

    Example:
        >>> add_generation(
        ...     trace,
        ...     name="llm_categorization",
        ...     model="llama3.1:8b",
        ...     input_="Categorize this transaction: Coffee - $5.00",
        ...     output="Food & Beverage",
        ...     usage={"prompt_tokens": 25, "completion_tokens": 3},
        ...     metadata={"temperature": 0.7, "max_tokens": 50}
        ... )
    """
    trace.generation(
        name=name,
        model=model,
        input=input_,
        output=output,
        usage=usage or {},
        metadata=metadata or {},
    )


def add_span(
    trace: object,
    name: str,
    input_: Optional[str] = None,
    output: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> None:
    """
    Add a span observation to a trace (for non-LLM operations).

    Args:
        trace: Trace object to add observation to
        name: Name of the span (e.g., "database_lookup")
        input_: Optional input data
        output: Optional output data
        metadata: Optional dict with additional metadata

    Example:
        >>> add_span(
        ...     trace,
        ...     name="database_lookup",
        ...     input_="SELECT * FROM transactions WHERE id=123",
        ...     output_="Transaction found",
        ...     metadata={"db": "postgres", "query_time_ms": 15}
        ... )
    """
    trace.span(
        name=name,
        input=input_ or "",
        output=output or "",
        metadata=metadata or {},
    )


if __name__ == "__main__":
    # Quick test
    try:
        client = get_langfuse_client("budget_claude")
        print("✓ Successfully initialized Langfuse client")
    except ValueError as e:
        print(f"✗ Error: {e}")
