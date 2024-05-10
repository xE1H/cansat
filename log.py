class Logger(object):
    def __init__(self, prefix='GENERAL'):
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m',
            'white': '\033[97m',
        }
        self.prefix = prefix

    def log(self, message, color='green'):
        print(
            f'{self.colors["reset"]}[{self.colors["blue"]}{self.prefix}{self.colors["reset"]}]:{self.colors[color]} {message}{self.colors["reset"]}')
