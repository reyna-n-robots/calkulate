# libraries
import numpy as np
import calkulate as calk
import pandas as pd

# create dataframe (dict-like container for Series objects. labeled rows and columns)
data = pd.read_excel("tests/data/TEST_titration_table.xlsx")

# write data to dataframe without writing row names (this standardizes tables)
# https://www.digitalocean.com/community/tutorials/pandas-to_csv-convert-dataframe-to-csv
# https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html?highlight=to_csv#pandas.DataFrame.to_csv
data.to_excel("tests/data/TEST_titration_table.xlsx",index=False)

# perform calkulate
data = calk.read_excel("tests/data/TEST_titration_table.xlsx").calkulate()
alkalinity_results = data.alkalinity  # <== here are your alkalinity results
print(alkalinity_results)