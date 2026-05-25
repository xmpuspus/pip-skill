"""Sentinel CLI entry point.

If the introspector walks this module it will execute the print below,
which the test asserts NEVER happens. Real-world equivalents:
flask.__main__ runs Click against sys.argv, django.__main__ runs
manage.py-style commands, uvicorn.__main__ starts a server.
"""

print("FAKE_PACKAGE_MAIN_EXECUTED")
