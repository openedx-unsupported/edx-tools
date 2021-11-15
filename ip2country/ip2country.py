#!/usr/bin/env python

import fileinput
import collections
import pygeoip

lookup = pygeoip.GeoIP('GeoIP.dat')
totals = collections.defaultdict(int)
for ip in fileinput.input():
    country = lookup.country_code_by_addr(ip)
    totals[country] += 1
for country in sorted(totals, key=totals.get, reverse=True):
    print(country+","+str(totals[country]))

