

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
