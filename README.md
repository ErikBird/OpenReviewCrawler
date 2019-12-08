# OpenReviewCrawler
This project is a crawler for OpenReview submissions. It is the base for [another project](https://github.com/movabo/science-revisioning) that wants to match comments and reviews to specific changes between revisions.

Both projects are created by students of the Technische Universität Darmstadt as a course project for the [UKP lab](https://www.informatik.tu-darmstadt.de/ukp/ukp_home/index.en.jsp).


## Setup
We recommend at least Python 3.6 to use this project.

Run `pip install -r requirements.txt` to install all required packages

## Usage
Run ``python crawler.py `` to start the crawler with the default config `./config.json`. 

If you want to specify the path to the config, use `-c | --config {path}`. 
If you don't want your password in the config, use `-p | --password {password}`.

To get a list of all possible venues, run `python crawler --help_venues`

``python crawler.py --help`` will display all possible arguments.
## Config
You specify the venues and years to crawl in the config. Check out the example config [here](config.json).

Use `year: "all"` to crawl an entire venue.
Leaving username and password empty uses the guest access.

## Output
The program will go over the venues by year, download the PDFs for the revisions and output a JSON with the data.
In the output JSON, information about submissions, comments and reviews are formatted as [Notes](https://openreview-py.readthedocs.io/en/latest/api.html#openreview.Note) as specified by OpenReview.
See [here](example_output.json) for an example JSON.

Each submission also has the field `revisions` which contains a list of all previous revisions of the submissions
and `notes` which contains a list of all comments, reviews and decisions of the submissions.
Each note in this list also has a field `revisions` for previous iterations of it.

PDFs are stored in the format `{forum}_{revision_number}.pdf`. `revisions_number` is the position in the revision array of a submissions.
Note that the array is sorted from newest to oldest.
