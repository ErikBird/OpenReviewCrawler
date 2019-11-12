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

def crawl(client, config,log):
    results = []
    driver  = start_webdriver()
    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            log.info('Current Download:'+ venue+' in '+str(year))
            invitations_iterator = openreview.tools.iterget_invitations(client, regex="{}/{}/".format(venue, year))
            invitations = [inv.id for inv in invitations_iterator]
            invitations = merge_invitations(invitations)
            if not invitations:
                log.warning('No Data for'+ venue+' in '+str(year))
                continue
            else:
                invs = []
                for inv in progressbar.progressbar(invitations):
                    notes = [note for note in openreview.tools.iterget_notes(client, invitation=inv)]
                    revisions = []
                    for n in notes:
                        revisions.append(get_revisions(n.id,driver))

                    invs.append({"invitation": inv,
                                        "notes": [note.to_json() for note in notes],
                                 'revisions': [json.dumps(rev) for  rev in revisions if revisions]})
                results.append({"venue": venue, "year": year, "invitations": invs})

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

def get_revisions(id,driver):
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

    args = parser.parse_args()
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    try:
        config = json.load(open(args.config))
    except:
        print('The configuration File has not been found. \n Please Make sure it is correctly Named \'config.json\' and is located in the project root foulder.\n Otherwise please specify the configuration Path with the parser argument \'-c PATH\'')


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
