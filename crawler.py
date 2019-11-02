import argparse
import json
import os
from datetime import date
import re
import openreview


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
        '-c', '--config', help='configuration for the crawling')
    parser.add_argument(
        '-p', '--password', help='password for the username given in the config. Overwrites password in config')
    parser.add_argument('--baseurl', default='https://openreview.net')

    args = parser.parse_args()

    if args.config is None:
        print("Available venues:")
        c = openreview.Client(baseurl='https://openreview.net')
        venues = openreview.tools.get_all_venues(c)
        print(*venues, sep="\n")

    else:
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

        crawl(client, config)