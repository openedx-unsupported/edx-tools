## drift.py

Sef Kloninger (sef@stanford.edu), Stanford University

Within a repo, measure how different two branches are.  It does
this **very** naively: consider the size of the differences between
those branches over a range of dates.

TODO:

* This script is currently broken by force pushes on branches.
  Since that's become the common way to handle branches, especially
  release branches, it's not all that valuable until we figure that out.

* Currently relies on comparing two branches in the same repo. As more
  development moves to different repos (forks), this should be more
  flexible to handle that case. This could just be as simple as having
  two remotes in the repo where you run the metrics.
  
