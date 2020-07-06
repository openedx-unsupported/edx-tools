"""
 Handles identifiers and urls for event locations


"""

from __future__ import absolute_import
import re
from collections import namedtuple
import six

URL_RE = re.compile("""
    (?P<tag>[^:]+)://
    (?P<org>[^/]+)/
    (?P<template>[^/]+)/
    (?P<category>[^/]+)/
    (?P<display_name>[^@]+)?
    """, re.VERBOSE)

MISSING_SLASH_URL_RE = re.compile("""
    (?P<tag>[^:]+):/
    (?P<org>[^/]+)/
    (?P<template>[^/]+)/
    (?P<category>[^/]+)/
    (?P<display_name>[^@]+)?
    """, re.VERBOSE)

# TODO (cpennington): We should decide whether we want to expand the
# list of valid characters in a location
INVALID_CHARS = re.compile(r"[^\w.-]")
# Names are allowed to have colons.
INVALID_CHARS_NAME = re.compile(r"[^\w.:-]")

# html ids can contain word chars and dashes
INVALID_HTML_CHARS = re.compile(r"[^\w-]")

_LocationBase = namedtuple('LocationBase', 'tag org template category display_name')


class TemplateLocation(_LocationBase):
    '''
    Encodes a location.

    Locations representations of URLs of the
    form {tag}://{org}/{template}/{category}/{name}[@{revision}]

    However, they can also be represented a dictionaries (specifying each component),
    tuples or list (specified in order), or as strings of the url
    '''
    __slots__ = ()

    @staticmethod
    def _clean(value, invalid):
        """
        invalid should be a compiled regexp of chars to replace with '_'
        """
        return re.sub('_+', '_', invalid.sub('_', value))

    @staticmethod
    def clean(value):
        """
        Return value, made into a form legal for locations
        """
        return TemplateLocation._clean(value, INVALID_CHARS)

    @staticmethod
    def clean_keeping_underscores(value):
        """
        Return value, replacing INVALID_CHARS, but not collapsing multiple '_' chars.
        This for cleaning asset names, as the YouTube ID's may have underscores in them, and we need the
        transcript asset name to match. In the future we may want to change the behavior of _clean.
        """
        return INVALID_CHARS.sub('_', value)

    @staticmethod
    def clean_for_url_name(value):
        """
        Convert value into a format valid for location names (allows colons).
        """
        return TemplateLocation._clean(value, INVALID_CHARS_NAME)

    @staticmethod
    def clean_for_html(value):
        """
        Convert a string into a form that's safe for use in html ids, classes, urls, etc.
        Replaces all INVALID_HTML_CHARS with '_', collapses multiple '_' chars
        """
        return TemplateLocation._clean(value, INVALID_HTML_CHARS)

    @staticmethod
    def is_valid(value):
        '''
        Check if the value is a valid location, in any acceptable format.
        '''
        try:
            TemplateLocation(value)
        except InvalidLocationError:
            return False
        return True

    @staticmethod
    def ensure_fully_specified(location):
        '''Make sure location is valid, and fully specified.  Raises
        InvalidLocationError or InsufficientSpecificationError if not.

        returns a Location object corresponding to location.
        '''
        loc = TemplateLocation(location)
        for key, val in six.iteritems(loc.dict()):
            if key != 'revision' and val is None:
                raise InsufficientSpecificationError(location)
        return loc

    def __new__(_cls, loc_or_tag=None, org=None, template=None, category=None,
                display_name=None):
        """
        Create a new location that is a clone of the specifed one.

        location - Can be any of the following types:
            string: should be of the form
                    {tag}://{org}/template/{category}/display_name]

            list: should be of the form [tag, org, template, category, name, revision]

            dict: should be of the form {
                'tag': tag,
                'org': org,
                'template': template,
                'category': category,
                'display_name': display_name
            }
            TemplateLocation: another TemplateLocation object

        In both the dict and list forms, the revision is optional, and can be
        ommitted.

        Components must be composed of alphanumeric characters, or the
        characters '_', '-', and '.'.  The name component is additionally allowed to have ':',
        which is terpreted specially for xml storage.

        Components may be set to None, which may be interpreted in some contexts
        to mean wildcard selection.
        """

        if (org is None and template is None and category is None and display_name is None ):
            location = loc_or_tag
        else:
            location = (loc_or_tag, org, template, category, display_name)

        if location is None:
            return _LocationBase.__new__(_cls, *([None] * 5))

        def check_dict(dict_):
            # Order matters, so flatten out into a list
            keys = ['tag', 'org', 'template', 'category', 'display_name']
            list_ = [dict_[k] for k in keys]
            check_list(list_)

        def check_list(list_):
            def check(val, regexp):
                if val is not None and regexp.search(val) is not None:
                    log.debug('invalid characters val="%s", list_="%s"' % (val, list_))
                    raise InvalidLocationError("Invalid characters in '%s'." % (val))

            list_ = list(list_)
            for val in list_[:4] + [list_[4]]:
                check(val, INVALID_CHARS)
            # names allow colons
            check(list_[4], INVALID_CHARS_NAME)

        if isinstance(location, six.string_types):
            match = URL_RE.match(location)
            if match is None:
                # cdodge:
                # check for a dropped slash near the i4x:// element of the location string. This can happen with some
                # redirects (e.g. edx.org -> www.edx.org which I think happens in Nginx)
                match = MISSING_SLASH_URL_RE.match(location)
                if match is None:
                    log.debug('location is instance of %s but no URL match' % six.string_types)
                    raise InvalidLocationError(location)
            groups = match.groupdict()
            check_dict(groups)
            return _LocationBase.__new__(_cls, **groups)
        elif isinstance(location, (list, tuple)):
            args = tuple(location)

            check_list(args)
            return _LocationBase.__new__(_cls, *args)
        elif isinstance(location, dict):
            kwargs = dict(location)
            kwargs.setdefault('revision', None)

            check_dict(kwargs)
            return _LocationBase.__new__(_cls, **kwargs)
        elif isinstance(location, Location):
            return _LocationBase.__new__(_cls, location)
        else:
            raise InvalidLocationError(location)

    def url(self):
        """
        Return a string containing the URL for this location
        """
        url = "{tag}://{org}/{template}/{category}/{display_name}".format(**self.dict())
        return url

    def html_id(self):
        """
        Return a string with a version of the location that is safe for use in
        html id attributes
        """
        s = "-".join(str(v) for v in self.list()
                     if v is not None)
        return TemplateLocation.clean_for_html(s)

    def dict(self):
        """
        Return an OrderedDict of this locations keys and values. The order is
        tag, org, template, category, name, revision
        """
        return self._asdict()

    def list(self):
        return list(self)

    def __str__(self):
        return self.url()

    def __repr__(self):
        return "TemplateLocation%s" % repr(tuple(self))

    @property
    def template_id(self):
        """Return the ID of the template that this item belongs to by looking
        at the location URL hierachy"""
        return "/".join([self.org, self.template, self.name])

    def replace(self, **kwargs):
        '''
        Expose a public method for replacing location elements
        '''
        return self._replace(**kwargs)
