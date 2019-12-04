#!/usr/bin/env python
"""
Python script to output state of each dependency for a repo.

Currently only gets data from pip show for each dependency and outputs it in csv file
"""
from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import re
import pdb
from subprocess import check_output
from email.parser import BytesHeaderParser
import email
import pandas as pd

from tqdm import tqdm
import pprint
import argparse

pp = pprint.PrettyPrinter(indent=4)



"""
The code below creates a single columns list with names of each of the data point indexes

For each dep, we want to know various info like: name, version, author ....
the code below makes sure there is single structure for it

It might be a good idea to somehow embed this info into data later on
"""
def createColumnName(name, version):
    return "{name}: {version}".format(name = name, version = version)

relevant_django = ["1.11", "2.0", "2.1", "2.2"]
relevant_python = ["2.7", "3.5", "3.6", "3.7", "3.8"]
columns = ["Name", "Author", "Version", "Home-page", "Requires"]
for version in relevant_python:
    columns.append(createColumnName("Python", version))
for version in relevant_django:
    columns.append(createColumnName("Django", version))

columns_index_dict = { key: index for index, key in enumerate(columns)}

def create_data(parsed_details):
    """
    parsed_details: dict with various nesting that has info 
    This function converts dict to array
    """
    output = []
    for key in columns_index_dict:
        output.append(None)
    output[columns_index_dict["Name"]] = parsed_details["Name"]
    output[columns_index_dict["Author"]] = parsed_details["Author"]
    output[columns_index_dict["Version"]] = parsed_details["Version"]
    output[columns_index_dict["Home-page"]] = parsed_details["Home-page"]
    output[columns_index_dict["Requires"]] = ", ".join(parsed_details["Requires"])
    for version in relevant_python:
        name = createColumnName("Python", version)
        output[columns_index_dict[name]] = False
        if "Python" in parsed_details:
            if version in parsed_details["Python"]:
                output[columns_index_dict[name]] = True

    for version in relevant_django:
        name = createColumnName("Django", version)
        output[columns_index_dict[name]] = False
        if "Django" in parsed_details:
            if version in parsed_details["Django"]:
                output[columns_index_dict[name]] = True
    return output

def capitalize_key_names(dictionary):
    """Returns a new dict that has all the key names capitalized"""
    new_dict = {}
    for key in dictionary:
        new_dict[key.capitalize()] = dictionary[key]
    return new_dict


def get_list_dependencies():
    """
    Returns list of dictionaries: [{"version": "", "name": ""}]
    """
    with open(os.devnull, 'w') as devnull:
        pip_list = check_output(['pip', 'list', '--format', 'json'],
                                stderr=devnull, universal_newlines=True)
        packages_temp = json.loads(pip_list)
        packages = {}
        for package in packages_temp:
            package = capitalize_key_names(package)
            packages[package["Name"]]=package
        return packages


def get_package_details_str(package_name, try_parsing = True):
    """
    runs pip show for given package and returns string with all the output
    """
    with open(os.devnull, 'w') as devnull:
        details = check_output(['pip', 'show', '--verbose', package_name],
                               stderr=devnull, universal_newlines=True)
        return details


def parse_details_string(detail_string):
    """pip show --verbose returns a string with details on package
    string is formated to be readable by BytesHeaderParser
    this function takes a detail string and tries to parse as much data out of it as is possible
    """
    final_details = detail_string
    parsable_details = BytesHeaderParser().parsebytes(final_details.encode())
    temp_dict = dict(parsable_details.items())
    if not test_serializability(temp_dict):
        #something in dict is not serializable, figure it out
        for key in temp_dict:
            if not test_serializability({key: temp_dict[key]}):
                if isinstance(temp_dict[key], email.header.Header):
                    temp_dict[key] = str(temp_dict[key])
                else:
                    raise ValueError("Value not default serializable, please use pdb.set_trace to investigate")

    #parse info from classifier
    temp_dict["Python"] = parse_classifier_for_version(temp_dict["Classifiers"], "Python")
    temp_dict["Django"] = parse_classifier_for_version(temp_dict["Classifiers"], "Django")
    # parse info from Requires
    temp_dict["Requires"] = [require.strip() for require in temp_dict["Requires"].split(",")]
    final_details = temp_dict
    return final_details

def parse_classifier_for_version(classifier, name):
    """
    classfiers are usually formated somewhat like this:
        Development Status :: 5 - Production/Stable
        Intended Audience :: Developers
        Topic :: System :: Archiving :: Packaging
        License :: OSI Approved :: MIT License
        Programming Language :: Python :: 3.8

    this function is designed to parse out version number for name input in the classifier.
    In case of name==Python, this function would find output ['3.8'] for example above
    """
    lines = classifier.splitlines()
    versions = []
    for line in lines:
        if name in line:
            nums = re.findall("\d+\.\d+", line)
            if len(nums)==0:
                nums = re.findall("\d", line)
            if len(nums)>0:
                versions.append(nums[0])
            else:
                versions.append("?")
    return versions


def test_serializability(dict_input):
    """tests to see if dict input is serializable into json"""
    with open(os.devnull, 'w') as devnull:
        try:
            json.dump(dict_input, devnull)
        except:
            return False
        return True


def get_packages_details():
    """
    The function will call pip list to get list of all dependencies installed in env.
    For each dependency, it will call pip show --verbose dependency and save returned string in packages
    returns packages dict={package name: {name:value, version: value, details: value}}
    """
    packages = get_list_dependencies()
    for package_name in tqdm(packages):
        details_str = get_package_details_str(package_name)
        packages[package_name]["details"] = details_str
    return packages


def parsing_out_info(packages):
    """
    packages= ={package name: {name:value, version: value, details: value}}
    the function parses through details for each package and outputs in data structure created
    at top of file
    """
    data = []
    for package_name in tqdm(packages):
        details_str = packages[package_name]["details"]
        parsed_details = parse_details_string(details_str)
        packages[package_name].update(parsed_details)
        data.append(create_data(packages[package_name]))
    return data



parser = argparse.ArgumentParser(
    description="Currently designed to output django and python state for dependecies installed in env"
)
parser.add_argument("--read_data_from_file", default=None)
parser.add_argument("--save_raw_data", default=None)
parser.add_argument("--csv_path", default="data.csv")
args = parser.parse_args()

packages = {}
if args.read_data_from_file is None:
    packages = get_packages_details()
    if args.save_raw_data is not None:
        with open(os.path.expanduser(args.save_raw_data),"w") as json_file:
            json.dump(packages, json_file)
else:
    with open(os.path.expanduser(args.read_data_from_file),"r") as json_file:
        packages = json.load(json_file)

data = parsing_out_info(packages)
info_dataframe = pd.DataFrame(data = data, columns=columns)
info_dataframe.to_csv(os.path.expanduser(args.csv_path))
        