# IoT Language Documentation

Place your IoT language and device documentation files in this directory.

## Directory Structure

The agent can access any files placed here using the `get_files_info` and `get_file_content` tools.

### Suggested Organization

- `language-spec.md` - Language syntax and semantics
- `std-lib.md` - Standard library reference
- `hardware-api.md` - Hardware/device API documentation
- `examples/` - Example code snippets
- `troubleshooting.md` - Common issues and solutions

## How It Works

When `DOCS_DIRECTORY` is set in `.env`, the agent will:
1. Be instructed to consult documentation when unsure about syntax or behavior
2. Use `get_files_info` to list available documentation files
3. Use `get_file_content` to read specific documentation files

## Adding Documentation

Simply add your documentation files to this directory. The agent will automatically be able to access them without any code changes.
