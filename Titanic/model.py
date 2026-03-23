import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

from sklearn import tree
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score


# Open the Titanic dataset
df = pd.read_csv('Titanic.csv')


# Print the first few lines of the dataframe
#
# Check the names and types of each column
print(df.head())
