#!/usr/bin/env python3

from lark import Lark, Transformer, v_args
import argparse
import json


class ISC_Transformer(Transformer):
    hosts = []
    '''
        host [name] {                              => pair
            hardware ethernet [hwaddr] ;           => option
            fixed-address [addr] ;                 => pair
        }

        KEY VALUE "{"                              => pair
            hardware KEY VALUE ("," VALUE)* ";"    => option
            KEY VALUE ("," VALUE)* ";"             => pair
        "}"
    '''
    @v_args(inline=True)
    def nested_line(self, line, *statements):
        child = line.children[0]

        if child.data == "pair":
            node = {'name': None, 'addr': None, 'hwaddr': None}

            host, name = child.children
            node['name'] = name.value

            for s in statements:
                addrs = list(s.find_pred(lambda v: v.data == "pair"))
                if addrs:
                    anon, addr = addrs[0].children
                    node['addr'] = addr.value

                ethers = list(s.find_pred(lambda v: v.data == "option"))
                if ethers:
                    anon, hwaddr = ethers[0].children
                    node['hwaddr'] = str.upper(hwaddr.value)

            self.hosts.append(node)


def main():
    '''
        argument parser
    '''
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-f", "--file", help="ISC config file.")
    args = argparser.parse_args()
    '''
        ISC config grammar
    '''
    transformer = ISC_Transformer()
    parser = Lark('''
            start : statement*
        statement : comment
                  | single_line
                  | nested_line
      single_line : line ";"
      nested_line : line "{" statement* "}"
          comment : SH_COMMENT
             line : option
                  | pair
                  | pair2
                  | single
                  | range
           option : ( "option" | "hardware" ) KEY VALUE ("," VALUE)*
             pair : KEY VALUE
            pair2 : "subnet" VALUE "netmask" VALUE
           single : ( "pool" | "group" )
            range : "range" VALUE VALUE
            VALUE : ESCAPED_STRING
                  | TOKEN
              KEY : /[a-zA-Z][\d\w\-\_]*/
            TOKEN : /[0-9a-zA-Z\.:_]+/

        %import common.SH_COMMENT
        %import common.ESCAPED_STRING
        %import common.WS
        %ignore WS
    ''',
                  parser="lalr",
                  transformer=transformer)

    conf = ""
    with open(args.file) as f:
        conf = f.read()

    parser.parse(conf)
    print(json.dumps(transformer.hosts))


if __name__ == '__main__':
    main()
