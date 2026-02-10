# Bug Hunter AI

An AI-powered agent for fixing bugs in IoT device code. The agent uses language models to analyze code, understand issues, and automatically fix bugs by reading files, making edits, and running tests.

## Features

- 🤖 **AI-Powered Bug Fixing**: Automatically fixes bugs in code using LLM reasoning
- 📚 **Documentation-Aware**: Can reference language and device documentation when fixing bugs
- 🔌 **Multi-Provider Support**: Works with Ollama, Groq, Gemini, and Hugging Face APIs
- 🔧 **Tool-Based Architecture**: Uses function calling to interact with the codebase
- 🧪 **Test-Driven**: Validates fixes by running test files

## Installation

### Prerequisites

- Python 3.13 or higher
- (Optional) `uv` package manager for faster dependency management

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Amitlaxman/bug-hunter-ai.git
cd bug-hunter-ai
```

2. Install dependencies:

**Using pip:**
```bash
pip install -r requirements.txt
```

**Using uv (recommended):**
```bash
uv pip install -r requirements.txt
```

3. Configure environment variables by copying `.env` and updating it:
```bash
cp .env.example .env  # If you have an example file
# Or edit .env directly
```

## Configuration

Edit the `.env` file to configure the agent:

### Required Settings

```env
WORKING_DIRECTORY=./converter          # Directory containing your IoT project code
MODEL=qwen2.5:14b                      # Model name (provider-specific)
OPENAI_API_KEY=your-api-key-here      # API key for your chosen provider
```

### Provider Configuration

The agent supports multiple LLM providers. Set `API_PROVIDER` to switch:

#### Ollama (Local)
```env
API_PROVIDER=ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
MODEL=qwen2.5:14b
```

#### Groq (Free/Cheap Tier)
```env
API_PROVIDER=groq
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=your-groq-api-key
MODEL=llama-3.2-3b-preview
```

#### Gemini (OpenAI-Compatible)
```env
API_PROVIDER=gemini
OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
OPENAI_API_KEY=your-gemini-api-key
MODEL=gemini-2.5-flash
```

#### Hugging Face
```env
API_PROVIDER=huggingface
OPENAI_BASE_URL=https://api-inference.huggingface.co/v1
OPENAI_API_KEY=your-hf-api-key
MODEL=your-hf-model-id
```

**Note:** If `OPENAI_BASE_URL` is not set, the agent will use provider-specific defaults based on `API_PROVIDER`.

### Documentation Configuration (Optional)

To enable documentation-aware bug fixing:

```env
DOCS_DIRECTORY=./docs/iot-language-spec    # Path to documentation folder
LANGUAGE_NAME=YourIoTLang 1.0               # Name of the IoT language
DEVICE_NAME=YourDeviceModelX                # Target device/platform name
```

### Other Settings

```env
MAX_CHARS=10000        # Maximum characters to read from a file
MAX_RETRIES=5          # Maximum API retry attempts
```

## Documentation Setup

The agent can reference language and device documentation when fixing bugs. This is especially useful for IoT-specific languages.

### Adding Documentation

1. Place your documentation files in the directory specified by `DOCS_DIRECTORY` (default: `./docs/iot-language-spec`)

2. Suggested file structure:
   ```
   docs/iot-language-spec/
   ├── README.md              # Overview
   ├── language-spec.md       # Syntax and semantics
   ├── std-lib.md            # Standard library
   ├── hardware-api.md       # Device APIs
   ├── examples.md           # Code examples
   └── troubleshooting.md    # Common issues
   ```

3. The agent will automatically:
   - Be instructed to consult documentation when unsure
   - Use `get_files_info` to list available docs
   - Use `get_file_content` to read specific documentation files

**No code changes needed** - just add files to the docs directory and set `DOCS_DIRECTORY` in `.env`.

## Usage

### Basic Usage

```bash
python main.py "Fix the bug in temperature.py: alert_threshold_c must be 80°C"
```

### With Verbose Output

```bash
python main.py "Fix the bug in temperature.py" --verbose
```

### Using uv

```bash
uv run main.py "Fix the bug in temperature.py" --verbose
```

---

## C++ Bug Detection Pipeline

An agentic system for **C++ (RDI) bug detection** that accepts code snippets, identifies the **exact line** where the bug first manifests, and outputs results in **CSV format (ID, Bug Line, Explanation)** with MCP-based documentation grounding.

### Architecture

- **Code Parsing Agent**: Structures code with line numbers for downstream agents.
- **Bug Detection Agent**: Uses the LLM to decide if a bug exists and the first manifest line.
- **MCP Doc Lookup Agent**: Calls the MCP server’s `search_documents` to retrieve relevant API/bug-pattern docs.
- **Explanation Generation Agent**: Produces a short explanation **referencing** the retrieved MCP documentation.

The pipeline runs: **Parse → MCP Lookup → Detect → Explain**, then writes CSV with columns **ID**, **Bug Line**, **Explanation**.

### Prerequisites

1. **MCP server** (for documentation grounding): run the server so `search_documents` is available.
2. **LLM config**: same `.env` as above (`OPENAI_API_KEY`, `MODEL`, `API_PROVIDER`, etc.).

### Run the MCP server

From the project root:

```bash
cd server
python mcp_server.py
```

The server listens on **port 8003** (SSE). Leave it running while using the pipeline.

Optional: ingest bug patterns from `samples.csv` into the server’s index (run once):

```bash
python server/ingest_from_samples.py
```

### Run the pipeline

From the project root:

```bash
# Default: read samples.csv, print CSV to stdout
python detect_bugs.py

