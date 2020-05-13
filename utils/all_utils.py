import sys
import time

class DOT_DICT(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __repr__(self):
        return 'DOT_DICT(' + dict.__repr__(self) + ')'

def program_sleep(sec):
    for remaining in range(sec, 0, -1):
        oneline_print(f'Sleep for {remaining} seconds...')
        time.sleep(1)

def oneline_print(msg):
    sys.stdout.write('\r                                         ')
    sys.stdout.write(f'\r{msg}')
    sys.stdout.flush()
