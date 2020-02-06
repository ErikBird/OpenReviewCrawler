import numpy as np
from matplotlib import pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns; sns.set()
#from sklearn.neighbors import KernelDensity
import json

def get_info(file_name):
    with open(file_name) as f:
        j = json.load(f)

    info_per_venue_year = {}
    comments_per_submission = []
    revisions_per_submission = []
    for v in j:
        if len(v["submissions"]) > 0:
            if v["venue"] not in info_per_venue_year:
                info_per_venue_year[v["venue"]] = {}
            info_per_venue_year[v["venue"]][v["year"]] = {"sub": len(v["submissions"]),
                                                          "accepted": 0, "rejected": 0, "withdrawn": 0, "unknown": 0,
                                                          "comments_per_submission": [], "revisions_per_submission": [],
                                                          "plain_comment": 0, "review": 0, "decision": 0, "other": 0}
            for s in v["submissions"]:
                comments_per_submission.append(len(s["notes"]))
                revisions_per_submission.append(len(s["revisions"]))
                info_per_venue_year[v["venue"]][v["year"]]["comments_per_submission"].append(len(s["notes"]))
                info_per_venue_year[v["venue"]][v["year"]]["revisions_per_submission"].append(len(s["revisions"]))
                if s["acceptance_tag"] == "accepted":
                    info_per_venue_year[v["venue"]][v["year"]]["accepted"] += 1
                elif s["acceptance_tag"] == "rejected":
                    info_per_venue_year[v["venue"]][v["year"]]["rejected"] += 1
                elif s["acceptance_tag"] == "withdrawn":
                    info_per_venue_year[v["venue"]][v["year"]]["withdrawn"] += 1
                elif s["acceptance_tag"] == "unknown":
                    info_per_venue_year[v["venue"]][v["year"]]["unknown"] += 1
                for n in s["notes"]:
                    inv = n["invitation"].lower()
                    if "review" in inv:
                        info_per_venue_year[v["venue"]][v["year"]]["review"] += 1
                    elif "comment" in inv:
                        info_per_venue_year[v["venue"]][v["year"]]["plain_comment"] += 1
                    elif "decision" in inv or "acceptance" in inv:
                        info_per_venue_year[v["venue"]][v["year"]]["decision"] += 1
                    else:
                        info_per_venue_year[v["venue"]][v["year"]]["other"] += 1
    return info_per_venue_year, comments_per_submission, revisions_per_submission

def plot_label_heatmap(data):
    venues = ["{} {}".format(k1, k2) for k1 in data for k2 in data[k1]]
    labels = ["accepted", "rejected", "withdrawn", "unknown"]
    matrix = np.array([[data[k1][k2][l]/data[k1][k2]["sub"] for l in labels] for k1 in data for k2 in data[k1]])

    fig, ax = plt.subplots(figsize=(14,10))
    im = ax.imshow(matrix, cmap="plasma")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(venues)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(venues)

    ax.grid(False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(venues)):
        for j in range(len(labels)):
            text = ax.text(j, i, " {:.1f} ".format(matrix[i, j]),
                           ha="center", va="center", color="w")
    ax.set_title("Acceptance label distribution for each venue")
    fig.tight_layout()
    fig.savefig("resources/label_fig.svg", bbox_inches="tight", )
    #plt.show()

def plot_comment_type_heatmap(data):
    venues = ["{} {}".format(k1, k2) for k1 in data for k2 in data[k1]]
    labels = ["plain_comment", "review", "decision", "other"]
    matrix = np.array([[0.0
                        if sum(data[k1][k2]["comments_per_submission"]) == 0
                        else data[k1][k2][l]/sum(data[k1][k2]["comments_per_submission"])
                             for l in labels] for k1 in data for k2 in data[k1]])

    fig, ax = plt.subplots(figsize=(14,10))
    im = ax.imshow(matrix, cmap="plasma")
    ax.set_xticks(np.arange(len(labels)))
    ax.set_yticks(np.arange(len(venues)))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(venues)

    ax.grid(False)

    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations.
    for i in range(len(venues)):
        for j in range(len(labels)):
            text = ax.text(j, i, " {:.1f} ".format(matrix[i, j]),
                           ha="center", va="center", color="w")
    ax.set_title("Comment type distribution for each venue")
    fig.tight_layout()
    fig.savefig("resources/comment_type_heatmap.svg", bbox_inches="tight", )
    #plt.show()

