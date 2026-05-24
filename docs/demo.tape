# pip-skill hero demo (VHS, https://github.com/charmbracelet/vhs)
#
# Regenerate with: vhs docs/demo.tape
# Outputs:         docs/demo.gif (the README hero) and docs/demo.mp4
#
# Design intent: real terminal output, not synthesised typing. Viewer
# verifies the value prop in the first ~5 seconds: one command, a real
# pip package, a real skill bundle on disk. Re-recording requires the
# bootstrapped venv at /tmp/pip-skill-demo-env (see scripts/bootstrap-demo.sh).

Output docs/demo.gif
Output docs/demo.mp4

Set Theme "Catppuccin Mocha"
Set FontSize 18
Set Width 1100
Set Height 600
Set Padding 24
Set TypingSpeed 28ms
Set PlaybackSpeed 1.0
Set Shell "bash"

Hide
Type "cd /tmp && rm -rf requests && export VIRTUAL_ENV_DISABLE_PROMPT=1 && source /tmp/pip-skill-demo-env/bin/activate && export PS1='$ ' && clear" Enter
Sleep 800ms
Show

Type "# Turn an installed pip package into an AI skill, in one command."
Sleep 400ms
Enter
Sleep 500ms
Type "pip-skill convert requests"
Sleep 300ms
Enter
Sleep 2500ms

Type "# Read what got generated."
Enter
Sleep 400ms
Type "head -8 requests/skills/requests/SKILL.md"
Enter
Sleep 1800ms

Type "# Verify the skill stays in sync with the installed package."
Enter
Sleep 400ms
Type "pip-skill test ./requests"
Enter
Sleep 2500ms
