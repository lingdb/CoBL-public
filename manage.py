import sys
import pathlib

from django.core.management import execute_from_command_line

from cobl import configure


if __name__ == "__main__":
    ci, cfg_path = 0, None
    for i, arg in enumerate(sys.argv):
        if arg.endswith('.ini') and pathlib.Path(arg).exists():
            ci = i
            break
    if ci:
        cfg_path = pathlib.Path(sys.argv.pop(ci))
    configure(cfg_path)
    execute_from_command_line(sys.argv)

