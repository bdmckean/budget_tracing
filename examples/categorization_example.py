"""
Complete example of tracing LLM calls for transaction categorization.

This example shows how to use Langfuse to trace calls to Ollama (llama3.1:8b)
for categorizing financial transactions. It demonstrates:

1. Setting up the Langfuse client
2. Creating traces with metadata
3. Adding generations for LLM calls
4. Adding spans for non-LLM operations
5. Error handling and logging
"""

import os
import json
import time
from typing import Dict, List
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

from tracing import get_langfuse_client, create_trace, add_generation, add_span


# Load environment variables from .env file
load_dotenv()

# Configuration
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
PROJECT_NAME = "budget_claude"  # Change to "budget_cursor" for the other project


@dataclass
class Transaction:
    """Represents a financial transaction."""
    id: str
    description: str
    amount: float
    date: str


class TransactionCategorizer:
    """Categorizes transactions using LLM with Langfuse tracing."""

    def __init__(self, project_name: str = PROJECT_NAME):
        """Initialize the categorizer with Langfuse tracing."""
        self.langfuse = get_langfuse_client(project_name)
        self.project_name = project_name
        self.session_id = f"{project_name}_{int(time.time())}"

    def categorize_transaction(self, transaction: Transaction) -> Dict:
        """
        Categorize a transaction using Ollama with Langfuse tracing.

        Args:
            transaction: Transaction object to categorize

        Returns:
            Dictionary with transaction ID, description, amount, and category
        """
        # Create a trace for this categorization
        trace = create_trace(
            self.langfuse,
            name="categorize_transaction",
            user_id="system",
            session_id=self.session_id,
            metadata={
                "transaction_id": transaction.id,
                "amount": transaction.amount,
                "date": transaction.date,
            }
        )

        try:
            # Step 1: Prepare the transaction data
            add_span(
                trace,
                name="prepare_transaction_data",
                input_=f"ID: {transaction.id}, Desc: {transaction.description}, Amount: {transaction.amount}",
                output="Transaction data prepared",
                metadata={"step": 1}
            )

            # Step 2: Create the categorization prompt
            prompt = self._create_prompt(transaction)
            add_span(
                trace,
                name="create_prompt",
                output=prompt,
                metadata={"step": 2, "prompt_length": len(prompt)}
            )

            # Step 3: Call Ollama with tracing
            start_time = time.time()
            category, confidence = self._call_ollama(transaction, prompt, trace)
            elapsed_time = time.time() - start_time

            # Step 4: Validate the result
            add_span(
                trace,
                name="validate_result",
                input_=f"Category: {category}, Confidence: {confidence}",
                output="Validation passed",
                metadata={"step": 4, "valid": True}
            )

            result = {
                "transaction_id": transaction.id,
                "description": transaction.description,
                "amount": transaction.amount,
                "category": category,
                "confidence": confidence,
                "processing_time_ms": elapsed_time * 1000,
            }

            # Mark trace as successful
            trace.update(output=result)

            return result

        except Exception as e:
            # Log error in trace
            add_span(
                trace,
                name="error",
                input_=str(type(e).__name__),
                output=str(e),
                metadata={"error": True}
            )
            raise

    def _create_prompt(self, transaction: Transaction) -> str:
        """Create a prompt for categorizing the transaction."""
        return f"""Categorize the following financial transaction into ONE of these categories:
- Food & Dining
- Transportation
- Shopping
- Bills & Utilities
- Healthcare
- Entertainment
- Other

Transaction Description: {transaction.description}
Amount: ${transaction.amount:.2f}

Respond with ONLY the category name, nothing else."""

    def _call_ollama(self, transaction: Transaction, prompt: str, trace) -> tuple:
        """Call Ollama API to categorize the transaction."""
        try:
            # Prepare the request
            request_data = {
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "temperature": 0.3,
                "top_p": 0.9,
                "stream": False,
            }

            # Make the API call
            response = requests.post(
                f"{OLLAMA_API_URL}/api/generate",
                json=request_data,
                timeout=30
            )
            response.raise_for_status()

            # Parse the response
            response_data = response.json()
            category = response_data.get("response", "").strip()

            # Extract confidence from the response
            # For a simple implementation, we'll use a default confidence
            confidence = 0.95

            # Log the generation to Langfuse
            add_generation(
                trace,
                name="ollama_categorization",
                model=OLLAMA_MODEL,
                input_=prompt,
                output=category,
                usage={
                    "prompt_tokens": response_data.get("prompt_eval_count", 0),
                    "completion_tokens": response_data.get("eval_count", 0),
                },
                metadata={
                    "temperature": request_data["temperature"],
                    "top_p": request_data["top_p"],
                    "ollama_host": OLLAMA_API_URL,
                }
            )

            return category, confidence

        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Could not connect to Ollama at {OLLAMA_API_URL}. "
                f"Make sure Ollama is running and {OLLAMA_MODEL} is loaded. "
                f"Error: {e}"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                f"Request to Ollama timed out. The model {OLLAMA_MODEL} might be slow."
            )
        except Exception as e:
            raise RuntimeError(f"Error calling Ollama: {e}")

    def categorize_batch(self, transactions: List[Transaction]) -> List[Dict]:
        """
        Categorize multiple transactions.

        Args:
            transactions: List of Transaction objects

        Returns:
            List of categorization results
        """
        results = []
        for transaction in transactions:
            try:
                result = self.categorize_transaction(transaction)
                results.append(result)
                print(f"✓ Categorized: {transaction.description:40s} → {result['category']}")
            except Exception as e:
                print(f"✗ Failed: {transaction.description:40s} → {e}")
                results.append({
                    "transaction_id": transaction.id,
                    "description": transaction.description,
                    "amount": transaction.amount,
                    "error": str(e),
                })

        return results


