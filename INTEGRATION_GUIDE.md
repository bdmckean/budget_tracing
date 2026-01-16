# Integration Guide - Connecting Budget Projects to Langfuse

This guide explains how to integrate `budget_claude` and `budget_cursor` projects with the shared Langfuse tracing instance.

## Quick Overview

Both sibling projects can connect to the centralized Langfuse server and send traces. Each project has its own set of API keys, allowing traces to be separated and organized by project in the Langfuse dashboard.

## Prerequisites

1. Langfuse server running (see README.md for setup instructions)
2. API keys generated for your project in Langfuse UI (see README.md section 3)
3. Python 3.10+ environment in your project
4. `langfuse` package installed

## Setup Steps

### 1. Install Langfuse in Your Project

In your sibling project (`budget_claude` or `budget_cursor`), add langfuse to your dependencies:

**Using uv:**
```bash
uv add langfuse
```

**Using pip:**
```bash
pip install langfuse>=2.0.0
```

### 2. Create or Update Your .env File

Add the Langfuse API keys for your project:

```bash
# For budget_claude
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3001

# For budget_cursor
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
LANGFUSE_HOST=http://localhost:3001
```

### 3. Import and Initialize Langfuse in Your Code

#### Basic Setup

```python
import os
from langfuse import Langfuse

# Initialize the Langfuse client
langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3001")
)
```

#### Using the Provided Helper Module

If you want to use the helper module from `budget_tracing/examples/tracing.py`:

1. Copy `examples/tracing.py` to your project or reference it from budget_tracing
2. Use the helper functions:

```python
import sys
sys.path.insert(0, "/path/to/budget_tracing/examples")

from tracing import get_langfuse_client, create_trace, add_generation, add_span

# Initialize
langfuse = get_langfuse_client("budget_claude")  # or "budget_cursor"

# Create a trace
trace = create_trace(
    langfuse,
    name="process_transaction",
    user_id="user_123",
    metadata={"transaction_id": "txn_456"}
)

# Add observations
add_span(trace, name="data_validation", output="Valid")
add_generation(trace, name="llm_call", model="llama3.1:8b", input_="...", output="...")
```

## Tracing Your LLM Calls

### Example 1: Simple LLM Call

```python
from langfuse import Langfuse
import os
import requests

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host="http://localhost:3001"
)

# Create a trace for your operation
trace = langfuse.trace(
    name="categorize_transaction",
    metadata={"amount": 50.00, "merchant": "Starbucks"}
)

# Call your LLM
prompt = "Categorize this transaction: Coffee - $5.00"
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.1:8b", "prompt": prompt, "stream": False}
)
result = response.json()

# Log the generation
trace.generation(
    name="ollama_request",
    model="llama3.1:8b",
    input=prompt,
    output=result["response"],
    usage={
        "prompt_tokens": result.get("prompt_eval_count", 0),
        "completion_tokens": result.get("eval_count", 0)
    }
)

print(f"Category: {result['response']}")
```

### Example 2: Multi-Step Trace

```python
from langfuse import Langfuse

langfuse = Langfuse(...)

# Start a trace for a complex operation
trace = langfuse.trace(
    name="transaction_processing_pipeline",
    user_id="user_123",
    session_id="session_xyz"
)

# Step 1: Data validation
trace.span(
    name="validate_input",
    input="transaction data",
    output="validation passed"
)

# Step 2: LLM categorization
trace.generation(
    name="categorize",
    model="llama3.1:8b",
    input="Categorize: ...",
    output="Food & Dining"
)

# Step 3: Database operation
trace.span(
    name="store_result",
    input="INSERT INTO transactions ...",
    output="Row 12345 created"
)
```

### Example 3: Using Traces with Ollama

```python
from langfuse import Langfuse
import requests
import time

def call_ollama_with_tracing(langfuse, transaction_desc, trace_name):
    """Call Ollama and trace the interaction."""

    trace = langfuse.trace(name=trace_name)

    # Prepare request
    request_data = {
        "model": "llama3.1:8b",
        "prompt": f"Categorize: {transaction_desc}",
        "temperature": 0.3,
        "stream": False
    }

    start_time = time.time()

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=request_data,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        elapsed = time.time() - start_time

        # Log successful generation
        trace.generation(
            name="ollama_call",
            model="llama3.1:8b",
            input=request_data["prompt"],
            output=response_data["response"],
            usage={
                "prompt_tokens": response_data.get("prompt_eval_count", 0),
                "completion_tokens": response_data.get("eval_count", 0)
            },
            metadata={
                "duration_seconds": elapsed,
                "temperature": request_data["temperature"]
            }
        )

        return response_data["response"]

    except Exception as e:
        # Log error
        trace.span(
            name="error",
            input=str(type(e)),
            output=str(e),
            metadata={"error": True}
        )
        raise
```

## Connecting to Ollama from Different Environments

### From Host Machine
```python
OLLAMA_URL = "http://localhost:11434"
```

### From Docker Container
If your Langfuse instance or another Docker service needs to call Ollama:
```python
OLLAMA_URL = "http://host.docker.internal:11434"  # macOS and Windows Docker
OLLAMA_URL = "http://172.17.0.1:11434"  # Linux Docker
```

