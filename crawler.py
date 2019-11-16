import argparse
import json
import os
from datetime import date
import re
import openreview
import logging
import sys
import progressbar
import urllib.request

def crawl(client, config, log):
    results = []
    driver = start_webdriver()
    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            log.info('Current Download: '+ venue+' in '+str(year))
            invitations_iterator = openreview.tools.iterget_invitations(client, regex="{}/{}/".format(venue, year))
            invitations = [inv.id for inv in invitations_iterator]
            invitations = merge_invitations(invitations)
            if not invitations:
                log.warning('No data for'+ venue+' in '+str(year))
                continue
            else:
                submissions = []
                forum_idx_map = {}
                other_notes = []
                for inv in progressbar.progressbar(invitations):
                    notes = [note.to_json() for note in openreview.tools.iterget_notes(client, invitation=inv)]
                    if "ubmission" in inv:
                        # this is a bit of a hack but there is no general submission invitation but all submission invitations
                        # contain at least (S|s)ubmission somewhere
                        # check https://openreview-py.readthedocs.io/en/latest/get_submission_invitations.html to verify
                        log.info("Submission invitation")
                        forum_idx_map.update({n["forum"]: i+len(submissions) for i, n in enumerate(notes)})
                        for n in notes:
                            n["revisions"] = download_revisions(n["id"],client=client)
                            print(n["revisions"])
                            #get_submission_revisions(n["id"], driver)
                            n["notes"] = []
                        submissions.extend(notes)
                    else:
                        revisions = [r.to_json() for r in client.get_references(invitation=inv)]
                        for note in notes:
                            note["revisions"] = [r for r in revisions if r["referent"] == note["id"]]
                        other_notes.extend(notes)
                if not submissions:
                    log.warning('No submissions found for '+ venue+' in '+str(year))
                    continue
                else:
                    for note in other_notes:
                        try:
                            submissions[forum_idx_map[note["forum"]]]["notes"].append(note)
                        except KeyError:
                            log.info("No submission found for note "+note["id"]+" in forum "+note["forum"])
                results.append({"venue": venue, "year": year, "submissions": submissions})

    if not os.path.exists(config["outdir"]):
        os.makedirs(config["outdir"])
    with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
        json.dump(results, file_handle, indent=config["json_indent"])


def merge_invitations(invitations):
    new_invitations = set()
    for inv in invitations:
        sub1 = re.sub(r"/(P|p)aper[0-9]+/", r"/\1aper.*/", inv)
        sub2 = re.sub(r"/(P|p)aper/[0-9]+/", r"/\1aper/.*/", sub1)
        new_invitations.add(sub2)
    return new_invitations


def download_revisions(note_id,client):
    references = client.get_references(note_id,original=True)
    out_path = os.path.join(config["outdir"], 'pdf/')
    if not os.path.exists(out_path): os.makedirs(out_path)
    for index,r in enumerate(references):
        pdf = note_id + '_' + str(index) + '.pdf'
        with open(os.path.join(out_path, pdf), "wb") as file1:
            file1.write(client.get_pdf(r.id,is_reference=True))
        log.info(pdf + ' downloaded')


def get_all_available_venues():
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
        '-c', '--config', help='configuration for the crawling', default='config.json')
    parser.add_argument(
        '-p', '--password', help='password for the username given in the config. Overwrites password in config')
    parser.add_argument('--baseurl', default='https://openreview.net')
    parser.add_argument("--help_venues", action='store_true', help="receive a list of all possible venues")
    args = parser.parse_args()

    if args.help:
        get_all_available_venues()

    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    try:
        config = json.load(open(args.config))
    except:
        print('The configuration file has not been found. \n Please Make sure it is correctly Named \'config.json\' and is located in the project root folder.\n Otherwise please specify the correct path with \'-c {path}\'')

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
