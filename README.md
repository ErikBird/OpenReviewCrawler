# OpenReviewCrawler
This project is a crawler for OpenReview submissions. It is the base for [another project](https://github.com/movabo/science-revisioning) that wants to match comments and reviews to specific changes between revisions.

Both projects are created by students of the Technische Universität Darmstadt as a course project for the [UKP lab](https://www.informatik.tu-darmstadt.de/ukp/ukp_home/index.en.jsp).

## Table of Contents
1. [About the OpenReview API Model](#api)
2. [Setup](#setup)
3. [Usage](#usage)
4. [Config](#config)
5. [Output](output)
6. [Labeling Approach](#labeling)
7. [Relational Database](#database)

<a name="api"></a>
## About the OpenReview API Model
We present the way OpenReview API models the data with invitations, notes and content in-depth [here](about_the_openreview_api_model.md).  

TL;DR:  
The model with notes, invitations and content allows customization for each venue.  
Notes are container for data (submissions, reviews, comments), invitations decide the type of a note and the content field of a note contains its textual content (title, abstract, authors for a paper; review text, score, confidence for a review and so on).  
Invitations and content are specified by each venue as needed or wanted and can thus vary between venues in name and extend.
<a name="setup"></a>
## Setup 
We recommend at least Python 3.6 to use this project.

Run `pip install -r requirements.txt` to install all required packages

<a name="usage"></a>
## Usage
Run ``python crawler.py `` to start the crawler with the default config `./config.json`. 

The program stores the JSON output after every venue and year and a restart will skip all venues and years already present in the JSON.


If you want to specify the path to the config, use `-c | --config {path}`. 
If you don't want your password in the config, use `-p | --password {password}`.

To get a list of all possible venues, run `python crawler --help_venues`

``python crawler.py --help`` will display all possible arguments.
<a name="config"></a>
## Config
You specify the venues and years to crawl in the config. Check out the example config [here](config.json).

Use `year: "all"` to crawl an entire venue.

Leaving username and password empty uses the guest access.

The binary variable `acceptance_labeling` determines if the data will be annotated with the acceptance decision prior to storing.

The binary variable `output_json` determines if the output will be saved as json file in the `outdir` with as `filename`.

The binary variable `output_SQL` determines if the data will be inserted in the database which is configured [here](example_output.json).

`output_SQL` and `output_json` function independent from each other.

The binary variable `skip_pdf_download` determines if the pdfs will be downloaded.

<a name="output"></a>
## Output
The program goes over the venues by year, download the PDFs for the revisions and output a dictionary of the data.
This data can then be stored as JSON or SQL-Database. 

For the JSON, the information about submissions, comments and reviews are formatted as [Notes](https://openreview-py.readthedocs.io/en/latest/api.html#openreview.Note) as specified by OpenReview (for more information, see [About the OpenReview API Model](api)).
An example JSON can be found [here](example_output.json).

In the JSON, each submission also has the field `revisions` which contains a list of all previous revisions of the submissions
and `notes` which contains a list of all comments, reviews and decisions of the submissions.
Each note in this list also has a field `revisions` for previous iterations of it.

PDFs are stored in the format `{forum}_{revision_number}.pdf`. `revisions_number` is the position in the revision array of a submissions.
Note that the array is sorted from newest to oldest.

The database removes some fields deemed unneccesary.

<a name="labeling"></a>
## Acceptance Labeling
How a submissions is marked as accepted or rejected varies from venue to venue, year to year and even within one venue year.

We present ``acceptance_labeling.py`` which uses string matching rules to label the acceptance status of all submissions.

### Usage
Run ``python acceptance_labeling.py -f {output_from_crawler.json}`` to label the output JSON from ``crawler.py``.
 
Each submission will receive a new field ``acceptance_tag`` that indicates its status.
 ``acceptance_tag`` can have any value from accepted, rejected, withdrawn, unknown.
 
The result is written in the input JSON by default, but a new output can be specified with the ``-w`` or ``--write_new_file`` argument.


``python acceptance_labeling.py --help`` will display all possible arguments.

### Labeling Approach
The labeling is done with string matching of the invitation names and note content.


A submission is labeled as withdrawn, if its invitation contains 'withdraw'.

Otherwise we search for a decision note in one of the notes. Decision notes contain 'decision' or 'acceptance' in their invitation.

We search each content field (except title) of the decision note for 'accept' or 'reject'.
If both are found in a field, it is labeled unknown, otherwise it is labeled accepted or rejected.
If both words are not found in a decision note, we also label it as accepted. This is due to many venues, which only write for what a submission is accepted (e.g. poster or workshop). 
However, all rejected papers that we have seen contain 'reject' in their decision note, so we do not expect many false positives from this.

We also accommodate ICLR exceptions (decicion as content field of the submission, decision note named meta review, desk rejected invitation), as ICLR is one of the largest venues on OpenReview.

### Results
We present the results of our approach on all venues and years using ``config_all.json`` [Date: 14.12.2019]

|Total   |Unknown   |Withdrawn   |Accepted   |Rejected   |
|---|---|---|---|---|
|10035   |4502*|779   |2615   |2139   |
 
 \* 2594 from ICLR 2020 which have no results at that time
 
 Random samples from the unknown submissions suggest that they have indeed no decision result and they are not failures of our labeling algorithm to identify the result.
 
 <a name="database"></a>
 ## Relational Database
 ### Database Connection
 The crawler is able to convert the dictionary data into a structured SQL Database format. Therefore it utilizes the popular 
 SQLAlchemy Library which can interface various popular database systems.
 
 This database can be configured [here](database/database.py).
 
 Since the database uses the normalization standards, it cannot store lists. 
 Therefore it is theoretically possible that the data-dictionary input contains more data than the database is storing.
 However the implementation is quite robust to not omit the key data about the paper-review process.
 ### Database Values
Most values are intuitive or might be looked up [here](https://openreview-py.readthedocs.io/en/latest/api.html#openreview.Note).
However for the following variables an explanation is quite useful:

`cdate` (int, optional) – Creation date

`tcdate` (int, optional) – True creation date

`tmdate` (int, optional) – Modification date

`ddate` (int, optional) – Deletion date
 ### UML Diagramm
 ![UML_Diagramm](Resources/UML.svg  "SQL Database Diagramm" )
