htmlwriter.py
=============

Scrapes and parses the output of a Jenkins system test run for edx-platform. Transforms the output into an HTML table with the similar test failures grouped, aggregated, and ranked.

Supports both output formats - the old nose format and the new pytest format.

