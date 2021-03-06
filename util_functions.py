#################################################
# author:       Ryan Ritchie                    #
# student no:   17019225                        #
# email:        ryan2.ritchie@live.uwe.ac.uk    #
#################################################


import importlib
import requests
import requests.exceptions
import unittest

from os import system, name

# aesthetics imports
try:
    import colorama
except ModuleNotFoundError:
    print('Required modules not found. use pip install -r requirements.txt')
    exit(1)

from colorama import Fore
colorama.init(autoreset=True)


def clear_screen():
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


def load_module(package_name, class_name):
    try:
        module = importlib.import_module(f'{package_name}.{class_name}')

        for _class in dir(module):
            obj = getattr(module, _class)

            try:
                if obj.__name__ == class_name:
                    return obj

            except AttributeError as e:
                print(e)
                pass

    except ImportError:
        return None

###############################################################################
#                                                                             #
#                            HTTP UTIL FUNCTIONS                              #
#                                                                             #
###############################################################################


def http_get_request(url, cookies):
    """

        @param url (str) -              the URL to make the request to
        @param cookies (dict) -         the cookies to send with the request
    """
    try:
        r = requests.get(url, cookies=cookies)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        warning(f'Server at {url} is not responding')
        return None

    return r


def http_post_request(url, post_params, cookies):
    """

        @param url (str) -              the URL to make the request to
        @param post_params (dict) -     the post parameters to include
        @param cookies (dict) -         the cookies to send with the request
    """
    try:
        r = requests.post(url, data=post_params, cookies=cookies)

    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        warning(f'Server at {url} is not responding')
        return None

    return r


def cookie_parse(cookie_string):
    if not cookie_string:
        return {}

    cookies = cookie_string.split(',')

    cookie_dict = {}
    for c in cookies:
        k, v = c.split('=')
        cookie_dict[k] = v

    return cookie_dict

###############################################################################
#                                                                             #
#                           PRINT UTIL FUNCTIONS                              #
#                                                                             #
###############################################################################


def banner_colour(banner):
    print(Fore.CYAN + banner)


def _print_status(message, type, prepend):
    if type == 'success':
        colour = Fore.GREEN
        status_code = '+'
    elif type == 'warning':
        colour = Fore.RED
        status_code = '-'
    elif type == 'info':
        colour = Fore.YELLOW
        status_code = '*'
    elif type == 'highlight':
        colour = Fore.CYAN
        status_code = '!'

    print(colour + f'{prepend}[{status_code}] {message}\n', end='')


def success(message, prepend=''):
    _print_status(message, 'success', prepend)


def warning(message, prepend=''):
    _print_status(message, 'warning', prepend)


def info(message, prepend=''):
    _print_status(message, 'info', prepend)


def highlight(message, prepend=''):
    _print_status(message, 'highlight', prepend)


class Test(unittest.TestCase):
    def test_cookie_parse(self):
        c_string = 'testcookie=1,PHPSESSID=ff7p62chjhlfi69o71nqk5vqd4'
        cookies = cookie_parse(c_string)
        self.assertEqual(cookies['testcookie'], '1')
        self.assertEqual(cookies['PHPSESSID'], 'ff7p62chjhlfi69o71nqk5vqd4')


if __name__ == '__main__':
    unittest.main()
