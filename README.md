# Dota-Realtime-Matchup-Analyzer
A real time match up analyzer for the video game Dota 2.

When joining a new match this tool will provide useful information about recent games of the other players. This includes their percentage of won games and most played heroes.

Identifying strong players and their best heroes can be a large advantage in the banning phase and when picking your own hero.

## Example output

![image](https://user-images.githubusercontent.com/34030720/126770087-b1367464-d598-4551-b0bc-1766a6f9cc0e.png)

The second column shows the players winrate in their last 25 games. Displayed are their 3 most played heroes in combination with won games/total games on the hero.

## Setup

Simply clone or download the repository and run `dota_realtime_matchup_analyzer.py` using python 3.6+. If you have not installed Dota 2 at the default location
(C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta) then specify its location in the `config.json` file.

## How does it work?

When joining a new match Dota provides the Dota-IDs of all players in the `server_log.txt` file located inside the Dota 2 folder. The provided Dota-IDs are then used in combination with the [OpenDota API](https://docs.opendota.com/).