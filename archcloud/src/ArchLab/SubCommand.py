import logging as log

class SubCommand(object):

    def __init__(self, parent_subparser, name, help):
        self.subparsers = parent_subparser
        self.name = name
        self.help = help
        self.parser = self.subparsers.add_parser(name=name, help=help)
        self.parser.set_defaults(func=self._run)

    def _run(self, args):
        log.debug("Executing {self.name} with {args}")
        self.run(args)
