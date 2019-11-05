import argparse
import json
import os
from datetime import date
import re
import openreview
import requests

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import selenium.webdriver.support.ui as ui

def crawl(client, config):
    results = []
    for target in config["targets"]:
        venue, years = target["venue"], target["years"]
        if years == "all":
            years = range(2000, date.today().year + 2)
        for year in years:
            invitations_iterator = openreview.tools.iterget_invitations(client, regex="{}/{}/".format(venue, year))
            invitations = [inv.id for inv in invitations_iterator]
            invitations = merge_invitations(invitations)
            if not invitations:
                continue
            else:
                invs = []
                for inv in invitations:
                    invs.append({"invitation": inv,
                                        "notes": [note.to_json() for note in openreview.tools.iterget_notes(client, invitation=inv)]})
                results.append({"venue": venue, "year": year, "invitations": invs})

    with open(os.path.join(config["outdir"], config["filename"]), 'w') as file_handle:
        json.dump(results, file_handle, indent=config["json_indent"])

def merge_invitations(invitations):
    new_invitations = set()
    for inv in invitations:
        sub1 = re.sub(r"/(P|p)aper[0-9]+/", r"/\1aper.*/", inv)
        sub2 = re.sub(r"/(P|p)aper/[0-9]+/", r"/\1aper/.*/", sub1)
        new_invitations.add(sub2)
    return new_invitations


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--config', help='configuration for the crawling', default='config.json')
    parser.add_argument(
        '-p', '--password', help='password for the username given in the config. Overwrites password in config')
    parser.add_argument('--baseurl', default='https://openreview.net')

    args = parser.parse_args()

    try:
        config = json.load(open(args.config))
    except:
        print('The configuration File has not been found. \n Please Make sure it is correctly Named \'config.json\' and is located in the project root foulder.\n Otherwise please specify the configuration Path with the parser argument \'-c PATH\'')

    print("Available venues:")
    c = openreview.Client(baseurl='https://openreview.net')
    venues = openreview.tools.get_all_venues(c)
    print(*venues, sep="\n")

    my_url = 'http://openreview.net/revisions?id=ryQu7f-RZ'
    options = Options()
    options.headless = True
    try:
        driver = webdriver.Firefox(options=options,
                                   executable_path=config['geckodriver'])
    except:
        print('The webdriver has not been setup correctly! Please follow the README Installation instructions to setup the geckodriver.')


    # driver = webdriver.PhantomJS('Resources/phantomjs-2.1.1-linux-x86_64/bin/phantomjs')
    driver.get(my_url)
    wait = ui.WebDriverWait(driver, 10)
    wait.until(lambda driver: driver.find_element_by_class_name('row'))
    print(driver.find_element_by_class_name('row'))

    for elm in driver.find_elements_by_class_name('title_pdf_row clearfix'):
        print(elm.text)


    '''
    if args.config is None:

        print("Available venues:")
        c = openreview.Client(baseurl='https://openreview.net')
        venues = openreview.tools.get_all_venues(c)
        print(*venues, sep="\n")

        my_url = 'http://openreview.net/revisions?id=ryQu7f-RZ'
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options, executable_path=r'/home/erikschwan/PycharmProjects/OpenReviewCrawler/geckodriver')
        #driver = webdriver.PhantomJS('Resources/phantomjs-2.1.1-linux-x86_64/bin/phantomjs')
        driver.get(my_url)
        wait = ui.WebDriverWait(driver, 10)
        wait.until(lambda driver: driver.find_element_by_class_name('row'))
        print(driver.find_element_by_class_name('row'))
        for elm in driver.find_elements_by_class_name('title_pdf_row clearfix'):
           print(elm.text)
        #response = session.body()
        #soup = BeautifulSoup(response)
        #print(soup.find(id="note_Syax5XD9M"))
        #response = c.__handle_response(response)
        #for t in response.json()['tags']:
        #   print(t)

    else:
        config = json.load(open(args.config))
        my_url = 'http://openreview.net/revisions?id=ryQu7f-RZ'
        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options,
                                   executable_path=config['geckodriver'])
        # driver = webdriver.PhantomJS('Resources/phantomjs-2.1.1-linux-x86_64/bin/phantomjs')
        driver.get(my_url)
        wait = ui.WebDriverWait(driver, 10)
        wait.until(lambda driver: driver.find_element_by_class_name('row'))
        print(driver.find_element_by_class_name('row'))

        for elm in driver.find_elements_by_class_name('title_pdf_row clearfix'):
            print(elm.text)

        username = config["username"]
        if args.password is not None:
            password = args.password
        else:
            password = config["password"]

        client = openreview.Client(
            baseurl='https://openreview.net',
            username=username,
            password=password)

        crawl(client, config)
        '''