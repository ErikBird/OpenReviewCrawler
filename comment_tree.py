import json
import argparse
import os
import logging


def comment_tree(file):
    """
    Transform a given output from crawler.py into a similar version that has comments to submissions
    nested as replies instead of in a flat structure. Replies to replies may occur.
    :param file: path to json file, conforms to crawler.py output
    """
    with open(file, "r") as f:
        jfile = json.load(f)
    results = []
    log.info("Transforming file %s to comment tree structure", file)
    for v in jfile:
        venue = v["venue"]
        year = v["year"]
        submissions = []
        for sub in v["submissions"]:
            tree_notes = create_comment_tree(sub["notes"])
            sub["notes"] = tree_notes
            submissions.append(sub)
        results.append({"venue": venue, "year": year, "submissions": submissions})

        with open(os.path.splitext(file)[0] + "_comment_tree.json", 'w') as new_file:
            json.dump(results, new_file, indent=3)
            log.info("Written new file %s_comment_tree.json", os.path.splitext(file)[0])


def create_comment_tree(forum_notes):
    """
    Create a tree structure for 1 Forum, given the notes in that forum.
    Return a list of notes which are parent/root notes.
    param forum_notes: list of notes for 1 forum
    """
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
        children, stop = __has_children(leaf_notes)
        leaf_notes = __insert_children(children)

    # attach all subtrees to the roots (lone leafs are left out, assume mistake in crawling)
    for leaf in leaf_notes:
        for r in root_notes:
            if r["id"] == leaf["replyto"]:
                r["replies"].append(leaf)
    return root_notes


def __has_children(notes):
    # check if there are still children left to be appended
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


def __insert_children(children):
    # insert children that are tagged to be inserted
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


def __find_forum(file, name):
    # find the notes to a forum by its name
    # assumes the name is a unique forum ID in the file
    with open(file, "r") as f:
        jfile = json.load(f)
    sub = None
    forum_notes = []
    for venue in jfile:
        for submission in venue["submissions"]:
            if submission["forum"] == name:
                forum_notes = submission["notes"]
                sub = submission
                break

    if sub is None:
        log.error("No forum named %s found.", name)
        exit()
    else:
        # create tree structure notes for the forum
        tree_notes = create_comment_tree(forum_notes)
        # return submission and tree structured notes
        return sub, tree_notes


def draw_forum(file, name):
    """
    Visualize the tree structure for 1 Forum, given the ID of the forum on OpenReview.net
    :param file: path to json file, conforms to crawler.py output
    :param name: ID of the forum
    """
    # get submission and corresponding notes
    submission, tree_notes = __find_forum(file, name)
    log.info("-->  %s : %s ", submission["forum"], submission["content"]["title"])
    for notes in tree_notes:
        __draw_note(notes, "")


def __draw_note(note, prefix):
    log.info("%s|--- %s", prefix, note["id"])
    prefix += "    "
    for n in note["replies"]:
        __draw_note(n, prefix)


if __name__ == "__main__":
    log = logging.getLogger("comment_tree")
    log.setLevel(logging.INFO)
    log.addHandler(logging.StreamHandler())
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", required=True, help="Input file created by crawler")
    parser.add_argument("--forum", default="all", help="If only one forum should be parsed into a tree, "
                                                       "state the wanted forum ID. e.g. --forum 'HkghWScuoQ' "
                                                       "Will only draw a tree, not create a file")
    args = parser.parse_args()

    if args.forum is not "all":
        draw_forum(args.file, args.forum)
    else:
        comment_tree(args.file)
