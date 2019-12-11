import json
import argparse
import os


def comment_tree(file):
    with open(file, "r") as f:
        jfile = json.load(f)
    results = []
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


def find_forum(file, name):
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
    tree_notes = create_comment_tree(forum_notes)
    if not sub:
        print("No forum named ", name, " found.")
    else:
        return sub, tree_notes


def draw_forum(file, name):
    submission, tree_notes = find_forum(file, name)
    print("--> " + submission["forum"] + " : "
          + submission["content"]["title"])
    for notes in tree_notes:
        draw_note(notes, "")


def draw_note(note, prefix):
    print(prefix, "|---", note["id"])
    prefix += "\t"
    for n in note["replies"]:
        draw_note(n, prefix)


if __name__ == "__main__":
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