# Write to file
python detect_bugs.py samples.csv -o results.csv

# Limit to first 5 rows (testing)
python detect_bugs.py -n 5 -o results.csv

# Without MCP (no doc lookup)
python detect_bugs.py --no-mcp -o results.csv
```

### Output format

Strict CSV with three columns:

| Column     | Description |
|-----------|-------------|
| **ID**    | Sample ID (from input CSV or row index). |
| **Bug Line** | 1-based line number where the bug first manifests; `0` if no bug. |
| **Explanation** | Short explanation of the bug, grounded in MCP docs when available. |

### MCP server URL

By default the client connects to `http://localhost:8003/sse`. Override with:

```env
MCP_SERVER_URL=http://localhost:8003/sse
```

### Project layout (pipeline)

```
agents/
├── parsing.py       # Code parsing agent
├── mcp_client.py    # MCP client (search_documents)
├── mcp_lookup.py    # MCP doc lookup agent
├── detection.py     # Bug detection agent
├── explanation.py   # Explanation generation agent
└── orchestrator.py  # Pipeline orchestration
server/
├── mcp_server.py    # MCP server (run first)
├── ingest_from_samples.py  # Ingest samples into index
└── storage/         # Persisted vector index
detect_bugs.py       # CLI entrypoint for pipeline
samples.csv          # Input CSV (ID, Explanation, Context, Code, Correct Code)
```

### Evaluation

Use `samples.csv` as the primary test set: run the pipeline on the **Code** column and compare **Bug Line** to ground truth (e.g. from a diff with **Correct Code**) and **Explanation** to the existing **Explanation** column. You can add a **Bug Line** column to the CSV later for ground truth.

---

## How It Works

### Architecture

The agent follows an agentic loop pattern:

1. **Initialization**: Loads configuration, creates LLM client, sets up system prompt
2. **Message Setup**: Creates conversation with system instructions and user prompt
3. **Agentic Loop**:
   - Sends messages + available tools to LLM
   - LLM decides which tool to call (or responds directly)
   - Executes tool calls (file operations, code execution)
   - Adds results back to conversation
   - Repeats until LLM provides final response

### Available Tools

- `get_files_info(directory)` - List files in a directory
- `get_file_content(file_path)` - Read file contents
- `write_file(file_path, content)` - Write/update file contents
- `run_python_file(file_path)` - Execute Python test files

### System Prompt

The agent uses a strict system prompt that:
- Instructs it to **fix bugs, not just explain them**
- Requires complete file rewrites (not partial edits)
- Enforces testing before declaring success
- References documentation when available
- Responds only in English

## Project Structure

```
bug-hunter-ai/
├── agent_core/              # Core agent library
│   ├── __init__.py
│   └── llm_client.py       # Provider-agnostic LLM client
├── agents/                  # C++ bug detection pipeline
│   ├── parsing.py           # Code parsing agent
│   ├── mcp_client.py        # MCP client
│   ├── mcp_lookup.py        # MCP doc lookup agent
│   ├── detection.py         # Bug detection agent
│   ├── explanation.py       # Explanation generation agent
│   └── orchestrator.py     # Pipeline + CSV output
├── converter/              # Example IoT project (WORKING_DIRECTORY)
│   ├── temperature.py      # IoT device configuration (with bug)
│   └── main.py             # Test harness
├── docs/                    # Documentation directory
│   └── iot-language-spec/  # Place IoT language docs here
├── server/                  # MCP server + ingestion
│   ├── mcp_server.py        # MCP server (SSE, port 8003)
│   ├── ingest_from_samples.py
│   └── storage/             # Vector index storage
├── functions/               # Tool implementations (IoT agent)
│   └── fn.py
├── main.py                 # CLI entry point (IoT bug fixing)
├── detect_bugs.py          # CLI entry point (C++ bug detection pipeline)
├── prompts.py              # System prompt builder
├── tools.py                # Tool schema definitions
├── samples.csv             # Input for C++ pipeline (ID, Code, etc.)
├── requirements.txt        # Python dependencies
└── .env                    # Configuration (not in git)
```

## Key Components

| Component | Purpose |
|-----------|---------|
| `WORKING_DIRECTORY` | Root directory for all file operations |
| `DOCS_DIRECTORY` | Location of language/device documentation |
| `tools[]` | JSON schemas describing available functions |
| `messages[]` | Conversation history that grows with tool calls |
| `agent_core.llm_client` | Provider-agnostic LLM client factory |

## Token Rate Limits

If you encounter rate limits, consider:
- Using local models (Ollama) for unlimited usage
- Switching to providers with higher rate limits
- Adjusting `MAX_RETRIES` in `.env` to handle temporary limits

## Contributing

Contributions welcome! Please feel free to submit issues or pull requests.


## Links

- Repository: https://github.com/Amitlaxman/bug-hunter-ai
