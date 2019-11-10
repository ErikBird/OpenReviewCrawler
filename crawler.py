import argparse
import json
import os
from datetime import date
import re
import openreview
import requests
import logging
import sys
import progressbar
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import selenium.webdriver.support.ui as ui
import time

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
                        # see https://openreview-py.readthedocs.io/en/latest/get_submission_invitations.html to verify
                        log.info("Submission invitation")
                        forum_idx_map.update({n["forum"]: i+len(submissions) for i, n in enumerate(notes)})
                        for n in notes:
                            n["revisions"] = get_submission_revisions(n["id"], driver)
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

    with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
        json.dump(results, file_handle, indent=config["json_indent"])


def start_webdriver():
    options = Options()
    options.headless = True
    try:
        driver = webdriver.Firefox(options=options,
                                   executable_path=config['geckodriver'])
    except:
        print(
            'The webdriver has not been setup correctly! Please follow the README Installation instructions to setup the geckodriver.')
    return driver


def merge_invitations(invitations):
    new_invitations = set()
    for inv in invitations:
        sub1 = re.sub(r"/(P|p)aper[0-9]+/", r"/\1aper.*/", inv)
        sub2 = re.sub(r"/(P|p)aper/[0-9]+/", r"/\1aper/.*/", sub1)
        new_invitations.add(sub2)
    return new_invitations


def get_submission_revisions(id, driver):
    my_url = 'http://openreview.net/revisions?id='+id
    driver.get(my_url)

    wait = ui.WebDriverWait(driver, 10)
    try:
        wait.until(lambda driver: driver.find_element_by_class_name('note_content_pdf'))
    except:
        log.error(id+' id causes a timeout')

    revisions = []
    for revision in driver.find_elements_by_class_name('note'):
        title = revision.find_element_by_class_name('note_content_title').text
        try:
            pdf = revision.find_element_by_class_name('note_content_pdf').get_attribute('href')
        except:
            pdf = 'NoPDF'
            log.error(id + ' provides no PDF')
            pass
        authors = [p.text for p in revision.find_elements_by_class_name('profile-link')]
        date = revision.find_element_by_class_name('date').text
        notes = [p.text for p in revision.find_elements_by_class_name('note_contents')]
        revisions.append({'title': title, 'pdf': pdf, 'authors': authors, 'date': date, 'pdf': pdf, 'notes': notes})

    return revisions


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

    args = parser.parse_args()
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    try:
        config = json.load(open(args.config))
    except:
        print('The configuration File has not been found. \n Please Make sure it is correctly Named \'config.json\' and is located in the project root foulder.\n Otherwise please specify the configuration Path with the parser argument \'-c PATH\'')

    '''
    print("Available venues:")
    c = openreview.Client(baseurl='https://openreview.net')
    venues = openreview.tools.get_all_venues(c)
    print(*venues, sep="\n")
    '''

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

    crawl(client, config,log)

