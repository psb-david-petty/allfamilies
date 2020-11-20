#!/usr/bin/env python3
#
# allfamilies.py
#

import argparse, csv, enum, os, re, sys

"""
The allfamilies module is a command-line tool for parsing an Aspen student
report. 
"""


def families(path, addresses=None,
             pp=False, rp=False, tp=False, sp=False, verbose=False,
             parents=['mother', 'father', 'guardian', ], ):
    """Parse .CSV file path and create GMail-formatted e-mail addresses.
    TODO: document all parameters"""
    with open(path, 'rb') as csv_file:
        lines = [line.decode('ISO-8859-1') for line in csv_file.readlines()]
        # Check whether lines is a single entry w/ '\r's.
        if len(lines) == 1:
            lines = lines[0].split('\r')

        # Parse the rows as follows:
        # ['', 'Name', 'Aardvark, TestStudent10', '', '333 Washington St #2', '', 'Brookline, MA 02445', '', '', '', '', '', '', '', '', '', 'Homeroom', '444']
        # ['Name', '', '', '', '', 'Relationship', '', 'Home Phone', '', 'Work Phone', '', 'Cell Phone', '', '', '', 'Email Address', '', '']
        # ['Aardvark, TestParent10', '', '', '', '', 'Father', '', '555-555-5555', '', '', '', '', '', '', '', 'father@psb.email', '', '']
        # ['Aardvark, TestParent11', '', '', '', '', 'Mother', '', '555-555-4444', '', '', '', '', '', '', '', 'mother@psb.email', '', '']
        # ['Aardvark, StepMother12', '', '', '', '', 'Step Mother', '', '', '', '', '', '', '', '', '', 'step-mother@psb.email', '', '']
        # into:
        # [ '"Aardvark, TestParent10 - Father of Aardvark, TestStudent10" <father@psb.email>,',
        #   '"Aardvark, TestParent11 - Mother of Aardvark, TestStudent10" <mother@psb.email>,',
        # ]

        @enum.unique
        class State(enum.Enum):
            START = 1
            NAME = 2
            COLLECT = 3

        student, preferred, yog = str(), str(), str()
        in_addresses, echoed, state = False, set(), State.START
        for row in csv.reader(lines):
            if row[1].lower().startswith('nam'):
                student = row[2]
                in_addresses = addresses and student in addresses
                if in_addresses or not addresses:
                    if verbose:
                        print(f"Student: {student}")
                if in_addresses:
                    preferred, address = addresses[student]
                    address_regex = r'(\d{2}).*brooklinek12.org'
                    yog = re.sub(address_regex, r'\1', address)
                if in_addresses and student not in echoed and sp:
                    print(gformat(preferred, address))
                    echoed.add(student)
                state = State.NAME
            elif state is State.NAME and row[0].lower().startswith('nam'):
                state = State.COLLECT
            elif state is State.COLLECT and row[14]:
                name = row[0]
                parent = row[5] if row[5] else 'Family'
                rel = parent if rp else str()
                phone = row[12] if tp and row[12] else \
                    row[9] if tp and row[9] else str()
                email = row[14] if row[14].find('@') >= 0 else str()
                if in_addresses or not addresses:
                    if name and email:
                        gmail = gformat(name, email, phone, rel, preferred, yog)
                        if parent.lower() in parents:
                            if verbose:
                                print(f"  Gmail: {gmail}")
                            if pp and email.find('@') >= 0:
                                print(gmail)


def students(path, printp=False, verbose=False):
    """Return dict of students and their e-mail addresses.
    TODO: document all parameters"""
    divider(path, printp)
    with open(path, 'rb') as csv_file:
        lines = [line.decode('ISO-8859-1') for line in csv_file.readlines()]
        # Check whether lines is a single entry w/ '\r's.
        if len(lines) == 1:
            lines = lines[0].split('\r')

        # Parse the rows as follows:
        # ['LastName', 'FirstName', 'Grade', 'Preferred', 'Gender', 'Email1', 'Email2', 'Pref pronoun']
        # ['Fishburn', 'Clarence', '47', '', 'M', clarence.fishburn@gmail.com', '', 'Match to gender']
        email = dict()
        for row in csv.reader(lines):
            if len(row) > 2:
                last, first, pref = row[0], row[1], row[3] if row[3] else row[1]
                rest = [x for x in row[4:] if x.find('@') >= 0]
                if last and first and rest:
                    key, name = f"{last}, {first}", f"{last}, {pref}",
                    email[key] = (name, rest[0], )
                    if verbose: print(f"   Dict: {{'{key}': {email[key]}}}")
        return email


