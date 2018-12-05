#!/usr/bin/env python3
import requests
import json
import getpass
import pathlib
import config
from ppformat import pp

cfg = None

def get_login_token(password):
    global cfg
    response = requests.post(cfg['url'] + "/login", data = {'password' : password})
    json_result = json.loads(response.text)
    return json_result[u'token']

def get(suburl):
    global cfg
    r = requests.get(cfg["url"] + suburl, headers={'X-Auth-Token' : cfg['token']})
    return json.loads(r.text)

def get_beverages():
    return get("/beverages")
def get_users():
    return get("/users")

def order_drink(drink):
    global cfg
    r = requests.post(cfg["url"] + "/orders",
                      headers={'X-Auth-Token': cfg['token']},
                      params={'user': cfg['user'], 'beverage': drink})
    print(r.text)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-format', choices=['text', 'json'], help='Output format')

    cfg = config.Config(pathlib.Path("~/.drinklist").expanduser())
    cfg.add_config_parameter('url', lambda: "https://fius.informatik.uni-stuttgart.de/drinklist/api",
                             help='The API url of the drinklist')
    cfg.add_config_parameter('pw', lambda: getpass.getpass(),
                             help='The drinklist password')
    cfg.add_config_parameter('token', lambda: get_login_token(cfg['pw']),
                             help='The login token to use.')
    cfg.add_config_parameter('user', lambda: input("Username: "),
                             help='Your drinklist username')
    cfg.add_args(parser)

    commands = parser.add_subparsers(title='commands',
                                     metavar='command',
                                     dest='command',
                                     description='The command to run')
    list_parser = commands.add_parser('list', help='List all available beverages.')
    list_parser.add_argument('-regex', help='Filter drinks by regex.', type=str, default=None)

    drink_parser = commands.add_parser('drink', help='Order a drink.')
    order_parser = commands.add_parser('order', help='Alias for drink.')
    def init_drink_parser(drink_parser):
        drink_parser.add_argument('drink', type=str, help='The drink to order')
    init_drink_parser(drink_parser)
    init_drink_parser(order_parser)

    commands.add_parser('users', help='List all registered users.')
    balance_parser = commands.add_parser('balance', help='Get the balance.')
    balance_parser.add_argument('-all', action='store_true',
                                help='show balance for all users')

    history_parser = commands.add_parser('history', help='Get the history.')
    history_parser.add_argument('-all', action='store_true',
                                help='Show history for all users')

    commands.add_parser('help', help='Show this help.')
    args = parser.parse_args()
    cfg.parse_args(args)

    formatter = None
    if args.format == 'json':
        formatter = lambda x: print(json.dumps(x))
    else:
        formatter = lambda x: print(pp(x))

    if args.command in [None, 'help']:
        parser.print_help()
    elif args.command == 'list':
        beverages = get_beverages()
        if args.regex is not None:
            import re
            p = re.compile(args.regex, re.IGNORECASE if args.regex==args.regex.lower() else re.ASCII)
            beverages = [b for b in beverages if p.search(b['name']) is not None]
        formatter(beverages)
    elif args.command in ['order', 'drink']:
        order_drink(args.drink)
    elif args.command == 'balance':
        if args.all:
            res = []
            for user in get_users():
                res+=[get("/users/" + user)]
            formatter(res)
        else:
            formatter([get("/users/" + cfg['user'])])
    elif args.command == 'history':
        if args.all:
            formatter(get("/orders"))
        else:
            formatter(get("/orders/" + cfg['user']))
    elif args.command == 'users':
        formatter(get_users())
