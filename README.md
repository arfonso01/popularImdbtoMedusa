# Add popular IMDB series to pyMedusa 

A script that add the popular tvshow of IMDB to pyMedusa. \
Works for IMDB, TMDB and TVDB indexers in pyMedusa

## Dependencies

- [python3](https://www.python.org/downloads/)
- [requests](https://pypi.org/project/requests/)
- [BeautifulSoup](https://pypi.org/project/beautifulsoup4/)

## How to use it

- Step 1: Edit the nexts variables (lines 7-11):
		
		min_rating = 8.5 # float
		min_year = 2020 # int
		medusa_host = 'localhost:8081' # string 
		medusa_api_key = 'my_medusa_api_key' # string
		medusa_indexer = "tmdb" # or "tvdb" or "imdb"

- Step 2: Run the python script

## Something else

The script make a two files:

- exclude_series.txt: to write IMDB ID's that I want to exclude. (see exclude_series.example.txt)
- popularImdbtoMedusa.log: to check the execution of the script
