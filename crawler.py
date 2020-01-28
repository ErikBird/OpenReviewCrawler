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
from database.database import SQLDatabase
from acceptance_labeling import labeling
import time
maxthreads = 10
sema = threading.Semaphore(value=maxthreads)
def crawl(client, config, log, db=None):
    '''
    This method crawls the configured venues and saves all comments and all PDF Revisions to the output folder.

    :param client: the openreview client
    :param config: the config dictionary
    :param log: the configured logging client
    :return: Nothing
    '''
    already_done = set([])
    results = []
    venue_id = -1
    if config["output_json"]:
        if os.path.exists(os.path.join(config["outdir"], config["filename"])):
            with open(os.path.join(config["outdir"], config["filename"]), 'r') as file_handle:
                log.info('previous file successfully loaded')
                results = json.load(file_handle)
                already_done = set(["{} {}".format(r["venue"], r["year"]) for r in results])
    elif config["output_SQL"]:
        venues = db.get_venues()
        if venues:
            venue_id = max([venue['id'] for venue in venues])
            already_done.update(["{} {}".format(v["venue"], v["year"]) for v in venues])



    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            if "{} {}".format(venue, year) in already_done:
                log.info("Skipping {} {}. Already done".format(venue, year))
                continue
            venue_id += 1

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
                            refs = client.get_references(n["id"], original=True)
                            references=[r.to_json() for r in refs[1:]]
                            original = refs[:1][0]
                            if not config["skip_pdf_download"]:
                                if config["output_json"]:
                                    pdf_name = n["id"] + '_' + str(0) + '.pdf'
                                    n['content']['pdf'] = '/pdf/' + pdf_name
                                    x = threading.Thread(target=download_revision_fs, args=(original.id, pdf_name, client))
                                    threads.append(x)
                                    x.start()
                                if config["output_SQL"]:
                                    x = threading.Thread(target=download_submission_db, args=(original.id, client, db, venue_id,n["id"]))
                                    threads.append(x)
                                    x.start()
                                for index, r in enumerate(references):
                                    if config["output_json"]:
                                        pdf_name = n["id"] + '_' + str(index+1) + '.pdf'
                                        r['content']['pdf']= '/pdf/'+pdf_name
                                        x = threading.Thread(target=download_revision_fs, args=(r['id'], pdf_name, client))
                                        threads.append(x)
                                        x.start()
                                    if config["output_SQL"]:
                                        x = threading.Thread(target=download_revision_db, args=(r['id'], client, db,n["id"]))
                                        threads.append(x)
                                        x.start()
                            n["revisions"] = references
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
            results.append({"venue_id":venue_id,"venue": venue, "year": year, "submissions": submissions})

    return results


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


def download_revision_fs(ref_id, pdf_name, client):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''
    sema.acquire()
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
    sema.release()

def download_revision_db(ref_id, client, db ,submission_id):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''
    sema.acquire()
    if not ref_id: return
    try:
        file = client.get_pdf(ref_id, is_reference=True)
    except:
        log.info(ref_id + ' has no pdf ')
        return
    db.insert_revision(ref_id, submission_id, pdf=file)
    log.info(ref_id + ' inserted into db')
    sema.release()

def download_submission_db(ref_id, client, db, venue_id,submission_id):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''
    sema.acquire()
    if not ref_id: return
    try:
        file = client.get_pdf(ref_id, is_reference=True)
    except:
        log.info(ref_id + ' has no pdf ')
        return
    db.insert_submission( venue_id,submission_id,pdf=file)
    log.info(ref_id + ' inserted into db')
    sema.release()

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

    db = None
    if config["output_SQL"]:
        db = SQLDatabase(dbtype='sqlite', dbname='myCrawl')
        db.create_db_tables()


    results = crawl(client, config, log,db)
    if config['acceptance_labeling']:
        results = labeling(results,log)

    if config["output_SQL"]:
        db.insert_dict(results)

    if config["output_json"]:
        if not os.path.exists(config["outdir"]):
            os.makedirs(config["outdir"])
        with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
            json.dump(results, file_handle, indent=config["json_indent"])
