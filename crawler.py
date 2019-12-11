import argparse
import json
import os
from datetime import date
import re
import openreview
import logging
import sys
import progressbar
import threading
from database import SQLDatabase

def crawl(client, config, log):
    '''
    This method crawls the configured venues and saves all comments and all PDF Revisions to the output folder.

    :param client: the openreview client
    :param config: the config dictionary
    :param log: the configured logging client
    :return: Nothing
    '''
    if not os.path.exists(config["outdir"]):
        os.makedirs(config["outdir"])
    if os.path.exists(os.path.join(config["outdir"], config["filename"])):
        with open(os.path.join(config["outdir"], config["filename"]), 'r') as file_handle:
            results = json.load(file_handle)
    else:
        results = []
    already_done = set(["{} {}".format(r["venue"], r["year"]) for r in results])

    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            if "{} {}".format(venue, year) in already_done:
                log.info("Skipping {} {}. Already done".format(venue, year))
                continue
            log.info('Current Download: '+ venue+' in '+str(year))
            invitations_iterator = openreview.tools.iterget_invitations(client, regex="{}/{}/".format(venue, year), expired=True)
            invitations = [inv.id for inv in invitations_iterator]
            invitations = merge_invitations(invitations)
            submissions = []
            if not invitations:
                log.warning('No data for '+ venue+' in '+str(year))
            else:
                forum_idx_map = {}
                other_notes = []
                for inv in progressbar.progressbar(invitations):
                    notes = [note.to_json() for note in openreview.tools.iterget_notes(client, invitation=inv)]
                    if "submission" in inv.lower():
                        # this is a bit of a hack but there is no general submission invitation but all submission invitations
                        # contain at least (S|s)ubmission somewhere
                        # check https://openreview-py.readthedocs.io/en/latest/get_submission_invitations.html to verify
                        log.info("Submission invitation")
                        forum_idx_map.update({n["forum"]: i+len(submissions) for i, n in enumerate(notes)})
                        threads = list()
                        for n in progressbar.progressbar(notes):
                            references = client.get_references(n["id"], original=True)
                            if not config["skip_pdf_download"]:
                                for index, r in enumerate(references):
                                    pdf_name = n["id"] + '_' + str(index) + '.pdf'
                                    x = threading.Thread(target=download_revision, args=(r.id,pdf_name,client))
                                    threads.append(x)
                                    x.start()
                            n["revisions"] = [r.to_json() for r in references]
                            n["notes"] = []
                        submissions.extend(notes)
                    else:
                        revisions = [r.to_json() for r in client.get_references(invitation=inv)]
                        for note in notes:
                            note["revisions"] = [r for r in revisions if r["referent"] == note["id"]]
                        other_notes.extend(notes)
            if not submissions:
                log.warning('No submissions found for '+ venue+' in '+str(year))
            else:
                for note in other_notes:
                    try:
                        submissions[forum_idx_map[note["forum"]]]["notes"].append(note)
                    except KeyError:
                        log.info("No submission found for note "+note["id"]+" in forum "+note["forum"])
            results.append({"venue": venue, "year": year, "submissions": submissions})
            if config["output_SQL"]:
                db = SQLDatabase(dbname='myCrawl')
                db.create_db_tables()
                db.insert_dict(results)
            if config["output_json"]:
                with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
                    json.dump(results, file_handle, indent=config["json_indent"])




def merge_invitations(invitations):
    '''
    This method merges invitations for OpenReview API wildcard support
    :param invitations: List of Invitations
    :return: Set of invitations
    '''
    new_invitations = set()
    for inv in invitations:
        sub1 = re.sub(r"/(P|p)aper[0-9]+/", r"/\1aper.*/", inv)
        sub2 = re.sub(r"/(P|p)aper/[0-9]+/", r"/\1aper/.*/", sub1)
        new_invitations.add(sub2)
    return new_invitations


def download_revision(ref_id, pdf_name, client):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''

    out_path = os.path.join(config["outdir"], 'pdf/')
    if not os.path.exists(out_path): os.makedirs(out_path)
    if not ref_id: return
    try:
        file = client.get_pdf(ref_id, is_reference=True)
    except:
        log.info(ref_id + ' has no pdf ')
        return
    with open(os.path.join(out_path, pdf_name), "wb") as file1:
        file1.write(file)
    log.info(pdf_name + ' downloaded')


def get_all_available_venues():
    '''
    This method prints all available venues to the console
    It can be used to find the exact name to configure the "config.json" file for the according venue.
    This method is executed it this programm is executed with the parameter "--help_venues"
    :return: Nothing
    '''
    print("Available venues:")
    c = openreview.Client(baseurl='https://openreview.net')
    venues = openreview.tools.get_all_venues(c)
    print(*venues, sep="\n")


if __name__ == '__main__':
    log = logging.getLogger("crawler")
    log.setLevel(logging.INFO)
    progressbar.streams.wrap_stderr()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', help='Configuration for the crawling', default='config.json')
    parser.add_argument(
        '-p', '--password', help='Password for the username out of the config. Overwrites the password in config')
    parser.add_argument('-b', '--baseurl', default='https://openreview.net',
                        help="in case a different base URL is needed. This will usually not be the case")
    parser.add_argument("--help_venues", action='store_true', help="Print a list of all possible venues")
    args = parser.parse_args()

    if args.help_venues:
        get_all_available_venues()
        exit()

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    config = json.load(open(args.config))
    username = config["username"]
    if args.password is not None:
        password = args.password
    else:
        password = config["password"]

    client = openreview.Client(
        baseurl='https://openreview.net',
        username=username,
        password=password)
    log.info('Login as '+username+' was successful')

    crawl(client, config, log)
