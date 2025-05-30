# Development Tools Configuration

## Overview

This directory contains configuration files for various development tools and IDEs used in the project. These configurations are isolated here to keep the project root clean while preserving development environment setups.

## Contents

### `.cursor/`
Configuration for Cursor IDE and VS Code integration.
- `mcp.json`: MCP (Model Context Protocol) settings
- `rules/`: Custom rules for code assistance and development workflow

### `.roo/`
Configuration for Roo development assistant.
- `rules/`: Development workflow rules
- `rules-architect/`: Architecture-specific rules
- `rules-ask/`: Query and assistance rules
- `rules-boomerang/`: Boomerang workflow rules
- `rules-code/`: Code generation and review rules
- `rules-debug/`: Debugging assistance rules
- `rules-test/`: Testing workflow rules

### `.roomodes`
Roo operation modes configuration.

### `.taskmasterconfig`
Configuration for TaskMaster project management integration.

### `.windsurfrules`
Rules and configuration for Windsurf AI development environment.

## Why This Organization?

1. **Clean Project Root**: Keeps development tool configurations separate from core project files
2. **Developer Experience**: Preserves IDE and tool settings for team consistency
3. **Optional Setup**: Developers can choose which tools to use without affecting the core project
4. **Version Control**: Allows tracking of development configurations while keeping them isolated

## Usage

### For Team Members
If you're using any of these development tools, you can:

1. **Copy configurations**: Link or copy relevant configurations to your project root if needed
2. **Customize safely**: Modify configurations without affecting the core project structure
3. **Share improvements**: Contribute improvements to shared development workflows

### For New Developers
These configurations are optional but recommended for consistent development experience:

```bash
# Example: Link Cursor configuration to project root (if using Cursor)
ln -s .dev/.cursor .cursor

# Example: Link Roo configuration (if using Roo)
ln -s .dev/.roo .roo
```

## Best Practices

1. **Tool-Specific Settings**: Keep tool configurations tool-specific and avoid cross-dependencies
2. **Documentation**: Document any special setup requirements in tool-specific README files
3. **Team Consistency**: Use shared configurations for consistent code formatting and workflows
4. **Privacy**: Avoid committing personal or sensitive configurations

## Adding New Development Tools

When adding configuration for new development tools:

1. Create a subdirectory in `.dev/`
2. Add appropriate entries to `.gitignore` if needed
3. Document the tool's purpose and setup in this README
4. Consider creating setup scripts for complex configurations

## Notes

- These configurations are designed to be portable and shareable among team members
- Individual developers may need to adapt configurations based on their local environment
- Not all tools are required for development - use what works best for your workflow
