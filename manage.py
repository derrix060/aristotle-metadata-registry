#!/usr/bin/python3

import os
import sys
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    if 'test' in sys.argv:
        testindex = sys.argv.index('test')
        after = sys.argv[testindex+1]
        command = sys.argv

        split = after.split('.')
        module = split[0]

        if module == 'python':
            module = split[2]
            command[2] = '.'.join(split[2:])

        if module == 'aristotle_mdr':
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aristotle_mdr.tests.settings.settings")
        else:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", module + ".tests.settings")

        execute_from_command_line(command)

    elif 'schemamigration' in sys.argv:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aristotle_mdr.tests.settings.settings")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aristotle_mdr.required_settings")


execute_from_command_line(sys.argv)
