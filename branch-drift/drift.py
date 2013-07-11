#!/usr/bin/env python

import matplotlib.pyplot as plt
import os
import datetime
import subprocess
import re
from collections import OrderedDict


def main():
    os.chdir("../../edx-platform")

    start_date = datetime.date(2013,06,01)
    end_date = datetime.date.today()
    from_branch = "edx-west/release"
    from_branch_origin = "origin/"+from_branch
    to_branch = "master"
    to_branch_origin = "origin/"+to_branch

    (difflines, diffblocks) = branch_diffs(from_branch_origin, to_branch_origin, 
            start_date, end_date)

    plt.figure(1)
    plt.subplot(211)
    plt.title("Size of diff between %s and %s" % (from_branch, to_branch))
    plt.plot(difflines.keys(), difflines.values())

    plt.subplot(212)
    plt.title("Changes between %s and %s" % (from_branch, to_branch))
    plt.plot(diffblocks.keys(), diffblocks.values())

    plt.savefig("diff")


def branch_diffs(from_branch, to_branch, start_date, end_date):
    """
    Scan over date range, running "gid diff" between braches, and count 
    differences. Returns two ordered dicts by date, one of size of diff 
    in lines, one in blocks.

    Date range cleveness from stack overflow (http://goo.gl/frxo0).
    """
    def daterange(start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

    difflines = OrderedDict()
    diffblocks = OrderedDict()
    for d in daterange(start_date, end_date):
        diffcmd = ["git", "diff", "%s@{%s}" % (from_branch, d), "%s@{%s}" % (to_branch, d)]
        diffoutput = subprocess.check_output(diffcmd)
        lines = 0
        blocks = 0
        diff_block_re = re.compile('^--- ')
        for line in diffoutput.splitlines():
            lines += 1
            if diff_block_re.match(line):
                blocks += 1
        difflines[d] = lines
        diffblocks[d] = blocks
        print "diff:", d.strftime('%Y-%m-%d'), lines, blocks

    return (difflines, diffblocks)


if __name__ == '__main__':
    main()
