from __future__ import absolute_import, print_function, unicode_literals

import json
import os
import re
import pdb
import requests

from subprocess import check_output
from email.parser import BytesHeaderParser

import email
import pprint
import argparse
from tqdm import tqdm


from common import GetEnvDepData



class CurrentState(GetEnvDepData):
    def __init__(self):
        default_json_file_path = "current_env_details.json"
        default_csv_file_path = "current_env_data.csv"
        super(CurrentState, self).__init__(default_json_file_path, default_csv_file_path)


    def get(self, name, version=None):
        """return a dictionary with pypi project data"""
        with open(os.devnull, "w") as devnull:
            details = check_output(
                ["pip", "show", "--verbose", name],
                stderr=devnull,
                universal_newlines=True,
            )
            return self.parse_details_string(details)
        return {}

    def parse_details_string(self, detail_string):
        """pip show --verbose returns a string with details on package
        string is formated to be readable by BytesHeaderParser
        this function takes a detail string and tries to parse as much data out of it as is possible
        """
        final_details = detail_string
        parsable_details = BytesHeaderParser().parsebytes(final_details.encode())
        temp_dict = dict(parsable_details.items())
        if not self.test_serializability(temp_dict):
            # something in dict is not serializable, figure it out
            for key in temp_dict:
                if not self.test_serializability({key: temp_dict[key]}):
                    if isinstance(temp_dict[key], email.header.Header):
                        temp_dict[key] = str(temp_dict[key])
                    else:
                        raise ValueError(
                            "Value not default serializable, please use pdb.set_trace to investigate"
                        )

        # parse info from classifier
        temp_dict["Python"] = self.parse_classifier_for_version(
            temp_dict["Classifiers"].splitlines(), "Python"
        )
        temp_dict["Django"] = self.parse_classifier_for_version(
            temp_dict["Classifiers"].splitlines(), "Django"
        )
        # parse info from Requires
        temp_dict["Requires"] = [
            require.strip() for require in temp_dict["Requires"].split(",")
        ]
        final_details = temp_dict
        return final_details



    def get_packages_details(self):
        packages = self.packages
        for package_name in tqdm(packages):
            details = self.get(package_name)
            packages[package_name].update(details)
        self.packages = packages
        return packages
