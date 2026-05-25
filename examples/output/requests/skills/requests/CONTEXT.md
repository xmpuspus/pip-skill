# Agent Guidelines for requests

## How to Use This Skill

1. Read `SKILL.md` for available functions and quick start
2. Check `references/api-reference.md` for detailed parameter schemas
3. Execute Python via the Bash tool: `python3 -c "import requests; ..."`

## Best Practices

- Start with the simplest function call to verify the package is installed
- For functions with many parameters, start with required params only
- Check return types in api-reference.md before parsing results
- If a function fails, check the error message for missing dependencies

## Context Window Management

- SKILL.md contains the 20 most useful functions
- api-reference.md contains full schemas; read only the sections you need
- Do not read the entire api-reference.md into context unless necessary

## Error Handling

- `ImportError`: Package not installed. Run `pip install requests`
- `AttributeError`: Function may have moved between versions. Check `requests.__version__`
- `TypeError`: Wrong argument types. Check parameter types in SKILL.md
