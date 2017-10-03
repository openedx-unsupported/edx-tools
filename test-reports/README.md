summarize_test_results.py
=========================

Traverses the directory structure of a Jenkins edx-platform test run, finds all test result files, and parses/summarizes the results. Transforms the output into an HTML table with the similar test failures grouped, aggregated, and ranked.

Supports both output formats - the old nose format and the new pytest format. Assumes that both test systems' output files are named 'nosetests.xml'.

