import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

years = list(range(2022,2018, -1))
all_matches = []
# this list will contain several dataframes in the matchlogs for 1 team in 1 season

standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

### code from practice will be pasted into this loop
for year in years:
    # parse HTML
    data = requests.get(standings_url)
    soup = BeautifulSoup(data.text, "lxml")
    standings_table = soup.select('table.stats_table')[0]

    # grabbing URLS of all teamlinks in stats table
    links = standings_table.find_all('a')
    links = [l.get("href") for l in links]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]

    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com{previous_season}"

    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
        
        # this takes out every team name from its URL
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")
        # grabbed scores & fixtures table
        
        # Get shooting stats by parsing HTML
        soup = BeautifulSoup(data.text, features="lxml")
        links = soup.find_all('a')
        links = [l.get("href") for l in links]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        shooting = pd.read_html(data.text, match='Shooting')[0]
        shooting.columns = shooting.columns.droplevel()
        # now we have both our matches and shooting data frames
        # Let's MERGE the data
        try:
            team_data = matches[0].merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            continue
        # ignores teams that don't have shooting stats

        team_data = team_data[team_data["Comp"] == "Premier League"]
        # this filters out only Premier League games
        team_data["Season"] = year
        team_data["Team"] = team_name
        # need to distinguish team and season in overall dataframe
        all_matches.append(team_data)
        time.sleep(15)
        # slowing down our scraping speed to avoid getting blocked by website


match_df = pd.concat(all_matches)
# takes list of dataframes as input and returns one dataframe

match_df.columns = [c.lower() for c in match_df.columns]
match_df.to_csv("matches.csv")

### We now have a csv file containing over 1000 matches


## scrape future match
standings_url = "https://fbref.com/en/comps/9/11566/2022-2023-Premier-League-Stats"

def scraping_future(standings_url):
    all_matches = []
    # parse HTML
    data = requests.get(standings_url)
    soup = BeautifulSoup(data.text, "lxml")
    standings_table = soup.select('table.stats_table')[0]

    # grabbing URLS of all teamlinks in stats table
    links = standings_table.find_all('a')
    links = [l.get("href") for l in links]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]

    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")
            
        # this takes out every team name from its URL
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")
        # grabbed scores & fixtures table
            
        team_data = matches[0]

        team_data = team_data[team_data["Comp"] == "Premier League"]
        # this filters out only Premier League games
        team_data["Season"] = 2023
        team_data["Team"] = team_name
        # need to distinguish team and season in overall dataframe
        all_matches.append(team_data)
        time.sleep(5)
        # slowing down our scraping speed to avoid getting blocked by website

    match_df = pd.concat(all_matches)
    # takes list of dataframes as input and returns one dataframe

    match_df.columns = [c.lower() for c in match_df.columns]
    match_df.to_csv("matches.csv", mode='a', header=False)

scraping_future(standings_url)
# ready to begin prediction!