def gformat(name, email, phone=None, rel=None, student=None, yog=None):
    """Return formatted Gmail address suitable for pasting into Gmail 'To:'.
    name and email are required, others are optional. For example:
    'Me, Mom (555-555-5555) - Mother of Me, Son - 2024" <mom@psb.email>, '"""
    assert name and email, \
        f"empty name ({name}) or e-mail address ({email}) for {student}"
    space, dash, lp, rp, of, ds20 = ' ', '-', '(', ')', ' of ', '- 20'
    has_both = rel and student
    year = f"{ds20 + yog if has_both and len(yog) == 2 else str()}"
    return \
        f'"{name}' \
        f'{space + lp + phone + rp if phone else str()}' \
        f'{space + dash if has_both else str()}' \
        f'{space + rel + of + student if has_both else str()}' \
        f'{space + year if has_both and year else str()}' \
        f'" <{email}>, '


def divider(path, printp=True):
    """If printp, print divider w/ path basename."""
    if printp:
        name, width = os.path.basename(path), 70
        left = (width - len(name)) // 2
        right = (width - len(name)) // 2 + len(name) % 2
        print(f"\n{'#' * left} {name} {'#' * right}")


class OptionParser(argparse.ArgumentParser):
    def __init__(self, **kargs):
        argparse.ArgumentParser.__init__(self, **kargs)
        # self.remove_argument("-h")
        self.add_argument("-?", "--help", action="help",
                          help="show this help message and exit")
        self.add_argument('--version', action='version',
                          version='%(prog)s 1.0')

    def error(self, msg):
        sys.stderr.write("%s: error: %s\n\n" % (self.prog, msg, ))
        self.print_help()
        sys.exit(2)


def main(argv):
    """ Parse command-line options and use them with students and families."""
    description = """Parse family .CSV file as saved from PSB Aspen > Students > 
    Reports > Student Contacts - Parent Guardian Only - selecting All & CSV.
    (If student .CSV files are present, only include families of students
    in those files.)"""
    formatter = lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=30)
    parser = OptionParser(description=description, add_help=False,
                          formatter_class=formatter)
    arguments = [
        # c1, c2, action, dest, default, help
        ('-p', '--print', 'store_true', 'print', False, 'print family e-mail addresses', ),
        ('-r', '--relation', 'store_true', 'relation', False, 'include relationship in e-mail addresses', ),
        ('-t', '--telephone', 'store_true', 'phone', False, 'include telephone in e-mail addresses', ),
        ('-s', '--student', 'store_true', 'student', False, 'include student e-mail address if possible', ),
        ('-v', '--verbose', 'store_true', 'verbose', False, 'echo status information', ),
    ]
    # Add optional arguments with values.
    for c1, c2, a, v, d, h in arguments:
        parser.add_argument(c1, c2, action=a, dest=v, default=d, help=h,)
    # Add positional arguments. PATH is both the string and the variable.
    parser.add_argument("PATH", help="path to family .CSV file")
    # Add positional arguments. CSV is both the list and the variable.
    parser.add_argument("CSV", nargs="*", help="path to student .CSV file(s)")
    # Parse arguments.
    ns = parser.parse_args(args=argv[1: ])

    # Execute all_families for all csv paths.
    if ns.CSV:
        for path in ns.CSV:
            addr = students(path, ns.print or ns.student, ns.verbose)
            families(ns.PATH, addr, ns.print, ns.relation, ns.phone, ns.student,
                     ns.verbose)
    else:
        if ns.student:
            print(f"# NOTE: -s, but only PATH ({ns.PATH}) on command-line")
        families(ns.PATH, pp=ns.print, rp=ns.relation, tp=ns.phone,
                 verbose=ns.verbose)


if __name__ == '__main__':
    is_idle, is_pycharm, is_jupyter = (
        'idlelib' in sys.modules,
        int(os.getenv('PYCHARM', 0)),
        '__file__' not in globals()
        )
    if any((is_idle, is_pycharm, is_jupyter, )):
        prefix = '../data/'
        test_path = os.path.join(prefix, 'test-all-families.csv')
        family_path = os.path.join(prefix, '2019-2020-all-families.csv')
        student_paths = [os.path.join(prefix, path) for path in [
            '2019-2020-apcsp-d.csv',
            '2019-2020-s2-ar-f.csv',
            '2019-2020-s2-ecs-b.csv',
            '2019-2020-s2-ecs-e.csv',
            '2019-2020-s2-java-c.csv',
            ]
        ]
        family_path = os.path.join(prefix, '2020-2021-all-families.csv')
        student_paths = [os.path.join(prefix, path) for path in [
            '2020-2021-advisory.csv',
            '2020-2021-apcs-a-d.csv',
            '2020-2021-apcs-p-e.csv',
            '2020-2021-s1-ecs-a.csv',
            '2020-2021-s1-ecs-c.csv',
            '2020-2021-s1-ecs-f.csv',
            ]
        ]
        main(['allfamilies.py', '-prts', family_path, ] + student_paths)
        print()
        main(['allfamilies.py', '-?', test_path, ])
    else:
        main(sys.argv)
