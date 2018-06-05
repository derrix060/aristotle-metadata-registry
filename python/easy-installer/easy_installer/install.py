"""
Aristotle Easy Installer

This script guides you through the setup of the Aristotle Metadata Registry.

Run install --help for help text
"""

import os
import re
import sys
from subprocess import call
from random import getrandbits
import hashlib
import shutil
import argparse

BASE_DIR = os.path.dirname(__file__)
name = "newly created"  # Forward-declaration placeholder
PIP_MSG = "You can finish installing by running - pip install -r requirements.txt - from the %s directory" % name

optional_modules = [
    ("Aristotle Glossary Extension", "#!aristotle_glossary!"),
    ("Aristotle Dataset Extensions", "#!aristotle_dse!"),
    ("Aristotle MDR API", "#!aristotle_mdr_api!"),
    ("Aristotle Graphql API", '#!aristotle_graphql!'),
    ("Aristotle PDF Downloads", '#!aristotle_pdf!'),
    ("Comet Indicator Registry", '#!comet!'),
    ("Mallard Questionnaire Registry", '#!mallard!')
]

def valid_input(prompt, match):

    for i in range(5):
        check = input(prompt)
        if re.match(match, check):
            return check
    raise Exception

def ask_yesno(message):
    yn = '^[YyNn]?$'  # yes/no regex
    return 'y' == valid_input('{} (y/n): '.format(message), yn).lower()

def setup_mdr(args):
    name_regex = '^[a-z][a-z_]*$'

    if not args.name or not re.match(name_regex, args.name[0]):
        name = valid_input("Enter the system name for your registry (lowercase letters and underscores ONLY): ", name_regex)
    else:
        name = args.name[0]

    if not args.directory or args.directory[0] == '.':
        print('No directory specified, Using current directory')
        directory = os.getcwd()
    else:
        directory = args.directory[0]

    use_existing_files = check_example_exists(directory, name)

    if not use_existing_files:

        copied = copy_example_mdr(directory)

        if not copied:
            print("Copying Example registy failed")
            exit()

        rename_example_mdr(name, directory)

    extensions = []

    do_install = ask_yesno("Do you wish to install any additional Aristotle modules?")
    if do_install:
        print("Select extensions to install (y/n)")
        for display, ext_token in optional_modules:
            do_ext = ask_yesno("  %s: "%display)
            if do_ext:
                extensions.append(ext_token)

    if extensions:
        start_dir = os.path.join(directory, name, name)
        find_and_remove(start_dir, extensions)

    # Update the settings key
    generate_secret_key(name, directory)

    if args.dry_install:
        do_install = False
    elif args.force_install:
        do_install = True
    else:
        do_install = ask_yesno("Ready to install requirements and run setup commands?")

    if not do_install:
        print("Performing dry run, no requirements installed.")
        print(PIP_MSG)
        exit()

    try:
        install_reqs(name, directory)
    except:
        print("Installing requirements failed.")
        print(PIP_MSG)
        exit()

    print("Running django management commands")
    result = manage_commands(name, directory)
    print("You can now locally test your installed registry by running the command './manage.py runserver'")

    print('Done! Your registry was installed in %s' % directory)

def generate_secret_key(name, directory):
    key = "Change-this-key-as-soon-as-you-can"
    # This is probably not cryptographically secure, not for production.
    gen_key = hashlib.sha224(str(getrandbits(128)).encode('utf-8')).hexdigest()
    fname = '%s/%s/settings.py' % (name, name)
    fpath = os.path.join(directory, fname)
    with open(fpath) as f:
        s = f.read()
    s = s.replace(key, gen_key)
    with open(fpath, "w") as f:
        f.write(s)


def rename_example_mdr(name, directory):
    startpath = os.path.join(directory, 'example_mdr')

    os.rename(os.path.join(startpath, 'example_mdr'), os.path.join(startpath, name))
    os.rename(startpath, os.path.join(directory, name))

    new_startpath = os.path.join(directory, name)
    find_and_replace(new_startpath, 'example_mdr', name)


def install_reqs(name, dir):
    # pip.main(['install', package])
    reqfile = os.path.join(dir, '%s/requirements.txt' % name)
    result = call(["pip", 'install', '-r%s' % reqfile])
    return result


def manage_commands(name, dir):
    manage_path = os.path.join(dir, '%s/manage.py' % name)
    migrate = call(["python3", manage_path, 'migrate'])
    cstatic = call(["python3", manage_path, 'collectstatic'])
    cctable = call(["python3", manage_path, 'createcachetable'])
    return (migrate, cstatic, cctable)

def check_example_exists(dir, name):

    dest = os.path.join(dir, name)
    if os.path.isdir(dest):
        print('A folder is already at %s' % dest)
        use_existing = ask_yesno("Would you like to use the existing files? They will be deleted otherwise")
        if use_existing:
            return True
        else:
            you_sure = ask_yesno("Are you sure you want to delete the directory at %s"%dest)
            if you_sure:
                print('Deleting existing example_mdr')
                shutil.rmtree(dest)
                return False
            else:
                print('Using existing files')
                return True

    return False

def copy_example_mdr(dir):
    print("Copying in example metadata registry")
    source = os.path.join(BASE_DIR, 'example_mdr')
    dest = os.path.join(dir, 'example_mdr')

    if os.path.isdir(source):
        shutil.copytree(source, dest)
        return True

    return False

def find_and_replace(mydir, old, new):
    """Really naive find and replace lovingly borrowed from stack overflow - http://stackoverflow.com/a/4205918/764357"""
    for dname, dirs, files in os.walk(mydir):
        for fname in files:
            if fname.endswith(('py', 'txt', 'rst')):
                fpath = os.path.join(dname, fname)
                with open(fpath) as f:
                    s = f.read()
                s = s.replace(old, new)
                with open(fpath, "w") as f:
                    f.write(s)

def find_and_remove(mydir, extensions):
    for dname, dirs, files in os.walk(mydir):
        for fname in files:
            if fname.endswith(('py', 'txt', 'rst')):
                fpath = os.path.join(dname, fname)
                with open(fpath) as f:
                    s = f.read()
                for ext in extensions:
                    s = s.replace(ext, '')
                with open(fpath, "w") as f:
                    f.write(s)

def main():

    parser = argparse.ArgumentParser(description='Install Aristotle Example Registry')
    parser.add_argument('-n', '--name', nargs=1, default='', type=str, dest='name', help='Registry Name')
    parser.add_argument('-f', '--force', action='store_true', default=False, dest='force_install', help='Force requirements install and setup commands (instead of asking)')
    parser.add_argument('-d', '--dry', action='store_true', default=False, dest='dry_install', help='Dry Install (do requirements installed or management commands run)')
    parser.add_argument('--dir', nargs=1, default='.', dest='directory', help='Directory to install the registry (default: current directory)')

    args = parser.parse_args()

    return setup_mdr(args)
