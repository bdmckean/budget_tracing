# Budget Tracing - Shared Langfuse Server

A centralized Langfuse instance for distributed tracing and monitoring of LLM calls across `budget_claude` and `budget_cursor` sibling projects.

## Overview

This repository contains a Docker-based setup for running a shared Langfuse server that both budget projects can connect to. This allows you to:

- Track and trace LLM API calls from both projects in a single dashboard
- Monitor performance metrics and costs across sibling projects
- Store project-specific API keys for separation of traces
- Debug and analyze LLM interactions across your budget application suite

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- macOS M2 with 24GB RAM (or similar specs)
- Ollama running on the host machine with llama3.1:8b model

### 1. Initial Setup

Clone this repository and prepare your environment:

```bash
# Navigate to the budget_tracing directory
cd /path/to/budget_tracing

# Copy the example environment file and edit with your own secrets
cp .env.example .env

# Edit .env and replace the NEXTAUTH_SECRET and SALT values if desired
# (or use the pre-generated ones in .env.example)
```

### 2. Start Langfuse

```bash
# Start the Langfuse server and PostgreSQL database
docker-compose up -d

# Check the status of the containers
docker-compose ps

# View logs (useful for debugging)
docker-compose logs -f langfuse
```

The Langfuse server will be available at: **http://localhost:3001**

Wait for the application to fully initialize (should see "ready" in logs). This typically takes 30-60 seconds.

### 3. Create Projects and Generate API Keys

#### First Time Setup in Langfuse UI:

1. **Open http://localhost:3001** in your browser
2. **Sign up** with the default admin credentials (this creates the initial admin account):
   - **Email**: `admin@budget.local`
   - **Password**: `admin123`
   
   > **Note**: You can use any email/password you prefer. The first user account created becomes the admin account. Change the password after first login for security.
3. **Create first project** for `budget_claude`:
   - Click "New Project"
   - Name: `budget_claude`
   - Click "Create"
4. **Generate API keys** for budget_claude:
   - Click the project settings (gear icon)
   - Navigate to "API Keys"
   - Create new API key
   - Copy the **Public Key** (starts with `pk-lf-`)
   - Copy the **Secret Key** (starts with `sk-lf-`)
   - Add to your `.env` file:
     ```
     BUDGET_CLAUDE_PUBLIC_KEY=pk-lf-...
     BUDGET_CLAUDE_SECRET_KEY=sk-lf-...
     ```

5. **Create second project** for `budget_cursor`:
   - Click "New Project"
   - Name: `budget_cursor`
   - Click "Create"
6. **Generate API keys** for budget_cursor:
   - Click the project settings (gear icon)
   - Navigate to "API Keys"
   - Create new API key
   - Copy the **Public Key** and **Secret Key**
   - Add to your `.env` file:
     ```
     BUDGET_CURSOR_PUBLIC_KEY=pk-lf-...
     BUDGET_CURSOR_SECRET_KEY=sk-lf-...
     ```

### 4. Stop Langfuse

```bash
# Stop the containers (data persists in volumes)
docker-compose down

# Stop and remove volumes (deletes all data)
docker-compose down -v
```

## Default Credentials

When setting up Langfuse for the first time, use these default admin credentials:

- **Email**: `admin@budget.local`
- **Password**: `admin123`

> **Security Note**: These are default credentials for local development. Change the password immediately after first login, especially if deploying to a shared environment or exposing the service to a network.

## Environment Configuration

The `.env` file contains all necessary configuration for running Langfuse. Key variables:

- **NEXTAUTH_SECRET**: Authentication secret for Langfuse UI (generated with `openssl rand -base64 32`)
- **SALT**: Password hashing salt (generated with `openssl rand -base64 32`)
- **BUDGET_CLAUDE_PUBLIC_KEY/SECRET_KEY**: API keys for the budget_claude project
- **BUDGET_CURSOR_PUBLIC_KEY/SECRET_KEY**: API keys for the budget_cursor project

## File Structure

