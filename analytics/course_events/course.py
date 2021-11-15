"""
 mainly for interpreting course data from MongoDB


"""

from pymongo import MongoClient
from dateutil import parser
from . import course_location

import copy

# A list of metadata that this module can inherit from its parent module
INHERITABLE_METADATA = (
    'graded', 'start', 'due', 'graceperiod', 'showanswer', 'rerandomize',
    # TODO (ichuang): used for Fall 2012 xqa server access
    'xqa_key', 'display_name',
    # How many days early to show a course element to beta testers (float)
    # intended to be set per-course, but can be overridden in for specific
    # elements.  Can be a float.
    'days_early_for_beta',
    'giturl'  # for git edit link
)

class CourseComponent():

      def __init__(self, name = 'None', location=None, level=0, children = [], date = None):
        '''
        Constructor
        '''
        self.name = name
        self.location = location
        self.level = level
        self.children = children
        self.start_date = date
        self.log_entries = []


class CourseStructure():
    '''
    General access to MongoDB
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.connection = MongoClient()
        self.level = 0
        self.components = []

    def _get_children(self, child, dbcursor, parent_component):

        self.level += 1
        level_indent = ''
        for result in dbcursor:
            location = course_location.Location(result['_id'])

            if location.url() == child:

                for n in range(0, self.level):
                    level_indent += '-'
                print('%s [%s]: %s' % (level_indent, location.category, result.get('metadata', {}).get('display_name', [])))
                print('%s Location %s' % (level_indent, location.url()))
                print('')

                children = result.get('definition', {}).get('children', [])
                component = CourseComponent(result.get('metadata', {}).get('display_name', []), location, self.level, [])
                parent_component.children.append(component)
                for next_child in children:
                    self._get_children(next_child, dbcursor.clone(), component)

                self.level -= 1


    def course_components(self, org, course_id):
        '''

        for a course_id, course_name, org build up:
          chapters (Section)
          sequential (subsections)
          vertical (unit)
          component (component)

        Parameters
        -----------
        org: org name
        course_id: id of course

        '''

        db = self.connection.xmodule
        collection = db.modulestore

        query = {'_id.org': org,
                     '_id.course': course_id,
                     '_id.category': {'$in': ['course', 'chapter', 'sequential', 'vertical',
                                              'wrapper', 'problemset', 'conditional', 'randomize', 'html', 'video', 'discussion','problem']}
                     }

        record_filter = {'_id': 1, 'definition.children': 1}

        for attr in INHERITABLE_METADATA:
            record_filter[f'metadata.{attr}'] = 1


        resultset = collection.find(query, record_filter)

        chapters = list()

        for result in resultset:
            location = course_location.Location(result['_id'])

            if location.category == 'course':
                print('[Course]: %s' % location.name)
                start = parser.parse(result.get('metadata', {}).get('start', []))
                print('Start Date: %s' % start.strftime('%m/%d/%Y %H:%M'))

                component = CourseComponent(location.name, location, self.level, None, start)
                self.components.append(component)


            if location.category == 'chapter':
                chapters.append(result)
                print('[Chapter]: %s' % result.get('metadata', {}).get('display_name', []))
                print('Location %s' % location.url())

                children = result.get('definition', {}).get('children', [])

                component = CourseComponent(result.get('metadata', {}).get('display_name', []), location, self.level, [],None)
                self.components.append(component)

                for nextchild in children:
                    self._get_children(nextchild, resultset.clone(), component)

        return self.components






