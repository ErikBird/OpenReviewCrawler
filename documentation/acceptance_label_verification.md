# Verification of our acceptance labeling approach

We cannot check if the label is correct for each submission.
Thus we can only check for a sample of submissions.

## Approach

We gather the samples as follows:  
We manually iterate over all venues and years containing submissions on the OpenReview website.  
If a venue at a year has subpages (i.e. conferences, workshops etc), we iterate over each.  
Then for each venue or subpage, we search for at least one accepted and rejected paper (and a withdrawn submission if they exist).  
Finally, we check if the submission is labeled correctly.

## Conclusion
Our verification suggests that the labels "accept", "reject" and "withdrawn" are correct.  
The "unknown" label is correct in all but three cases and caused by lack of a decision or no comments entirely. 
The three cases are labeled unknown on purpose as they can cause false positives.

## In-depth Venue Results

Here is a graphic of all venues years containing submissions and their label distribution. 

![](../resources/label_fig.svg   "Graphic of all venues years containing submissions and their label distribution")

We will now present the results for each venue year and their subpages. 
The order of checked venues closely follows the order in the graphic.    
If we write a decision or decision note exists, we mean that our algorithm is able to label the submissions correctly with our assumptions about invitation and content field naming.
### ICLR 2013
- Comments not available through API, maybe due to age
- Decision is in content of submission

### ICLR 2014
- Comments not available through API, maybe due to age  
- Decision is in content of submission  
- Decision field can exist but have no decision; most submissions have reviews but no decision  

### ICLR 2016
- No submissions on the website but accessible with API  
- No decision note exists

### ICLR 2017
- Workshop: accepted submissions have no note but rejected submissions do
- Conference has decision note

### ICLR 2018
- Conference has decision note
- Workshop has decision note

### ICLR 2019
- Conference has decision note (called meta review)
- Workshop has decision note

### ICLR 2020
- Conference has decision note
- Workshop has no submissions/ comments yet

### NIPS 2016
- Not accessible from website but API works
- Reviews exist but no final decision

### NIPS 2017
- LITS workshop has decision but invitation is for generic comments; labeled unknown because false positive rate too high possibly
- autodiff workshop has decision note

### NIPS 2018
- Spatiotemporal: reviews but no decision
- MLITS has decision note
- IRASL has decision note
- CDNNRIA has decision note
- MLOSS: reviews but no decision

### NeurIPS 2019
- Reproducibility Challenge has no decisions
- Workshops have sometimes a decision note or no comments at all

### ICML 2013
- Comments not available through API, maybe due to age
- Decision is in content of submission

### ICML 2017
- WHI: reviews but no decision
- RML has decision note
- MLAV no comments

### ICML 2018
- NAMPI has decision note
- RML has decision note
- ECA has decision note

### ICML 2019
- DP has decision note
- RL4RL has decision note
- AMTL has no submissions

### AKBC 2013
- Decision is in content of submission

### AKBC 2019
- Has decision note

### ESWC 2918
- Has decision note

### IEEE 2018
- No reviews, no decisions

### ISMIR 2018
- All notes are generic comments
- No decisions

### ISWC 2017
- Decision is generic comment; not labeled

### ISWC 2018
- Decision is generic comment; not labeled

### MIC 2018
- No comments

### MIDL 2018
- Abstract has decision note
- Conference has decision note

### MIDL 2019
- Has decision note
- Has the following policy: Remove If Rejected: (optional) Remove submission if paper is rejected.

### MIDL 2020
- No decisions/ comments yet

### RSS 2017
- Submissions not accessible from website but API works
- Has reviews but no decisions

### RSS 2019
- Submissions not accessible from website but API works
- No comments

### VIVO 2019
- Has decision note
- No rejected papers could be found, might be removed

### ICAPS 2019
- SPARK: Has decision note; No rejected papers could be found, might be removed
- XAIP: Has decision note
- HP: Reviews but no decision; often no comments
- WIPC: reviews but no decision
- KIPC: reviews but no decision
- HSDIP: meta review like ICLR 2019

### RIIAA 2019
- No comments

### AABI 2019
- No comments

