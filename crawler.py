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
import copy
def crawl(client, config, log, db=None):
    '''
    This method crawls the configured venues and saves all comments and all PDF Revisions to the output folder.

    :param client: the openreview client
    :param config: the config dictionary
    :param log: the configured logging client
    :return: Nothing
    '''
    already_done = set([])
    sql_venue_to_id ={}
    results = []
    venue_id = 0
    tmp_venue_id = -1
    if config["output_json"]:
        if os.path.exists(os.path.join(config["outdir"], config["filename"])):
            with open(os.path.join(config["outdir"], config["filename"]), 'r') as file_handle:
                log.info('previous file successfully loaded')
                results = json.load(file_handle)
                already_done = set(["{} {}".format(r["venue"], r["year"]) for r in results])
    elif config["output_SQL"]:
        venues = db.get_venues()
        if venues:
            for v in venues:
                sql_venue_to_id["{} {}".format(v["venue"], v["year"])]=v['id']


    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            if "{} {}".format(venue, year) in already_done:
                log.info("Skipping {} {}. Already done".format(venue, year))
                continue
            if "{} {}".format(venue, year) in sql_venue_to_id:
                log.debug("Overrive Venue "+"{} {}".format(venue, year)+" from Database")
                tmp_venue_id = sql_venue_to_id["{} {}".format(venue, year)]
            else:
                while True:
                    if venue_id in sql_venue_to_id.values():
                        venue_id = + 1
                    else:break
                sql_venue_to_id["{} {}".format(venue, year)]=venue_id
                tmp_venue_id = venue_id
                log.debug("New Venue " + "{} {}".format(venue, year)+" ID: "+str(venue_id))

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
                            try:
                                refs = client.get_references(n["id"], original=True)
                            except:
                                log.error("Request Error for ID: "+str(n["id"]))
                            references=[r.to_json() for r in refs[1:]]
                            n["revisions"] = references
                            n["notes"] = []
                            if len(refs) > 0 :
                                #print(refs[0].to_json()['content'].keys())
                                if "pdf" in  refs[0].to_json()['content'].keys():
                                    original = refs[:1][0]
                                    if not config["skip_pdf_download"]:
                                        download_manager(n, original, venue_id, references, threads)
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
            results.append({"venue_id":sql_venue_to_id["{} {}".format(venue, year)],"venue": venue, "year": year, "submissions": submissions})

    return (results,threads)


def download_manager(n,original,venue_id,references,threads):
    if config["output_json"]:
        pdf_name = n["id"] + '_' + str(0) + '.pdf'
        n['content']['pdf'] = '/pdf/' + pdf_name
        if config["threaded_download"]:
            x = threading.Thread(target=download_revision_fs, args=(original.id, pdf_name, client))
            threads.append(x)
            x.start()
        else:download_revision_fs(original.id, pdf_name, client)
    if config["output_SQL"]:
        if config["threaded_download"]:
            x = threading.Thread(target=download_submission_db, args=(original.id, client, db, venue_id, n["id"]))
            threads.append(x)
            x.start()
        else:download_submission_db(original.id, client, db, venue_id, n["id"])

    for index, r in enumerate(references):
        if config["output_json"]:
            pdf_name = n["id"] + '_' + str(index + 1) + '.pdf'
            r['content']['pdf'] = '/pdf/' + pdf_name
            if config["threaded_download"]:
                x = threading.Thread(target=download_revision_fs, args=(r['id'], pdf_name, client))
                threads.append(x)
                x.start()
            else:download_revision_fs(r['id'], pdf_name, client)
        if config["output_SQL"]:
            if config["threaded_download"]:
                x = threading.Thread(target=download_revision_db, args=(r['id'], client, db, n["id"]))
                threads.append(x)
                x.start()
            else:download_revision_db(r['id'], client, db, n["id"])

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

def download_revision_db(ref_id, client, db ,submission_id):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''
    if not ref_id: return
    try:
        file = client.get_pdf(ref_id, is_reference=True)
    except:
        log.info(ref_id + ' has no pdf ')
        return
    db.insert_revision(ref_id, submission_id, pdf=file)


def download_submission_db(ref_id, client, db, venue_id,submission_id):
    '''
    This method downloads a pdf file from a openreview note and stores it in the oupath/pdf/ folder.
    If the folder does not exist, it will be created.
    :param ref_id: The target note id
    :param pdf_name: The target filename
    :param client: The openreview client
    :return: Nothing
    '''
    if not ref_id: return
    try:
        file = client.get_pdf(ref_id, is_reference=True)
    except:
        log.info(ref_id + ' has no pdf ')
        return
    db.insert_submission( venue_id,submission_id,pdf=file)


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
        db.start()
        #x = threading.Thread(target=db.run())



    results,threads = crawl(client, config, log,db)
    if config['acceptance_labeling']:
        results = labeling(results,log)

    if config["output_SQL"]:
        while any(thread.is_alive() for thread in threads) and not db.q.empty():
            log.info('PDF Download Threads still active')
            time.sleep(1)

        db.insert_dict(results)
        db.close()
        while db.is_alive() :
            log.info('SQL Insertion still active, Queue Size: '+ str(db.q.qsize()))
            time.sleep(1)

    if config["output_json"]:
        if not os.path.exists(config["outdir"]):
            os.makedirs(config["outdir"])
        with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
            json.dump(results, file_handle, indent=config["json_indent"])