def autolabel(rects, ax):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

def plot_sub_venue(data, reduce_year=True):
    if reduce_year:
        labels = ["{}".format(k1) for k1 in data]
        subs = [sum([data[k1][k2]["sub"] for k2 in data[k1]]) for k1 in data]
    else:
        labels = ["{} {}".format(k1, k2) for k1 in data for k2 in data[k1]]
        subs = [data[k1][k2]["sub"] for k1 in data for k2 in data[k1]]

    order = np.argsort(subs)
    nl = []
    ns = []
    for i in order:
        nl.append(labels[i])
        ns.append(subs[i])
    labels = nl
    subs = ns

    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    fig, ax = plt.subplots(figsize=(11, 6))
    rects1 = ax.bar(x, subs, width)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Submissions')
    ax.set_title('Submissions for each venue')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ymin, ymax = plt.ylim()
    plt.ylim(ymin, ymax+500)
    autolabel(rects1, ax)

    fig.tight_layout()

    if reduce_year:
        fig.savefig("resources/venue_sub_bar.svg", bbox_inches="tight", )
    else:
        fig.savefig("resources/venueyear_sub_bar.svg", bbox_inches="tight", )

    #plt.show()

def plot_comment_venue(data, reduce_year=True):
    fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(11, 8))
    if reduce_year:
        labels = ["{}".format(k1) for k1 in data]
        comments = [np.concatenate([data[k1][k2]["comments_per_submission"] for k2 in data[k1]]) for k1 in data]
    else:
        labels = ["{} {}".format(k1, k2) for k1 in data for k2 in data[k1]]
        comments = [data[k1][k2]["comments_per_submission"] for k1 in data for k2 in data[k1]]
    sum_comments = [sum(c) for c in comments]

    order = np.argsort(sum_comments)
    nl = []
    nc = []
    nsc = []
    for i in order:
        nl.append(labels[i])
        nc.append(comments[i])
        nsc.append(sum_comments[i])
    labels = nl
    comments = nc
    sum_comments = nsc

    # plot violin plot
    ax = axes[0]
    ax.violinplot(comments,
                       showmeans=False,
                       showmedians=True)
    ax.set_title('Comment distribution and total comments for each venue')

    ax.yaxis.grid(True)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.set_xticks([y + 1 for y in range(len(comments))])
    ax.set_ylabel('Comments per submission')
    plt.setp(ax.get_xticklabels(), visible=False)
    # bar plot
    ax = axes[1]
    x = np.arange(len(labels))  # the label locations
    width = 0.35  # the width of the bars
    rects1 = ax.bar(x, sum_comments, width)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Total comments')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ymin, ymax = plt.ylim()
    plt.ylim(ymin, ymax+500)
    autolabel(rects1, ax)

    fig.tight_layout()
    if reduce_year:
        fig.savefig("resources/venue_comment_distribution.svg", bbox_inches="tight", )
    else:
        fig.savefig("resources/venueyear_comment_distribution.svg", bbox_inches="tight", )

    #plt.show()