### From Sibling Projects
Since `budget_claude` and `budget_cursor` run on the host machine:
```python
OLLAMA_URL = "http://localhost:11434"
```

## Best Practices for Tracing

### 1. Use Meaningful Trace Names

```python
# Good
trace = langfuse.trace(name="transaction_categorization")
trace = langfuse.trace(name="user_onboarding_flow")

# Less helpful
trace = langfuse.trace(name="process")
trace = langfuse.trace(name="step1")
```

### 2. Add Metadata for Context

```python
trace = langfuse.trace(
    name="transaction_processing",
    metadata={
        "transaction_id": "txn_123",
        "amount": 50.00,
        "currency": "USD",
        "merchant_category": "restaurant"
    }
)
```

### 3. Use User IDs to Track Users

```python
trace = langfuse.trace(
    name="budget_analysis",
    user_id="user_456"  # Track behavior by user
)
```

### 4. Group Related Traces with Session IDs

```python
session_id = "session_20240115_abc123"

# Multiple related operations
trace1 = langfuse.trace(name="import_transactions", session_id=session_id)
trace2 = langfuse.trace(name="categorize_transactions", session_id=session_id)
trace3 = langfuse.trace(name="generate_report", session_id=session_id)

# All grouped together in dashboard
```

### 5. Log Token Usage

```python
trace.generation(
    name="llm_call",
    model="llama3.1:8b",
    input=prompt,
    output=response,
    usage={
        "prompt_tokens": 150,
        "completion_tokens": 25,
        "total_tokens": 175
    }
)
```

### 6. Add Metadata to Generations

```python
trace.generation(
    name="categorize",
    model="llama3.1:8b",
    input=prompt,
    output=category,
    metadata={
        "temperature": 0.3,
        "top_p": 0.9,
        "max_tokens": 50,
        "latency_ms": 250
    }
)
```

## Viewing Your Traces

### In Langfuse Dashboard

1. Open http://localhost:3001
2. Select your project (budget_claude or budget_cursor)
3. Click "Traces" in the sidebar
4. Filter by:
   - **Trace name**: `categorize_transaction`
   - **User**: `user_123`
   - **Session**: `session_abc`
   - **Date range**: Custom range

### Trace Details

Each trace shows:
- **Timeline**: Chronological view of all operations
- **Tokens**: Prompt and completion tokens for each generation
- **Metadata**: Custom metadata attached to trace
- **User**: User ID if provided
- **Session**: Session ID if provided
- **Duration**: How long the trace took

### Comparing Traces

Use the dashboard to:
- Compare performance across different categorization strategies
- Track token usage over time
- Identify slow operations
- Monitor error rates

## Troubleshooting

### Traces Not Appearing in Dashboard

**Check 1:** Verify API keys
```python
import os
print(os.getenv("LANGFUSE_PUBLIC_KEY"))
print(os.getenv("LANGFUSE_SECRET_KEY"))
```

**Check 2:** Verify Langfuse is running
```bash
curl http://localhost:3001/api/health
```

**Check 3:** Verify project name
- API keys must be for the project you're viewing
- `budget_claude` keys won't appear in `budget_cursor` project

**Check 4:** Check for errors
```python
from langfuse import Langfuse

langfuse = Langfuse(debug=True)  # Enable debug mode
```

### Connection Refused Error

```
Error: Could not connect to Langfuse at http://localhost:3001
```

**Solution:**
```bash
# Make sure Langfuse is running
docker-compose ps

# Start if not running
docker-compose up -d

# Check logs
docker-compose logs langfuse
```

### API Keys Not Found

```
ValueError: Missing Langfuse API keys
```

**Solution:**
1. Create a `.env` file in your project
2. Add your API keys from Langfuse UI
3. Load with `python-dotenv`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Host.Docker.Internal Not Working

If using Ollama in Docker:
```python
import os
import platform

if platform.system() == "Darwin":  # macOS
    OLLAMA_URL = "http://host.docker.internal:11434"
elif platform.system() == "Linux":
    OLLAMA_URL = "http://172.17.0.1:11434"
else:  # Windows
    OLLAMA_URL = "http://host.docker.internal:11434"
```

## Environment Variables Summary

In your sibling projects, set these in `.env`:

```bash
# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3001

# Ollama Configuration
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

## Next Steps

1. Copy the example files from `budget_tracing/examples/` to your project
2. Update your `.env` file with API keys
3. Instrument your LLM calls with Langfuse tracing
4. Monitor your traces in the Langfuse dashboard
5. Use insights to optimize performance and costs

## Support

For detailed Langfuse documentation: https://docs.langfuse.com/
For Ollama documentation: https://ollama.ai/

## Example Integration in budget_claude

Here's a minimal example for `budget_claude`:

```python
# budget_claude/tracing.py
import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "http://localhost:3001")
)

def trace_transaction_categorization(transaction):
    """Trace the categorization of a transaction."""
    trace = langfuse.trace(
        name="categorize_transaction",
        metadata={"transaction_id": transaction["id"]}
    )
    # ... categorization logic ...
    return result
```

Then in your main code:
```python
from tracing import langfuse, trace_transaction_categorization

result = trace_transaction_categorization({"id": "txn_123", "desc": "Coffee"})
```

That's it! Your traces will now appear in http://localhost:3001
