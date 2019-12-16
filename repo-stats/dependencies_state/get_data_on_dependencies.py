#!/usr/bin/env python
"""
Python script to output state of each dependency for a repo.

Currently only gets data from pip show for each dependency and outputs it in csv file
"""

import argparse
from latest_state import LatestState
from current_state import CurrentState


def auto_get_data(arguments):
    """
    use this function for the first time you are in a given env, this will get info on all packages installed
    and on all the latest packages avaible
    """
    # arguments: Namespace(auto_script=False, csv_path=None, latest=False, read_json_file=None, reget_data=False, save_raw_data=None)
    arguments.csv_path = None
    arguments.latest = False
    arguments.read_json_file = None
    arguments.reget_data = False
    arguments.save_raw_data = None

    get_data_on_packages(arguments)
    arguments.latest = True
    get_data_on_packages(arguments)


def get_data_on_packages(arguments):
    if arguments.latest:
        state_getter = LatestState()
    else:
        state_getter = CurrentState()

    packages = {}
    #Either read data from local file or get from sh command
    if arguments.read_json_file:
        print("reading data from file")
        if arguments.read_json_file == True:
            state_getter.readLocalJsonData()
        else:
            state_getter.readLocalJsonData(arguments.read_json_file)
    else:
        print("Getting new data")
        packages = state_getter.get_list_dependencies()
        packages = state_getter.get_packages_details()
    print("Saving data")
    # save all json data, cause our defined array(below) is subset of stuff
    #(so in case something goes wrong in conversion below, the data can just be read from file)
    state_getter.saveRawJsonData(arguments.save_json_file)
    print("Converting data")
    final_data = state_getter.convert_from_dict_to_defined_array()
    print("Saving CSV")
    state_getter.saveCSVData(arguments.csv_path)


parser = argparse.ArgumentParser(
    description="Currently designed to output django and python state for dependecies installed in env"
)
parser.add_argument("--read_json_file", nargs='?', default=False, const=True)
parser.add_argument("--save_json_file", default=None)
parser.add_argument("--csv_path", default=None)
parser.add_argument("--latest", nargs='?', default=False, const=True)
parser.add_argument("--auto_script", default=False)
args = parser.parse_args()

if args.auto_script:
    auto_get_data(args)
else:
    get_data_on_packages(args)

