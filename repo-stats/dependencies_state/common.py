import json
import os
import re
import requests

from abc import ABC, abstractmethod

from subprocess import check_output
from email.parser import BytesHeaderParser

import email
import argparse
from tqdm import tqdm
import pandas as pd


class GetEnvDepData(ABC):
    relevant_django = ["1.11", "2.0", "2.1", "2.2"]
    relevant_python = ["2.7", "3.5", "3.6", "3.7", "3.8"]
    def __init__(self, default_json_file_path, default_csv_file_path):
        self.packages = {}
        self.default_json_file_path = default_json_file_path
        self.default_csv_file_path = default_csv_file_path
        self.data = []

    @abstractmethod
    def get(self, name, version=None):
        None

    @abstractmethod
    def get_packages_details(self):
        None


    def readLocalJsonData(self, file_path=None):
        if file_path is None:
            file_path = self.default_json_file_path
        with open(os.path.expanduser(file_path)) as json_file:
            self.packages = json.load(json_file)

    def saveRawJsonData(self, file_path=None):
        if file_path is None:
            file_path = self.default_json_file_path
        with open(os.path.expanduser(file_path), "w") as json_file:
            json.dump(self.packages, json_file)

    def saveCSVData(self, file_path=None):
        if file_path is None:
            file_path = self.default_csv_file_path
        info_dataframe = pd.DataFrame(data=self.data, columns=self.columns)
        info_dataframe.to_csv(file_path)


    def createColumnName(self, name, version):
        return f"{name}: {version}"

    @property
    def columns(self):
        columns = ["Name", "Author", "Version"]
        for version in self.relevant_python:
            columns.append(self.createColumnName("Python", version))
        for version in self.relevant_django:
            columns.append(self.createColumnName("Django", version))

        return columns

    @property
    def columns_index_dict(self):
        return {key: index for index, key in enumerate(self.columns)}
    

    def create_data(self, parsed_details):
        """
        parsed_details: dict with various nesting that has info 
        This function converts dict to array
        """
        output = []
        for key in self.columns_index_dict:
            output.append(None)
        if "Name" in list(parsed_details.keys()):
            output[self.columns_index_dict["Name"]] = parsed_details["Name"]
        if "Author" in list(parsed_details.keys()):
            output[self.columns_index_dict["Author"]] = parsed_details["Author"]
        if "Version" in list(parsed_details.keys()):
            output[self.columns_index_dict["Version"]] = parsed_details["Version"]
        if "Python" in list(parsed_details.keys()):
            for version in self.relevant_python:
                name = self.createColumnName("Python", version)
                output[self.columns_index_dict[name]] = False
                if "Python" in parsed_details:
                    if version in parsed_details["Python"]:
                        output[self.columns_index_dict[name]] = True
        if "Django" in list(parsed_details.keys()):
            for version in self.relevant_django:
                name = self.createColumnName("Django", version)
                output[self.columns_index_dict[name]] = False
                if "Django" in parsed_details:
                    if version in parsed_details["Django"]:
                        output[self.columns_index_dict[name]] = True
        return output


    def capitalize_key_names(self, dictionary):
        """Returns a new dict that has all the key names capitalized"""
        new_dict = {}
        for key in dictionary:
            new_dict[key.capitalize()] = dictionary[key]
        return new_dict


    def get_list_dependencies(self):
        """
        Returns list of dictionaries: [{"version": "", "name": ""}]
        """
        with open(os.devnull, "w") as devnull:
            pip_list = check_output(
                ["pip", "list","--format", "json"], stderr=devnull, universal_newlines=True
            )
            packages_temp = json.loads(pip_list)
            packages = {}
            for package in packages_temp:
                package = self.capitalize_key_names(package)
                packages[package["Name"]] = package
            self.packages = packages
            return packages
        return {}

    def parse_classifier_for_version(self, classifier, name):
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
        versions = []
        for line in classifier:
            if name in line:
                nums = re.findall(r"\d+\.\d+", line)
                if len(nums) == 0:
                    nums = re.findall(r"\d", line)
                if len(nums) > 0:
                    versions.append(nums[0])
                else:
                    versions.append("?")
        return versions

    def test_serializability(self, dict_input):
        """tests to see if dict input is serializable into json"""
        with open(os.devnull, "w") as devnull:
            try:
                json.dump(dict_input, devnull)
            except:
                return False
            return True
    def convert_from_dict_to_defined_array(self):
        """
        packages= ={package name: {name:value, version: value, details: value}}
        the function parses through details for each package and outputs in data structure created
        at top of file
        """
        packages = self.packages
        data = []
        for package_name in tqdm(packages):
            data.append(self.create_data(packages[package_name]))
        self.data = data
        return data
