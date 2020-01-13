# About the OpenReview API and its modelling approach

OpenReview's modelling approach allows it to be flexible in regards to the different requirements of the many venues.

Its most important building blocks (for this project) are **invitations**, **notes** and **content**.
We will present them now.

## Notes
Notes are the "container" for submissions, comments and reviews. 
There are specified [here](https://openreview-py.readthedocs.io/en/latest/api.html#openreview.Note) by OpenReview.
We will briefly go over each field and then look at the important ones (invitation and content) more in-depth afterwards.
* invitation: the "type" of note. More about this later
* content: a dictionary which holds the visible content of the note. More later
* id: unique id for the note
* forum: unique id for the forum of the note. A forum is usually a paper, so all comments, reviews and the submission note itself for a paper have the same forum id
* replyto: the note id to which this note replies. Top-level comments and reviews have the forum id as value
* details: dictionary for additional meta data. Usually not important
* cdate, tcdate, tmdate, ddate: creation, true creation, modification and deletion date as Unix timestamp
* readers, nonreaders, writers, signature: not important. Used for rights management
* original, number, referent, tauthor: unimportant
 
 Examples for notes can be found in the [example_output.json](example_output.json).
 
## Invitation
Invitations are similar to API endpoints within the OpenReview model. 
Venues create their own invitations to organize and users then "post" notes to these invitations.
The notes then can be retrieved by querying for the invitation.

(There exist invitations without notes, but we will ignore them, as their are not important for us.)

The invitation decides if a note is a submission, comment, review, acceptance decision or something different.
Administrative tasks like the ability to withdraw an submission is handled with an invitation, as well. 
A withdrawn papern is then found at this invitation.

Since invitations are created by the venues, they can have different sets of invitations for e.g. different workshops at the venue.  
The invitations can also change between the years for the same venue.

How exactly the invitation is called is also decided by the venue. 
This is why general parsing of information can be hard, as the same type of note can have different invitation names.  
For example, the note which hold the acceptance decision is sometimes called "Decision" and sometimes "Acceptance". 
Other venues can  use entirely different names for the same note purpose. 

Some example invitations:
* ICLR.cc/2019/Conference/-/Blind_Submission: Papers submissions are found in this invitation for the ICLR 2019 conference
* ICLR.cc/2019/Conference/-/Paper2/Public_Comment: Public comments (which are generally questions by non-reviewers) for paper 2 (papers are numbered internally) at the ICLR 2019 connference are found here
* auai.org/UAI/2019/Conference/-/Paper5/Decision: The acceptance decision for paper 5 for the UAI 2019 conference is found here


## Content
The content field holds most of the displayed textual data.
It is a dictionary where the keys (and format of the values) are decided by the venue for each invitation.

Let us look at the content of some common note types. Different venues might have different names for the keys or have additional or fewer keys but the general look is similar.
The format is "key": "value"

**Submission:**

"title": "The paper title",  
"abstract": "The abstract of the paper"  
"tl;dr": "An even shorter summary. Some venues use this."
"authorids": \["jon.doe@example.de", "jane.doe@example.de"]  
"authors": \["Jon Doe", "Jane Doe"]  
"keywords": \["example", "not real"]

Author information is missing for anonymous submissions.

**Acceptance Decision:**

"decision": "reject"

**Review:**

"title": "A title for the review"  
"review": "The review text"  
"rating": "4: Top 50% of accepted papers, clear accept"  
"confidence": "2: The reviewer is fairly confident that the evaluation is correct"


**Comment:**

"title": "A title for the comment"   
"comment": "The comment itself"

