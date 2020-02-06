import argparse
import json
import os
import re
import logging
import sys
import progressbar


def labeling(data_dict,log):
    """
    Tag a given JSON file for acceptance/rejection/withdrawal/unknwon
    :param dict: Dictionary of the crawled data to be tagged
    :param log: logger
    """
    for venue_year in data_dict:
        log.info("Tagging {} {}".format(venue_year["venue"], venue_year["year"]))
        for submission in progressbar.progressbar(venue_year["submissions"]):
            # First check if submission was withdrawn
            if "withdraw" in submission["invitation"].lower():
                submission["acceptance_tag"] = "withdrawn"
            else:
                # Venues in 2013 and 2014 often have the decision in the content of the submission
                if "decision" in submission["content"]:
                    log.debug("{} has decision in content".format(submission["forum"]))
                    if "reject" in submission["content"]["decision"].lower() and "accept" in submission["content"]["decision"].lower():
                        log.debug(
                            "Forum {}. Tagged as unknown because decision is unclear. Decision: {}".format(
                                submission["forum"], submission["content"]["decision"]))
                        submission["acceptance_tag"] = "unknown"
                    elif "reject" in submission["content"]["decision"].lower():
                        submission["acceptance_tag"] = "rejected"
                    elif "accept" in submission["content"]["decision"].lower():
                        submission["acceptance_tag"] = "accepted"
                    else:
                        # exclude ICLR 2014 from this choice
                        if not (venue_year["venue"] == "ICLR.cc" and venue_year["year"] == 2014):
                            log.debug(
                                "Forum {}. Tagged as accepted because not rejected. This might be wrong. Decision: {}".format(
                                    submission["forum"], submission["content"]["decision"]))
                            submission["acceptance_tag"] = "accepted"
                        else:
                            submission["acceptance_tag"] = "unknown"
                else:
                    for note in submission["notes"]:
                        # Only found in ICLR 2020 as far as we are aware
                        if "desk_reject" in note["invitation"].lower():
                            log.debug("{} was desk rejected".format(submission["forum"]))
                            submission["acceptance_tag"] = "rejected"

                        # Found a decicion note
                        if "decision" in note["invitation"].lower() or "acceptance" in note["invitation"].lower():
                            log.debug("{} has decision note".format(submission["forum"]))
                            # We consider a submission accepted if it is not rejected. This is due to some venues only writing
                            # for what a submission is accepted (poster, talk, workshop) without writing the word 'accept'.
                            # 'Reject' is found in all rejected submission decisions (as far as we are aware).
                            for key in note["content"]:
                                # Naming varies for the fild. Both decision and acceptance decision exist.
                                if "decision" in key.lower():
                                    if "reject" in note["content"][key].lower() and "accept" in note["content"][key].lower():
                                        log.debug(
                                            "Forum {}. Tagged as unknown because decision is unclear. Decision: {}".format(
                                                submission["forum"], note["content"][key]))
                                        submission["acceptance_tag"] = "unknown"
                                    elif "reject" in note["content"][key].lower():
                                        submission["acceptance_tag"] = "rejected"
                                    elif "accept" in note["content"][key].lower():
                                        submission["acceptance_tag"] = "accepted"
                                    else:
                                        log.debug(
                                            "Forum {}. Tagged as accepted because not rejected. This might be wrong. Decision: {}".format(
                                                submission["forum"], note["content"][key]))
                                        submission["acceptance_tag"] = "accepted"
                            break
                        # Found a meta review
                        # This will not stop the loop unlike a decision note in case both are used for some reason
                        # Currently, only ICLR 2019 and an ICAPS 2019 workshop uses meta reviews as far as we know.
                        elif "meta" in note["invitation"].lower():
                            log.debug("{} has meta review note".format(submission["forum"]))
                            try:
                                if "reject" in note["content"]["recommendation"].lower():
                                    submission["acceptance_tag"] = "rejected"
                                elif "accept" in note["content"]["recommendation"].lower():
                                    submission["acceptance_tag"] = "accepted"
                                else:
                                    submission["acceptance_tag"] = "unknown"
                                    log.debug("Forum {}. Meta review without decision".format(submission["forum"]))
                            except KeyError:
                                submission["acceptance_tag"] = "unknown"
                                log.debug("Forum {}. Unexpected format of a meta review note.".format(submission["forum"]))
                # Some venues use simple comments for the decision. We ignore them because the invitation is not
                # exclusively used for the decision so the false classification risk is too high.
                if not "acceptance_tag" in submission:
                    log.debug("Forum {}. No decision could be found.".format(submission["forum"]))
                    submission["acceptance_tag"] = "unknown"
    return data_dict


if __name__ == "__main__":
    log = logging.getLogger("acceptance_tagging")
    log.addHandler(logging.StreamHandler())
    progressbar.streams.wrap_stderr()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--file', required=False, help='JSON created by crawler.py which should get tagged')
    parser.add_argument(
        "--write_new_file", "-w", help="Write the output in a new JSON with the given path. Otherwise the input file is overwritten"
    )
    parser.add_argument(
        "--logging_level", help="Logging level", default="INFO"
    )
    args = parser.parse_args()
    log.setLevel(logging.getLevelName(args.logging_level))
    if args.file:
        with open(args.file, "r") as f:
            json_file = json.load(f)
            label = labeling(json_file,log)
            if args.write_new_file:
                with open(args.write_new_file, "w") as f:
                    json.dump(json_file, f, indent=3)
            else:
                json.dump(json_file, f, indent=3)
