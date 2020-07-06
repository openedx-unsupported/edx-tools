from __future__ import absolute_import
__author__ = 'dglance'
"""
 course_tree_events: Prints out tsv of course structure and associated events.
                       Uses MongoDB for course structure and tracking log for events.


"""
import argparse

from course_events import trackinglog,course

description  = 'Prints out tsv of course structure and associated events./n'
description += ' uses MongoDB for course structure and tracking log for events'

parser = argparse.ArgumentParser(description=description)

parser.add_argument('--org', dest='org', help='organisation name')
parser.add_argument('--course', dest='course', help='course name')
parser.add_argument('--log', dest='log', help='log path')
parser.add_argument('--out', dest='outfile', help='tsv output file name')


args = parser.parse_args()

course_tree = course.CourseStructure()

course_components = course_tree.course_components(args.org,args.course)

course_events = trackinglog.CourseEvents(args.org,args.course,args.log, args.outfile)

course_components = course_events.parse(course_components)

course_events.dump_out(course_components)



