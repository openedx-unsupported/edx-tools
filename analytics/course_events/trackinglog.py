"""
 utility to parse tracking logs and output event information related to course editing


"""


import json
from dateutil import parser
import codecs
from . import template_location, course_location, course

EVENT_TYPE = ['/create_new_course', '/clone_item', '/save_item', '/publish_draft', '/create_draft', '/delete_item']

class CourseEvents():

    def __init__(self, org, course, logfile, outfile):

        self.org = org
        self.course = course
        self.logfile = open(logfile, 'r')
        self.outfile = codecs.open(outfile, 'w', 'latin-1', 'replace')


    def _dump_course_tree(self, component):

        level_indent = ''
        for n in range(0, component.level):
            level_indent += '\t'

        out = '%s%s\t%s\t%s\n' % (level_indent, component.location.category, component.name, component.location.url())
        self.outfile.write(out)

        if component.children is not None and len(component.children) > 0:
            for child_component in component.children:
                self._dump_course_tree(child_component)

        return


    def _dump_log_children(self, component):

        for log_entry in component.log_entries:
            self.outfile.write(log_entry)

        if component.children is not None and len(component.children) > 0:
            for child_component in component.children:
                self._dump_log_children(child_component)

        return

    def dump_out(self, course_components):

        for component in course_components:
            self._dump_course_tree(component)

        out = 'component\tname\tlocation\tevent\tuser\tdatetime\n'
        self.outfile.write(out)

        for component in course_components:
            self._dump_log_children(component)


    def _get_children(self, display_name, category, component):


        if component.location.category == category and component.name == display_name:
            return component
        elif component.children is not None and len(component.children) > 0:
            # return true if found
            for child_component in component.children:
                found_component = self._get_children(display_name, category, child_component)
                if found_component is not None:
                    return found_component


        return None

    def _get_children_by_id(self, location_id, component):


        if component.location.url() == location_id:
            return component
        elif component.children is not None and len(component.children) > 0:
            # return true if found
            for child_component in component.children:
                found_component = self._get_children_by_id(location_id, child_component)
                if found_component is not None:
                    return found_component


        return None



    def search_components(self, username, time, event_type, location, course_components):

        for component in course_components:
            if component.location.url() == location.url():
                out = '%s\t%s\t location\t%s \n' % (location.category, component.name, component.location.url())
                print out
                create = parser.parse(time)
                out = 'user:\t%s\tevent:\t%s\t DateTime:\t%s \n' % (username, event_type, create.strftime('%m/%d/%Y %H:%M'))
                print out
                log_entry = '%s\t%s\t%s\t%s\t%s\t%s \n' % (location.category, component.name, component.location.url(),
                        event_type,username,create.strftime('%m/%d/%Y %H:%M'))
                component.log_entries.append(log_entry)

                update_course_event(component,username,event_type,create)

                break
            elif component.children is not None and len(component.children) > 0:
                # return true if found
                for child in component.children:
                    child_component = self._get_children_by_id(location.url(), child)
                    if child_component is not None:
                        out = '%s\t%s\t location:\t%s \n' % (location.category, child_component.name, child_component.location.url())
                        print out
                        create = parser.parse(time)
                        out = 'user:\t%s\tevent:\t%s\tDate Time:\t%s \n' % (username, event_type, create.strftime('%m/%d/%Y %H:%M'))
                        print out
                        log_entry = '%s\t%s\t%s\t%s\t%s\t%s \n' % (location.category, child_component.name, child_component.location.url(),
                        event_type,username,create.strftime('%m/%d/%Y %H:%M'))
                        component.log_entries.append(log_entry)


                        break

                if child_component is not None:
                    break


    def parse(self, course_components):


        for line in self.logfile:
            try:
                elements = json.loads(line)
            except:
                continue

            # we are looking for particular events
            # /create_new_course
            # /clone_item : item is in the Templatelocation of the Event
            # /edit/<Location>
            # /save_item
            # /publish_draft
            # /create_draft
            # /delete_item

            event_type = elements['event_type']

            # if not an event of interest: continue
            if event_type is None or (event_type not in EVENT_TYPE and event_type.find('/edit/') != 0):
                continue


            # get all details

            username = elements['username']
            event = elements['event']
            host = elements['host']
            event_source = elements['event_source']
            time = elements['time']
            ip = elements['ip']
            agent = elements['agent']
            page = elements['page']

            # get target
            # Template Location items: /create_new_course, /clone_item
            # Course Location items: /create_draft, /delete_item, /save_item, /clone_item (for parent)

            if event_type == '/create_new_course':
                post = json.loads(event)['POST']
                org = post['org']
                name = post['display_name']
                number = post['number']

                for component in course_components:
                    if component.location.category == 'course' and component.name == name[0]:
                        out = 'course:\t %s\t start_date:\t%s\t location:\t%s \n' % (name[0], component.start_date.strftime('%m/%d/%Y %H:%M'), component.location.url())
                        print out
                        create = parser.parse(time)
                        out = 'user:\t %s \t event:\t created \t Date Time: \t %s \n' % (username, create.strftime('%m/%d/%Y %H:%M'))
                        print out
                        break
            elif event_type == '/clone_item':
                post = json.loads(event)['POST']
                parent_locations = post['parent_location']
                template = post['template']

                parent_location = course_location.Location(parent_locations[0])

                if parent_location.org != self.org and parent_location.course != self.course:
                    continue

                location = template_location.TemplateLocation(template[0])

                display_name = ''
                if location.category in ['vertical', 'sequential', 'chapter']:
                    display_names = post['display_name']
                    display_name = display_names[0]
                else:
                    display_name = location.display_name
                    # display_name may have _ substituted for spaces only in template names
                    display_name = display_name.replace('_',' ')

                for component in course_components:
                    if component.location.category == location.category and component.name == display_name:
                        out = '%s\t%s\t location\t%s \n' % (location.category, display_name, component.location.url())
                        print out
                        create = parser.parse(time)
                        out = 'user:\t%s\tevent:\tcreate\t Date Time\t%s \n' % (username, create.strftime('%m/%d/%Y %H:%M'))
                        print out
                        log_entry = '%s\t%s\t%s\t%s\t%s\t%s \n' % (location.category, display_name, component.location.url(),
                        'clone_item',username,create.strftime('%m/%d/%Y %H:%M'))
                        component.log_entries.append(log_entry)
                        break
                    elif component.children is not None and len(component.children) > 0:
                        # return true if found
                        for child in component.children:
                            child_component = self._get_children(display_name, location.category, child)
                            if child_component is not None:
                                out = '%s\t%s\t location:\t%s \n' % (location.category, display_name, child_component.location.url())
                                print out
                                create = parser.parse(time)
                                out = 'user:\t%s\tevent:\tcreate\tDate  Time:\t%s \n' % (username, create.strftime('%m/%d/%Y %H:%M'))
                                print out
                                log_entry = '%s\t%s\t%s\t%s\t%s\t%s \n' % (location.category, child_component.name, child_component.location.url(),
                                                                        'clone_item',username,create.strftime('%m/%d/%Y %H:%M'))
                                component.log_entries.append(log_entry)
                                break

                        if child_component is not None:
                            break
            elif event_type == '/save_item':

                # The POST may be longer than the log allows and so loses the closing braces
                # so easier just to substring out the location id

                start = event.find('i4x:')
                end = event.find('"',start)
                location_id = event[start:end-1]

                location = course_location.Location(location_id)

                if location.org != self.org and location.course != self.course:
                    continue

                self.search_components(username,time, 'save_item', location, course_components)


            elif event_type == '/publish_draft' or event_type == '/create_draft':

                post = json.loads(event)['POST']
                location_id = post['id']

                location = course_location.Location(location_id[0])

                if location.org != self.org and location.course != self.course:
                    continue

                self.search_components(username,time, event_type[1:], location, course_components)

            elif event_type.find('/edit/') != 0:

                # The POST may be longer than the log allows and so loses the closing braces
                # so easier just to substring out the location id

                start = event.find('i4x:')
                end = event.find('"',start)
                location_id = event[start:end]

                location = course_location.Location(location_id)

                if location.org != self.org and location.course != self.course:
                    continue

                self.search_components(username,time, 'edit', location, course_components)


        return course_components




