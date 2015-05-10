import config_parser
import configparser
import sys
from router import Router


def main():
    if len(sys.argv) < 2:
        sys.exit("No file given")

    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    config_dict = config_parser.parse_config(config)

    if not config_dict:
        sys.exit("Invalid config file. Exiting...")
    print("Config_dict: ", config_dict)
    print("Starting!")
    x = Router()

if __name__ == "__main__":
    main()