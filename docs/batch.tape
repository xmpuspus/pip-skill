# pip-skill batch demo (VHS, https://github.com/charmbracelet/vhs)
#
# Regenerate with: vhs docs/batch.tape && cp docs/batch.gif demos/batch.gif
#
# Requires the demo venv (run scripts/bootstrap-demo.sh first) plus
# httpx and click installed in it.

Output docs/batch.gif

Set Theme "Catppuccin Mocha"
Set FontSize 18
Set Width 1100
Set Height 380
Set Padding 24
Set TypingSpeed 28ms
Set Shell "bash"

Hide
Type "cd /tmp && rm -rf requests httpx click && export VIRTUAL_ENV_DISABLE_PROMPT=1 && source /tmp/pip-skill-demo-env/bin/activate && export PS1='$ ' && clear" Enter
Sleep 800ms
Show

Type "# Convert three packages in parallel."
Sleep 300ms
Enter
Sleep 400ms
Type "pip-skill batch requests httpx click --workers 3"
Sleep 200ms
Enter
Sleep 3500ms
