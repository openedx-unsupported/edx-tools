#!/usr/bin/python

# WARNING: This script isn't fast and doesn't write anything to disk.

from collections import defaultdict
import six.moves.http_cookiejar
import getpass
import json
import time
import six.moves.urllib.request, six.moves.urllib.error, six.moves.urllib.parse
import six

class CourseStructureBrowser:
    def __init__(self):
        self.cookie_jar = six.moves.http_cookiejar.CookieJar()
        self.url_opener = six.moves.urllib.request.build_opener(
                six.moves.urllib.request.HTTPCookieProcessor(self.cookie_jar))
    def login(self, username, password):
        self.url_opener.open("https://courses.edx.org/login").read()
        self.url_opener.addheaders = [
                ("referer", "https://courses.edx.org/login"),
                ("X-CSRFToken",
                    self.cookie_jar._cookies
                        ['courses.edx.org']['/']['csrftoken'].value)]
        self.url_opener.open(
                "https://courses.edx.org/user_api/v1/account/login_session/",
                data='email=%s&password=%s&remember=false' %
                    (six.moves.urllib.parse.quote(username),
                    six.moves.urllib.parse.quote(password)))
    def grab_all_courses(self, pageLimit = None):
        courses = []
        jj = {'next': 'https://courses.edx.org/api/course_structure/v0/courses/?format=json'}
        page = 0
        while jj['next'] is not None:
            if pageLimit and pageLimit <= page:
                break
            page += 1
            print("Grabbing", jj['next'])
            data = None
            while data is None:
                try:
                    data = self.url_opener.open(jj['next']).read()
                except six.moves.urllib.error.HTTPError:
                    print("Error... sleeping.")
                    time.sleep(5)
            jj = json.loads(data)
            data = " ".join(data.split("\n"))
            courses += jj['results']
        return courses
    def grab_course_structure(self, course_ids):
        course_structure = {}
        for course_id in course_ids:
            cs_uri = "https://courses.edx.org/api/course_structure/v0/course_structures/%s" % course_id
            print("Grabbing", cs_uri)

            data = None
            failure_count = 0
            while failure_count < 5:
                try:
                    course_structure[course_id] = \
                        self.url_opener.open(cs_uri).read()
                    break
                except six.moves.urllib.error.HTTPError as e:
                    print("Error %s... sleeping." % e)
                    failure_count += 1
                    time.sleep(5)
        return course_structure
    def parse_course_json(self, course_json):
        def collectNodes(nodeList, root):
            rvalue = {root}
            for child in nodeList[root]['children']:
                rvalue.update(collectNodes(nodeList, child))
            return rvalue

        course_tree = json.loads(course_json)
        orphans = set(course_tree['blocks'].keys()).difference( \
            collectNodes(course_tree['blocks'], course_tree['root']))
        assert(len(orphans) == 0)

        return course_tree

if __name__ == '__main__':
    username = input("edx username: ")
    password = getpass.getpass()

    csb = CourseStructureBrowser()
    csb.login(username, password)
    courses = csb.grab_all_courses()
    
    course_trees = {course_id: csb.parse_course_json(course_json) for
            (course_id, course_json) in
            csb.grab_course_structure([course['id'] for course in courses]).items()}

    total_count = defaultdict(lambda: 0)
    for course_id in course_trees:
        count = defaultdict(lambda: 0)
        for block in course_trees[course_id]['blocks'].values():
            count[block['type']] += 1
            total_count[block['type']] += 1
        print("Stats for course %s" % course_id)
        for block in count:
            print("    %8d %s" % (count[block], block))
        print()
    print("Totals")
    for block in total_count:
        print("    %8d %s" % (total_count[block], block))