```
budget_tracing/
├── docker-compose.yml          # Docker composition for Langfuse + PostgreSQL
├── .env.example                # Example environment variables (copy to .env)
├── README.md                   # This file
├── INTEGRATION_GUIDE.md         # Detailed integration guide for sibling projects
├── examples/
│   ├── requirements.txt        # Python dependencies for examples
│   ├── tracing.py             # Langfuse client setup utilities
│   └── categorization_example.py  # Complete example with Ollama integration
└── scripts/
    ├── start.sh               # Helper script to start Langfuse
    ├── stop.sh                # Helper script to stop Langfuse
    ├── logs.sh                # View Langfuse logs
    └── reset.sh               # Reset database (dangerous!)
```

## Useful Commands

### View Logs

```bash
# Follow Langfuse logs in real-time
docker-compose logs -f langfuse

# Follow PostgreSQL logs
docker-compose logs -f postgres

# View last 100 lines
docker-compose logs --tail=100
```

### Database Management

```bash
# Check database status
docker-compose exec postgres pg_isready

# Access PostgreSQL shell (if needed for advanced debugging)
docker-compose exec postgres psql -U langfuse -d langfuse
```

### Restart Services

```bash
# Restart Langfuse server (useful if you make config changes)
docker-compose restart langfuse

# Restart PostgreSQL
docker-compose restart postgres

# Restart everything
docker-compose restart
```

### Reset Data

```bash
# ⚠️  WARNING: This deletes all data!
# Stop containers and remove volumes
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Integrating with Sibling Projects

For detailed instructions on how to connect `budget_claude` and `budget_cursor` to this Langfuse instance, see **INTEGRATION_GUIDE.md**.

Quick summary:
1. Install `langfuse` package in your project (`pip install langfuse>=2.0.0`)
2. Load API keys from environment variables
3. Initialize the Langfuse client with your project's keys
4. Wrap your LLM calls with Langfuse tracing

Example:
```python
from langfuse import Langfuse

# Initialize with project-specific keys
langfuse = Langfuse(
    public_key=os.getenv("BUDGET_CLAUDE_PUBLIC_KEY"),
    secret_key=os.getenv("BUDGET_CLAUDE_SECRET_KEY"),
    host="http://localhost:3001"  # Or your remote Langfuse URL
)

# Trace your LLM calls
trace = langfuse.trace(name="categorize_transaction")
# ... rest of tracing code
```

## Architecture

```
Host Machine (macOS M2)
│
├── Ollama (localhost:11434)
│   └── llama3.1:8b model
│
├── budget_claude/ (sibling project)
│   └── Connects to Langfuse via http://localhost:3000
│
├── budget_cursor/ (sibling project)
│   └── Connects to Langfuse via http://localhost:3000
│
└── budget_tracing/ (this repo)
    ├── Docker Container: Langfuse Server
    │   └── http://localhost:3000
    └── Docker Container: PostgreSQL Database
        └── localhost:5432 (internal to Docker network)
```

## Troubleshooting

### Langfuse won't start

```bash
# Check container logs for errors
docker-compose logs langfuse

# Ensure ports aren't already in use
lsof -i :3000
lsof -i :5432

# Try forcing a restart
docker-compose restart
```

### Can't connect from sibling projects

- Ensure `LANGFUSE_HOST` in your sibling projects is set correctly:
  - From Docker container: `http://host.docker.internal:3000`
  - From host machine: `http://localhost:3000`
- Check firewall settings
- Verify API keys are correct in sibling projects

### Database connection issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify database exists
docker-compose exec postgres psql -U langfuse -d langfuse -c "\dt"
```

### Out of memory or performance issues

The current setup is optimized for your M2 Mac with 24GB RAM. If you experience slowness:
- Check Docker's memory allocation: `docker stats`
- Check host system resources: `top`, `Activity Monitor`
- Consider scaling back other services or increasing Docker's memory limit

## Next Steps

1. Configure your sibling projects to use this Langfuse instance
2. Start instrumenting your LLM code with Langfuse tracing
3. Monitor performance and costs in the Langfuse dashboard
4. Set up alerts and dashboards based on your monitoring needs

For detailed integration instructions, see **INTEGRATION_GUIDE.md**.

## Support

For issues with:
- **Langfuse**: https://github.com/langfuse/langfuse
- **Docker**: https://docs.docker.com/
- **This setup**: Check the troubleshooting section or review the INTEGRATION_GUIDE.md

## License

This setup is provided as-is for use with the budget project suite.
