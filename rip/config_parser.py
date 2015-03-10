import configparser
import re
import sys

"""
Author: Carl Kenny
Date:   10/03/2015
Prog:   Parses router config (.ini) and provides basic error checking
"""


def parse_config(config):
    """
    :param config: ConfigParser() object
    :return dict: Contains: router-id, input-ports and outputs
    """
    config_dict = {}

    router_id = int(config['ROUTER']['router-id'])

    if 1 <= router_id < 64000:
        config_dict['router-id'] = router_id
    else:
        return None

    ports = set()
    ports_split = config['ROUTER']['input-ports'].split(',')
    port_count = len(ports_split)

    for port in ports_split:
        port = int(port)
        if 1024 <= port <= 64000:
            ports.add(port)
        else:
            return None

    config_dict['input-ports'] = ports
    output_split = config['ROUTER']['outputs'].split(',')
    outputs = []

    for output in output_split:
        re_result = re.search("(.*)-(.)-(.)", output).groups()
        output_port, metric, router_id  = [int(i) for i in re_result]
        if 1024 <= output_port <= 64000 and output_port not in config_dict['input-ports']:
            outputs.append([output_port, metric, router_id])
        else:
            return None

    config_dict['outputs'] = outputs

    return config_dict if port_count == len(ports) else None


def main():
    if len(sys.argv) < 2:
        sys.exit("No file given")

    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    config_dict = parse_config(config)

    if not config_dict:
        sys.exit("Invalid config file. Exiting...")
    print("Config_dict: ", config_dict)

if __name__ == "__main__":
    main()