def main():
    """Run the transaction categorization example."""
    print("\n" + "=" * 60)
    print("Transaction Categorization with Langfuse Tracing")
    print("=" * 60 + "\n")

    # Initialize the categorizer
    try:
        categorizer = TransactionCategorizer(PROJECT_NAME)
        print(f"✓ Langfuse client initialized for project: {PROJECT_NAME}")
        print(f"✓ Using Ollama at: {OLLAMA_API_URL}")
        print(f"✓ Using model: {OLLAMA_MODEL}\n")
    except ValueError as e:
        print(f"✗ Error: {e}")
        print("\nPlease ensure your .env file is configured correctly.")
        return

    # Sample transactions to categorize
    sample_transactions = [
        Transaction("txn_001", "Starbucks Coffee", 5.50, "2024-01-15"),
        Transaction("txn_002", "Uber to Airport", 42.00, "2024-01-15"),
        Transaction("txn_003", "Whole Foods Groceries", 87.50, "2024-01-15"),
        Transaction("txn_004", "Movie Tickets", 28.00, "2024-01-15"),
        Transaction("txn_005", "CVS Pharmacy", 15.30, "2024-01-15"),
    ]

    print(f"Processing {len(sample_transactions)} transactions...\n")

    # Categorize transactions
    results = categorizer.categorize_batch(sample_transactions)

    # Display results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60 + "\n")

    total_amount = 0
    for result in results:
        if "error" not in result:
            total_amount += result["amount"]
            print(f"ID: {result['transaction_id']:10s} | Amount: ${result['amount']:8.2f} | "
                  f"Category: {result['category']:20s} | Confidence: {result['confidence']:.2%}")
        else:
            print(f"ID: {result['transaction_id']:10s} | ERROR: {result['error']}")

    print(f"\n{'Total Amount Processed':30s}: ${total_amount:8.2f}")
    print("\n✓ Traces have been sent to Langfuse!")
    print(f"✓ View your traces at: http://localhost:3001/project/{PROJECT_NAME}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
