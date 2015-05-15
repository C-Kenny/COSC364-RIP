import config_parser
import configparser
import sys
from router import Router


def main():
    if len(sys.argv) < 2:
        sys.exit("No file given")

    # closes file when done, file like object
    with open(sys.argv[1]) as fp:
        config = configparser.ConfigParser()
        config.readfp(fp)
        config_dict = config_parser.parse_config(config)

        if not config_dict:
            sys.exit("Invalid config file. Exiting...")
        print("Loaded config file. Starting router...")
        x = Router(config_dict)

if __name__ == "__main__":
    main()
