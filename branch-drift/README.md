drift.py
Sef Kloninger (sef@stanford.edu), Stanford University

Within a repo, measure how different two branches are.  Naively does so
by considering the size of the differences between those branches over a
range of dates.

Note that this script is currently broken by force pushes on branches.
Since that's become the common way to handle branches, especially
release branches, it's not all that valuable until we figure that out.

