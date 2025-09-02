# TaylorMadePromptLibrary
A fast, portable prompt library with PowerShell and Python tools.

## Quickstart
```powershell
# list
pwsh -File tools/list-prompts.ps1 -Sort updatedAt -Order desc -Limit 20
# add
pwsh -File tools/add-prompt.ps1 -Title "One-Liner Summary" -Category Writing -Body "Summarize..." -Tags writing summary
# search titles/bodies
pwsh -File tools/find-prompts.ps1 -Query research -Body
```
```bash
# python cli (optional)
python -m venv .venv && . .venv/bin/activate
python cli/tmpl.py list --q research --limit 10
python cli/tmpl.py add --title "OSINT Sweep" --category OSINT --body "You are an OSINT analyst..." --tags osint sweep
```

## Contributing
- Keep prompts atomic and reusable.
- Respect the style guide; validate before PR.
