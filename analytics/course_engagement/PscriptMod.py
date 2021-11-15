#This script is meant to read in an SQL query (dumped as csv)
#and create a pivot table with modules as rows and grades as columns.
import sys
import csv
import pandas as pd
import numpy as np

datafile = sys.argv[1]
mappingfile = sys.argv[2]

#Taking in the txt output of a SQL query and pivot-tabling
csvdata = pd.read_csv(datafile, sep='\t')
data_distribution = pd.tools.pivot.pivot_table(csvdata.fillna(value=9999),
      values='student_id',
      rows='module_id',
      cols='grade',
      aggfunc='count')
unindexed = data_distribution.reset_index()

#Taking in the translation between module_id and display_name based on the json map
dfI = pd.read_csv(mappingfile, sep=' "" ', header=None, names=['module_id','display_name'])
mapping = pd.DataFrame( {'module_id': dfI['module_id'], 'display_name': dfI['display_name']})

merged = mapping.merge(unindexed, on='module_id', sort=False)

name = "{}readable.csv".format(sys.argv[1].rsplit( ".", 1 )[ 0 ])
merged.to_csv(name, index=False)