def plot_revision_venue(data, reduce_year=True):
    fig, ax = plt.subplots(figsize=(11, 8))
    if reduce_year:
        labels = ["{}".format(k1) for k1 in data]
        revisions = [np.concatenate([data[k1][k2]["revisions_per_submission"] for k2 in data[k1]]) for k1 in data]
    else:
        labels = ["{} {}".format(k1, k2) for k1 in data for k2 in data[k1]]
        revisions = [data[k1][k2]["revisions_per_submission"] for k1 in data for k2 in data[k1]]
    sum_revisions = [sum(c) for c in revisions]

    order = np.argsort(sum_revisions)
    nl = []
    nc = []
    nsc = []
    for i in order:
        nl.append(labels[i])
        nc.append(revisions[i])
        nsc.append(sum_revisions[i])
    labels = nl
    revisions = nc
    sum_revisions = nsc

    # plot violin plot
    ax.violinplot(revisions,
                  showmeans=False,
                  showmedians=True)
    ax.set_title('Revision distribution for each venue')

    ax.yaxis.grid(True)
    ax.yaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.set_xticks([y + 1 for y in range(len(revisions))])
    ax.set_ylabel('Revisions per submission')
    ax.set_xticklabels(labels)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    fig.tight_layout()
    if reduce_year:
        fig.savefig("resources/venue_revision_distribution.svg", bbox_inches="tight", )
    else:
        fig.savefig("resources/venueyear_revision_distribution.svg", bbox_inches="tight", )

    #plt.show()

def plot_comment_distribution(cps, bandwidth=0.5, filter=30):
    fig, ax = plt.subplots(figsize=(10, 6))

    cps = [c for c in cps if c<=filter]
    #x = np.linspace(np.min(cps), np.max(cps), 1000)[:, np.newaxis]
    #kde = KernelDensity(kernel='tophat', bandwidth=bandwidth).fit(np.array(cps).reshape(-1, 1))
    #log_dens = kde.score_samples(x)
    #plt.fill_between(x[:, 0], np.exp(log_dens), alpha=0.5)

    bins = np.arange(0, filter+2)-0.5
    ax.hist(cps, bins=bins, density=True)

    ax.set_xlabel('Comments per submission')
    ax.set_xticks(np.arange(0, filter))
    ax.set_ylabel('Density')
    ax.set_title('Distribution of Comments')

    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    fig.savefig("resources/comment_distribution.svg", bbox_inches="tight", )
    #plt.show()

def plot_revision_distribution(rps, bandwidth=0.5, filter=30):
    fig, ax = plt.subplots(figsize=(10, 6))
    rps = [r for r in rps if r<=filter]
    #x = np.linspace(np.min(cps), np.max(cps), 1000)[:, np.newaxis]
    #kde = KernelDensity(kernel='tophat', bandwidth=bandwidth).fit(np.array(cps).reshape(-1, 1))
    #log_dens = kde.score_samples(x)
    #plt.fill_between(x[:, 0], np.exp(log_dens), alpha=0.5)

    bins = np.arange(0, filter+2)-0.5
    ax.hist(rps, bins=bins, density=True)

    ax.set_xlabel('Revisions per submission')
    ax.set_xticks(np.arange(0, filter))
    ax.set_ylabel('Density')
    ax.set_title('Distribution of Revisions')

    # Tweak spacing to prevent clipping of ylabel
    fig.tight_layout()
    fig.savefig("resources/revision_distribution.svg", bbox_inches="tight", )
    #plt.show()

def print_stats(data, cps, rps):
    # total
    print("{} submissions".format(len(cps)))
    print("{} comments".format(np.sum(cps)))
    print("{} revisions".format(np.sum(rps)))

    for s in ["plain_comment", "review", "decision", "other"]:
        total = sum([sum([data[k1][k2][s] for k2 in data[k1]]) for k1 in data])
        print("{} {}".format(total, s))

if __name__ == "__main__":
    data, cps, rps = get_info("all20200302/out.json")
    #print_stats(data, cps, rps)
    plot_label_heatmap(data)
    plot_sub_venue(data, True)
    plot_sub_venue(data, False)
    plot_comment_venue(data, True)
    plot_comment_venue(data, False)
    plot_revision_venue(data, True)
    plot_revision_venue(data, False)
    plot_comment_distribution(cps)
    plot_revision_distribution(rps)
    #plot_comment_type_heatmap(data)