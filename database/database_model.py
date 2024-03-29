from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, BigInteger, String, MetaData, ForeignKey, LargeBinary

# Table Names
VENUE           = 'venue'
SUBMISSION       = 'submission'
REVISIONS = 'revisions'
NOTE = 'notes'
NOTE_REVISION = "note_revision"
#msc
Base = declarative_base()


class Venue(Base):
    __tablename__ = VENUE
    id = Column(Integer, primary_key=True)
    venue = Column(String)
    year = Column(String)


class Submission(Base):
    __tablename__ = SUBMISSION
    id = Column(String, primary_key=True)
    venue = Column(None, ForeignKey(Venue.id))
    original = Column(String)
    cdate = Column(BigInteger)
    tcdate = Column(BigInteger)
    tmdate = Column(BigInteger)
    ddate = Column(BigInteger)
    number = Column(Integer)
    title = Column(String)
    abstract = Column(String)
    acceptance_tag = Column(String)
    replyto = Column(String)
    authorid0 = Column(String)
    authorid1 = Column(String)
    authorid2 = Column(String)
    authorid3 = Column(String)
    authorid4 = Column(String)
    authorid5 = Column(String)
    authorid6 = Column(String)
    authorid7 = Column(String)
    authorid8 = Column(String)
    authorid9 = Column(String)
    authorid10 = Column(String)
    authorid11 = Column(String)
    authorid12 = Column(String)
    author0 = Column(String)
    author1 = Column(String)
    author2 = Column(String)
    author3 = Column(String)
    author4 = Column(String)
    author5 = Column(String)
    author6 = Column(String)
    author7 = Column(String)
    author8 = Column(String)
    author9 = Column(String)
    author10 = Column(String)
    author11 = Column(String)
    author12 = Column(String)
    pdf_ref = Column(String)
    pdf_binary = Column(LargeBinary, nullable=True)
    forum = Column(String)
    referent = Column(String)
    invitation = Column(String)
    replyCount = Column(Integer)
    submission_content = Column(String)


class Revision(Base):
    __tablename__ = REVISIONS
    id = Column(String, primary_key=True)
    submission = Column(None, ForeignKey(Submission.id))
    original = Column(String)
    cdate = Column(BigInteger)
    tcdate = Column(BigInteger)
    tmdate = Column(BigInteger)
    ddate = Column(BigInteger)
    number = Column(Integer)
    title = Column(String)
    abstract = Column(String)
    replyto = Column(String)
    authorid0 = Column(String)
    authorid1 = Column(String)
    authorid2 = Column(String)
    authorid3 = Column(String)
    authorid4 = Column(String)
    authorid5 = Column(String)
    authorid6 = Column(String)
    authorid7 = Column(String)
    authorid8 = Column(String)
    authorid9 = Column(String)
    authorid10 = Column(String)
    authorid11 = Column(String)
    authorid12 = Column(String)
    author0 = Column(String)
    author1 = Column(String)
    author2 = Column(String)
    author3 = Column(String)
    author4 = Column(String)
    author5 = Column(String)
    author6 = Column(String)
    author7 = Column(String)
    author8 = Column(String)
    author9 = Column(String)
    author10 = Column(String)
    author11 = Column(String)
    author12 = Column(String)
    pdf_ref = Column(String)
    pdf_binary = Column(LargeBinary, nullable=True)
    forum = Column(String)
    referent = Column(String)
    invitation = Column(String)
    replyCount = Column(Integer)
    revision_content = Column(String)


class Note(Base):
    __tablename__ = NOTE
    id = Column(String, primary_key=True)
    submission = Column(None, ForeignKey(Submission.id))
    original = Column(String)
    cdate = Column(BigInteger)
    tcdate = Column(BigInteger)
    tmdate = Column(BigInteger)
    ddate = Column(BigInteger)
    number = Column(Integer)
    title = Column(String)
    decision = Column(String)
    forum = Column(String)
    referent = Column(String)
    invitation = Column(String)
    replyto = Column(String)
    replyCount = Column(Integer)
    note_content = Column(String)


class NoteRevision(Base):
    __tablename__ = NOTE_REVISION
    id = Column(String, primary_key=True)
    submission = Column(None, ForeignKey(Note.id))
    original = Column(String)
    cdate = Column(BigInteger)
    tcdate = Column(BigInteger)
    tmdate = Column(BigInteger)
    ddate = Column(BigInteger)
    number = Column(Integer)
    title = Column(String)
    decision = Column(String)
    forum = Column(String)
    referent = Column(String)
    invitation = Column(String)
    replyto = Column(String)
    replyCount = Column(Integer)
    note_content = Column(String)
