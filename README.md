# OpenReviewCrawler
This project is a crawler for OpenReview submissions. It is the base for [another project](https://github.com/movabo/science-revisioning) that wants to match comments and reviews to specific changes between revisions.

Both projects are created by students of the Technische Universität Darmstadt as a course project for the [UKP lab](https://www.informatik.tu-darmstadt.de/ukp/ukp_home/index.en.jsp).


## Setup
We recommend at least Python 3.6 to use this project.

Run `pip install -r requirements.txt` to install all required packages

## Usage
Run ``python crawler.py `` to start the crawler with the default config `./config.json`. 
The program then will go over the venues by year, download the PDFs for the revisions and output a JSON with the data.
In output JSON, information about submissions, comments and reviews are formatted as [Notes](https://openreview-py.readthedocs.io/en/latest/api.html#openreview.Note) as specified by OpenReview.

If you want to specify the path to the config, use `-c | --config {path}`. 
If you don't want your password in the config, use `-p | --password {password}`.

To get a list of all possible venues, run `python crawler --help_venues`

## Config
You specify the venues and years to crawl in the config. Check out the example config [here](config.json).

Use `year: "all"` to crawl an entire venue.
Leaving username and password empty uses the guest access.