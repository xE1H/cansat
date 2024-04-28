class Logger(object):
    def __init__(self):
        self.colors = {
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'reset': '\033[0m',
            'white': '\033[97m',
        }

    def log(self, prefix, message, color='green'):
        print(
            f'{self.colors["reset"]}[{self.colors["blue"]}{prefix}{self.colors["reset"]}]:{self.colors[color]} {message}{self.colors["reset"]}')
