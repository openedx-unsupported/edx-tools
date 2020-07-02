#!/usr/bin/env python
"""
Takes a list of XML filenames. For each <video> tag it finds in the file it
will:

1) Check to see that the YouTube URL actually exists.
2) If there are multiple speeds specified, it will check that video lengths
   match what is expected from the speeds.
3) Inconsistencies like "0.75" vs. ".75"

A video tag looks like:

<video name="S1V1: Motivation for 6.002x" 
 youtube="1.5:q1xkuPsOY6Q,1.25:9WOY2dHz5i4,1.0:4rpg8Bq6hb4,0.75:KLim9Xkp7IY"/>

The name is optional

TODO:
* Check to see if something with different IDs has same content
* Get rid of the globals for warnings, errors

Encapsulation in this is a disaster because I ended up hacking on the summary
information and pre-fetching later on.
"""
from __future__ import absolute_import
from __future__ import print_function
from collections import namedtuple
from datetime import timedelta
from xml.etree import ElementTree
import argparse
import json
import logging
import re
import sys

import gdata.youtube
import gdata.youtube.service

from get_json_subs import get_json_subs

MARGIN = 2 # How many seconds off a video can be from the expected speed.

logging.basicConfig(format="%(levelname)-7s %(message)s")
log = logging.getLogger('data.video_test')

num_errors = 0
num_warnings = 0


class Video(namedtuple('Video', 'name speeds_to_ids filename')):

    def check(self, ids_to_videos):
        self._check_durations(ids_to_videos)
        self._check_conventions()

    def log_msg(self, msg, video_id=None):
        if video_id:
            video_text = "{0} ({1}) ".format(str(self.name), video_id)
        else:
            video_text = ""

        return self.filename + " - " + video_text + msg

    # Put in our own logging message wrappers here so that we don't have to keep
    # passing in the filename. But we should still pass in the video.
    def _check_durations(self, ids_to_videos):
        """Make sure the duration is what we expect it to be."""
        global num_errors
        global num_warnings
        try:
            youtube_id = self.speeds_to_ids["1.0"]
            if not youtube_id:
                raise ValueError("No YouTube ID for 1.0 speed: {0}"
                                 .format(self.speeds_to_ids))

            regular_version = ids_to_videos[youtube_id]
        except KeyError as err:
            log.error(self.log_msg("Video referenced in file does not exist!",
                                   video_id=youtube_id))
            num_errors += 1
            return
        except Exception as err:
            log.error(self.log_msg("Could not check durations", video_id=youtube_id))
            num_errors += 1
            log.exception(err)
            return

        regular_duration = int(regular_version.media.duration.seconds)
        for speed, youtube_id in sorted(self.speeds_to_ids.items()):
            if speed == "1.0":
                subtitles = get_json_subs(youtube_id, verbose=False)
                if not subtitles["text"]:
                    num_errors += 1
                    log.error(self.log_msg("Subtitle text missing", 
                                           video_id=youtube_id))
                elif not subtitles["start"]:
                    num_errors += 1
                    log.error(self.log_msg("Subtitle start times missing",
                                           video_id=youtube_id))
                elif not subtitles["end"]:
                    num_errors += 1
                    log.error(self.log_msg("Subtitle end times missing",
                                           video_id=youtube_id))
                continue

            try:
                version = ids_to_videos[youtube_id]
            except KeyError as err:
                log.error(self.log_msg("Video referenced in file does not exist!",
                                       video_id=youtube_id))
                num_errors += 1
                continue
            except gdata.service.RequestError as err:
                log.error(self.log_msg(str(err), video_id=youtube_id))
                num_errors += 1
                continue

            duration = int(version.media.duration.seconds)
            duration_td = timedelta(seconds=duration)
            expected_duration = round(regular_duration / float(speed))
            expected_duration_td = timedelta(seconds=expected_duration)

            if expected_duration - MARGIN <= duration <= expected_duration + MARGIN:
                msg = self.log_msg("{speed:4s} has duration {duration}",
                                   video_id=youtube_id)
                log.debug(msg.format(speed=speed, duration=duration_td))
            else:
                msg = self.log_msg("{speed:4s} has duration {duration} but " +
                                   "should be {expected_duration}",
                                   video_id=youtube_id)
                log.error(msg.format(speed=speed, 
                                     duration=duration_td, 
                                     expected_duration=expected_duration_td))
                num_errors += 1

    def _check_conventions(self):
        """Makes sure we specify speeds that are valid and helps to enforce
        consistency."""
        global num_errors
        global num_warnings

        GOOD_SPEEDS = {"0.75", "1.0", "1.25", "1.50"}
        OK_SPEEDS_TO_GOOD_SPEEDS = { ".75" : "0.75",
                                       "1" : "1.0",
                                     "1.5" : "1.50"}
        ACCEPTABLE_SPEEDS = GOOD_SPEEDS | set(OK_SPEEDS_TO_GOOD_SPEEDS)

        for speed, video_id in sorted(self.speeds_to_ids.items()):
            if speed not in ACCEPTABLE_SPEEDS:
                msg = self.log_msg("has invalid speed {speed}", video_id=video_id)
                log.error(msg.format(speed=speed))
                num_errors += 1
            elif speed in OK_SPEEDS_TO_GOOD_SPEEDS:
                msg = self.log_msg("has speed {speed}, should be {preferred_speed}",
                                   video_id=video_id)
                log.warning(msg.format(speed=speed, 
                                       preferred_speed=OK_SPEEDS_TO_GOOD_SPEEDS[speed]))
                num_warnings += 1


