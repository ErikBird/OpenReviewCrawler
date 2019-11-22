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

def crawl(client, config, log):
    '''
    This method crawls the configured venues and saves all comments and all PDF Revisions to the output folder.

    :param client: the openreview client
    :param config: the config dictionary
    :param log: the configured logging client
    :return: Nothing
    '''
    results = []
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
                    if "submission" in inv.lower():
                        # this is a bit of a hack but there is no general submission invitation but all submission invitations
                        # contain at least (S|s)ubmission somewhere
                        # check https://openreview-py.readthedocs.io/en/latest/get_submission_invitations.html to verify
                        log.info("Submission invitation")
                        forum_idx_map.update({n["forum"]: i+len(submissions) for i, n in enumerate(notes)})
                        threads = list()
                        for n in progressbar.progressbar(notes):
                            references = client.get_references(n["id"], original=True)
                            pdf_names=[]
                            for index, r in enumerate(references):
                                pdf_name = n["id"] + '_' + str(index) + '.pdf'
                                pdf_names.append(pdf_name)
                                x = threading.Thread(target=download_revision, args=(r.id,pdf_name,client))
                                threads.append(x)
                                x.start()
                            n["revisions"] = pdf_names
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
    '''
    This method merges invitations if they are redundant
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
    log.setLevel(logging.CRITICAL)
    progressbar.streams.wrap_stderr()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', help='configuration for the crawling', default='config.json')
    parser.add_argument(
        '-p', '--password', help='password for the username given in the config. Overwrites password in config')
    parser.add_argument('-b','--baseurl', default='https://openreview.net')
    parser.add_argument("--help_venues", action='store_true', help="receive a list of all possible venues")
    args = parser.parse_args()

    if args.help_venues:
        get_all_available_venues()
        exit()

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
