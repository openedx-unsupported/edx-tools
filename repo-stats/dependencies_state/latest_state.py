import json
import os
import re
import requests

from subprocess import check_output
from email.parser import BytesHeaderParser

import email
import pprint
import argparse
from tqdm import tqdm
from common import GetEnvDepData



class LatestState(GetEnvDepData):
    def __init__(self):
        default_json_file_path = "fully_updated_env_details.json"
        default_csv_file_path = "fully_updated_env_data.csv"
        super().__init__(default_json_file_path, default_csv_file_path)


    def get(self, name, version=None):
        """return a dictionary with pypi project data"""
        url = "https://pypi.org/pypi/%s/json" % name
        if version:
            url = "https://pypi.org/pypi/%s/%s/json" % (name, version)
        r = requests.get(url)
        if r.status_code < 400:
            return r.json()
        else:
            print(f"request did not succeed: {name}")
        return {}


    def get_packages_details(self):
        packages = self.packages
        for package_name in tqdm(packages):
            details = self.get(package_name)
            if "info" in list(details.keys()):
                packages[package_name]["Author"] = details["info"]["author"]
                packages[package_name]["Classifiers"]=details["info"]["classifiers"]
                packages[package_name]["Version"]=details["info"]["version"]
                requires = details["info"]["requires_dist"]
                if requires is None:
                    requires = []
                packages[package_name]["Requires"]=requires
                # parse info from classifier
                packages[package_name]["Python"] = self.parse_classifier_for_version(
                    packages[package_name]["Classifiers"], "Python"
                )
                packages[package_name]["Django"] = self.parse_classifier_for_version(
                    packages[package_name]["Classifiers"], "Django"
                )
        return packages
