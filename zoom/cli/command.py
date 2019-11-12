class CommandFailure(Exception): pass

class Command:
    arguments = tuple()
    options = tuple()

    def __init__(self, cli_arguments, cli_options, verbose):
        self.cli_arguments = cli_arguments
        self.cli_options = cli_options
        self.verbose = verbose

    @classmethod
    def describe_usage(cls, command_name):
        description = 'Command usage: zoom %s %s %s'%(command_name, ' '.join(
            '<%s>'%argument[0] for argument in cls.arguments
        ), ' '.join(
            '[-%s | --%s]'%(option[1], option[0]) for option in cls.options
        ))

        if cls.arguments:
            description += '\n\nCommand arguments:'
            for name, argument_description in cls.arguments:
                name = name + (' '*(13 - len(name)))
                description += '\n  %s %s'%(name, argument_description)

        if cls.options:
            description += '\n\nCommand-specific options:'
            for name, shorthand, option_description in cls.options:
                name = '--%s'%name
                if shorthand:
                    name = '-%s, %s'%(shorthand, name)
                name = name + (' '*(13 - len(name)))
                description += '\n  %s %s'%(name, option_description)

        return description

    def get_argument(self, name, default=None, take_input=True):
        k = 0
        for i, argument in enumerate(self.arguments):
            if argument[0] == name:
                k = i
                break

        value = self.cli_arguments[k] if k < len(self.cli_arguments) else None
        if value:
            return value

        if not take_input:
            return default

        definition = self.arguments[k]
        return input('%s (%s): '%(
            definition[0], definition[1][0:-1]
        ))

    def get_option(self, name, typ=None, default=None, take_input=False):
        definition = 0
        for option in self.options:
            if option[0] == name:
                definition = option
                break

        name, shorthand, description = definition

        value = (
            self.cli_options.get('--%s'%name) or 
            self.cli_options.get('-%s'%shorthand)
        )
        if value:
            if typ:
                try:
                    value = typ(value)
                except ValueError:
                    raise CommandFailure('Invalid value for "%s"'%name)
            return value

        if not take_input:
            return default

        return input('%s (%s): '%(
            name, description[0:-1]
        ))
        
    def run(self):
        raise NotImplementedError()
