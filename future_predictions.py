import pandas as pd

matches = pd.read_csv("matches.csv", index_col=0)


def future_prediction(matches):
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

    # target is whether the team won or not, loss is coded as a 1 and win is coded as a 2 draw is coded as a 0
    matches["target"] = matches["result"].astype("category").cat.codes

    predictors = ["venue_code", "opp_code", "hour"]

    ## training our ML model
    from sklearn.ensemble import RandomForestClassifier
    # random forest is a series of decision trees (random state=1 means our results will always be the same)
    rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

    train = matches[matches["date"] < '2022-08-01']
    test = matches[matches["date"] > '2022-08-01']

    # split the data to improve future match predictions
    rf.fit(train[predictors], train["target"])
    # fit random forest model and train with our given predictors to predict the target
    prediction = rf.predict(test[predictors])

    predictions = pd.DataFrame(dict(outcome=prediction, team=test["notes"], date=test["date"], opponent=test["opponent"]), index=test.index)

    predictions.index = range(predictions.shape[0])


    teampoints = {}
    x = 0
    y = 38
    while y < 760:
        teampoints[f"{predictions['team'][x]}"] = (predictions["outcome"][x:y].value_counts()[2] * 3) + (predictions["outcome"][x:y].value_counts()[0])
        x += 38
        y += 38

    teampoints = dict(sorted(teampoints.items(), key=lambda item: item[1], reverse=True))

    return teampoints

