import json
import os
import re
import requests

from subprocess import check_output
from email.parser import BytesHeaderParser
from importlib_metadata import metadata, requires, PackageNotFoundError
import email
import argparse
from tqdm import tqdm


from common import GetEnvDepData



class CurrentState(GetEnvDepData):
    def __init__(self):
        default_json_file_path = "current_env_details.json"
        default_csv_file_path = "current_env_data.csv"
        super().__init__(default_json_file_path, default_csv_file_path)


    def get(self, name, version=None):
        """return a dictionary with pypi project data"""
        try:
            md = metadata(name)
            return self.parse_metadata(md)
        except PackageNotFoundError:
            return self.getPipShow(name)

    def getPipShow(self, name, version=None):
        """return a dictionary with pypi project data"""
        with open(os.devnull, "w") as devnull:
            details = check_output(
                ["pip", "show", "--verbose", name],
                stderr=devnull,
                universal_newlines=True,
            )
            return self.parse_details_string(details)
        return {}

    def parse_metadata(self, metadata_input):
        """pip show --verbose returns a string with details on package
        string is formated to be readable by BytesHeaderParser
        this function takes a detail string and tries to parse as much data out of it as is possible
        """
        temp_dict = {}
        for key in set(metadata_input.keys()):
            temp_dict[key] = metadata_input.get_all(key)
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
        """
        the name of Classifiers key is diff for pip show and metadata from importlib_metadata
        This keeps the pip show naming
        """
        temp_dict["Classifiers"] = temp_dict["Classifier"]
        return self.parse_out_more_info(temp_dict)

    def parse_details_string(self, detail_string):
        """pip show --verbose returns a string with details on package
        string is formated to be readable by BytesHeaderParser
        this function takes a detail string and tries to parse as much data out of it as is possible
        """
        final_details = detail_string
        parsable_details = BytesHeaderParser().parsebytes(final_details.encode())
        temp_dict = dict(list(parsable_details.items()))
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
        temp_dict["Classifiers"] = temp_dict["Classifiers"].splitlines()
        return self.parse_out_more_info(temp_dict)

    def parse_out_more_info(self, details_dict):
        # parse info from classifier
        details_dict["Python"] = self.parse_classifier_for_version(
            details_dict["Classifiers"], "Python"
        )
        details_dict["Django"] = self.parse_classifier_for_version(
            details_dict["Classifiers"], "Django"
        )
        return details_dict

    def get_packages_details(self):
        packages = self.packages
        for package_name in tqdm(packages):
            details = self.get(package_name)
            packages[package_name].update(details)
        self.packages = packages
        return packages
