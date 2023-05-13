import pandas as pd
import openpyxl
matches = pd.read_csv("matches.csv", index_col=0)

# dtypes looks at the type of data in each column, ML only looks at numeric data type (float64 or int64)
# convert non-numerical data into numerical

matches["date"]  = pd.to_datetime(matches["date"])
# converts existing column to datetime

## creating predictors
# These are the factors we will add to our table

# home or away advantage, venue code is 0 when game is away and 1 in when game is at home
matches["venue_code"] = matches["venue"].astype("category").cat.codes

# record against opponent, each opponent has it's own code 
matches["opp_code"] = matches["opponent"].astype("category").cat.codes

# time that the game is played, only observing hour
matches["hour"] = matches["time"].str.replace(":.+", "", regex = True).astype("int")

# day that the game is played
matches["day_code"] = matches["date"].dt.dayofweek 

# target is whether the team won or not, loss is coded as a 0 and win is coded as a 1
matches["target"] = (matches["result"] == "W").astype("int")

predictors = ["venue_code", "opp_code", "hour", "day_code"]

# to improve accuracy let's predict rolling average
def rolling_averages(group, cols, new_cols):
    group = group.sort_values("date")
    rolling_stats = group[cols].rolling(3, closed='left').mean()
    group[new_cols] = rolling_stats
    group = group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "xg", "xga", "poss", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]

matches_rolling = matches.groupby("team").apply(lambda x: rolling_averages(x, cols, new_cols))
matches_rolling = matches_rolling.droplevel('team')
# applied a function to compute rolling averages for every match

matches_rolling.index = range(matches_rolling.shape[0])
# assign specific index values to be our new indices so that we don't have repeating data


## training our ML model
from sklearn.ensemble import RandomForestClassifier
# random forest is a series of decision trees (random state=1 means our results will always be the same)
rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

# determine precision of model
from sklearn.metrics import precision_score

def make_predictions(data, predictors):
    train = data[data["date"] < '2022-01-01']
    test = data[data["date"] > '2022-01-01']
    # split the data to improve future match predictions
    rf.fit(train[predictors], train["target"])
    # fit random forest model and train with our given predictors to predict the target
    preds = rf.predict(test[predictors])
    # this generates predictions
    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    # this gives us a chart showing where our predictions went wrong
    precision = precision_score(test["target"], preds)
    # when we predicted a win, what percentage of the time did the team actually win
    return combined, precision

combined, precision = make_predictions(matches_rolling, predictors + new_cols)

combined = combined.merge(matches_rolling[["date", "team", "opponent", "result"]], left_index = True, right_index=True)

## combining home and away predictions to avoid inconsistant predictions

# normalize team and opponent names
class MissingDict(dict):
    __missing__ = lambda self, key: key

map_values = {
    "Brighton and Hove Albion": "Brighton",
    "Manchester United": "Manchester Utd",
    "Newcaste United": "Newcastle Utd",
    "West Ham United": "West Ham",
    "Wolverhampton Wanderers": "Wolves"
}
mapping = MissingDict(**map_values)
combined["new_team"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date", "new_team"], right_on=["date", "opponent"])
# merge team field with opponent field

precision = merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] == 0)]["actual_x"].value_counts()
# this is the actual accuracy of our program
print("2022-01-01 onwards precision:", precision[1]  / (precision[1]+precision[0]))


## Part TWO of this project is predicting the outcome of future matches given the little data we have on the game (day, venue, hour, opponent)
from future_predictions import future_prediction

future = future_prediction(matches)

print("2022-2023 predicted table:", future)
