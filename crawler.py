import argparse
import json
import os
from datetime import date
import re
import openreview
import logging
import sys
import progressbar


def crawl(client, config, log):
    results = []
    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            log.info('Current Download: '+venue+' in '+str(year))
            invitations_iterator = openreview.tools.iterget_invitations(client, regex="{}/{}/".format(venue, year))
            invitations = [inv.id for inv in invitations_iterator]
            invitations = merge_invitations(invitations)
            if not invitations:
                log.warning('No data for'+venue+' in '+str(year))
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
                            n["revisions"] = download_revisions(n["id"], client=client)
                            n["notes"] = []
                        submissions.extend(notes)
                    else:
                        revisions = [r.to_json() for r in client.get_references(invitation=inv)]
                        for note in notes:
                            note["revisions"] = [r for r in revisions if r["referent"] == note["id"]]
                        other_notes.extend(notes)
                if not submissions:
                    log.warning('No submissions found for '+venue+' in '+str(year))
                    continue
                else:
                    tree_notes = []
                    for forum in forum_idx_map:
                        forum_notes = [note for note in other_notes if note["forum"] == forum]
                        tree_notes.extend(create_comment_tree(forum_notes))

                    for note in tree_notes:
                        try:
                            submissions[forum_idx_map[note["forum"]]]["notes"].append(note)
                        except KeyError:
                            log.info("No submission found for note " + note["id"] + " in forum " + note["forum"])
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


def download_revisions(note_id, client):
    references = client.get_references(note_id, original=True)
    out_path = os.path.join(config["outdir"], 'pdf/')
    if not os.path.exists(out_path):
        os.makedirs(out_path)
    for index, r in enumerate(references):
        pdf = note_id + '_' + str(index) + '.pdf'
        with open(os.path.join(out_path, pdf), "wb") as file1:
            file1.write(client.get_pdf(r.id, is_reference=True))
        log.info(pdf + ' downloaded')
    return references


def get_all_available_venues():
    print("Available venues:")
    c = openreview.Client(baseurl='https://openreview.net')
    venues = openreview.tools.get_all_venues(c)
    print(*venues, sep="\n")


def create_comment_tree(forum_notes):
    root_notes = []
    leaf_notes = []
    for i, note in enumerate(forum_notes):
        note["replies"] = []
        # find parent nodes (direct replies to a submission) = root nodes in forum
        if note["replyto"] == note["forum"]:
            # append to root
            root_notes.append(note)
        else:
            # if note is not a root, it will be in the remaining tree
            leaf_notes.append(note)
    stop = False
    # check in each iteration if there are still children not attached
    # new leaf_notes are subtrees where children are already appended
    while not stop and leaf_notes:
        children, stop = has_children(leaf_notes)
        leaf_notes = insert_children(children)

    # attach all subtrees to the roots (lone leafs are left out, assume mistake in crawling)
    for leaf in leaf_notes:
        for r in root_notes:
            if r["id"] == leaf["replyto"]:
                r["replies"].append(leaf)
    return root_notes


def has_children(notes):
    children = []
    # if there are no more lone children, stop
    stop = True
    for note in notes:
        c = False
        for n in notes:
            if note["id"] == n["replyto"]:
                # label child as "hasChild = true"
                c = True
                # as long as one note is a child, do not stop
                stop = False
        children.append((note, c))
    return children, stop


def insert_children(children):
    combined_notes = [child[0] for child in children]
    for child in children:
        # if no more children, insert at parent -> assume is last comment
        if not child[1]:
            # find parent and append
            for note in combined_notes:
                if note["id"] == child[0]["replyto"]:
                    note["replies"].append(child[0])
                    combined_notes.remove(child[0])
    return combined_notes


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

    if args.help_venues:
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