def parse_video_tags(xml_file):
    global num_errors
    global num_warnings
    xml_txt = "\n".join(line for line in xml_file 
                        if not line.strip().startswith("%")).strip()

    # This removes template directives that look like tags, e.g.: <%include.../>
    xml_txt = re.sub(r"<%.+\/>", "", xml_txt)

    if not xml_txt:
        log.warning("Skipping empty file {0}".format(xml_file.name))
        return []

    try:
        doc = ElementTree.fromstring(xml_txt)
        video_els = doc.findall(".//video")
    except Exception as err:
        log.exception(err)
        log.error("Could not parse file {0}".format(xml_file.name))
        return []

    def _parse_speeds(youtube_attr):
        time_id_pairs = youtube_attr.split(",")
        return dict(s.split(":") for s in time_id_pairs)

    return [Video(name=video_el.attrib.get("name", None),
                  speeds_to_ids=_parse_speeds(video_el.attrib["youtube"]),
                  filename=xml_file.name)
            for video_el in video_els]


def uri_for(author, start_index):
    """Make the URL for a feed request -- the API doesn't do this for us. Note
    that the normal search by author is broken for private feeds -- we have to 
    query based on uploads like this."""
    MAX_RESULTS = 50 # As many as we're allowed to pull at one time.
    return "http://gdata.youtube.com/feeds/api/users/{0}/uploads?".format(author) + \
           "max-results={0}&".format(MAX_RESULTS) + \
           "start-index={0}".format(start_index)

def videos_for(author, email, password, api_key):
    """For a given YouTube author, return as many videos from their feed as 
    possible, starting from start index = 1 (it's 1-based)"""
    youtube = gdata.youtube.service.YouTubeService()
    youtube.developer_key = api_key
    youtube.email = email
    youtube.password = password
    youtube.ProgrammaticLogin(None, None) # Captcha tokens are None.
    log.debug("Using API key: {0}".format(youtube.developer_key))

    start = 1
    while True:
        uri = uri_for(author, start)
        log.debug("Fetching videos from {0}".format(uri))
        feed = youtube.GetYouTubeVideoFeed(uri)
        log.debug("-- got {0} videos".format(len(feed.entry)))

        if not feed.entry:
            break

        for e in feed.entry:
            # e.id.text gives you something like tag:youtube.com,2008:video:p2Q6BrNhdh8
            youtube_id = e.id.text.split("/")[-1]
            yield youtube_id, e

        start += len(feed.entry)

def get_all_videos(accounts_to_auth_info):
    """Return a dict of YouTube IDs => YouTubeVideoEntry objects that represents
    every YouTubeVideoEntry that exists in our accounts"""
    ids_to_videos = {}

    for author, (email, password, key) in accounts_to_auth_info.items():
        log.debug("Pre-fetching videos for {0}".format(author))
        ids_to_videos.update(dict(videos_for(author, email, password, key)))

    return ids_to_videos


def get_auth_sub_url():
    next = 'http://127.0.0.1:8000/'
    scope = 'http://gdata.youtube.com'
    secure = False
    session = True
    yt_service = gdata.youtube.service.YouTubeService()
    return yt_service.GenerateAuthSubURL(next, scope, secure, session)


def main():
    parser = argparse.ArgumentParser(description='Check YouTube URLs in course data files.')
    parser.add_argument("files", nargs="+", type=argparse.FileType('r'))
    parser.add_argument("--log-level", required=False, dest='log_level', default="INFO",
                        choices=['info', 'INFO', 'warning', 'WARNING', 
                                 'error', 'ERROR', 'debug', 'DEBUG'])
    parser.add_argument("--auth-file", required=True, dest='auth_file',
                        type=argparse.FileType('r'))

    args = parser.parse_args()
    log.setLevel(args.log_level.upper())

    accounts_to_auth_info = json.load(args.auth_file)

    log.info("Pre-fetching video data from accounts: {0}"
             .format(", ".join(accounts_to_auth_info)))
    ids_to_videos = get_all_videos(accounts_to_auth_info)
    log.info("Pre-fetching complete ({0} videos)".format(len(ids_to_videos)))

    log.info("Checking files and subtitles...")
    num_files = len(args.files)
    num_video_tags = 0
    for f in args.files:
        videos = parse_video_tags(f)
        for video in videos:
            video.check(ids_to_videos)
            num_video_tags += 1

    print()
    print("Checked {0} video tags from {1} files".format(num_video_tags, num_files))
    print("Errors: {0}".format(num_errors))
    print("Warnings: {0}".format(num_warnings))

    return num_errors


if __name__ == '__main__':
    sys.exit(main())




