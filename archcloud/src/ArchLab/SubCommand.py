import logging as log

class SubCommand(object):

    def __init__(self, parent_subparser, name, help):
        self.subparsers = parent_subparser
        self.name = name
        self.help = help
        self.parser = self.subparsers.add_parser(name=name, help=help)
        self.parser.set_defaults(func=self._run)
        self.parser.add_argument('-v', action='store_true', dest="verbose", default=False, help="Be verbose")        
    def _run(self, args):
        log.debug(f"Executing {self.name} with {args}")
        self.run(args)
