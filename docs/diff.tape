# pip-skill diff demo (VHS, https://github.com/charmbracelet/vhs)
#
# Regenerate with: vhs docs/diff.tape && cp docs/diff.gif demos/diff.gif
#
# Requires the demo venv (run scripts/bootstrap-demo.sh first).

Output docs/diff.gif

Set Theme "Catppuccin Mocha"
Set FontSize 18
Set Width 1100
Set Height 380
Set Padding 24
Set TypingSpeed 28ms
Set Shell "bash"

Hide
Type "cd /tmp && rm -rf requests && export VIRTUAL_ENV_DISABLE_PROMPT=1 && source /tmp/pip-skill-demo-env/bin/activate && export PS1='$ ' && pip-skill convert requests > /dev/null 2>&1 && clear" Enter
Sleep 1500ms
Show

Type "# Detect API drift between a generated skill and the installed package."
Sleep 300ms
Enter
Sleep 400ms
Type "pip-skill diff ./requests"
Sleep 200ms
Enter
Sleep 2500ms
