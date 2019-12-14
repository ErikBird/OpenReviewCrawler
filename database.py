from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
# Global Variables
SQLITE                  = 'sqlite'

# Table Names
VENUE           = 'venue'
SUBMISSION       = 'submission'
REVISIONS = 'revisions'
NOTE = 'notes'
NOTE_REVISION = "note_revision"


class SQLDatabase:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }

    # Main DB Connection Ref Obj
    db_engine = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    def create_db_tables(self):
        metadata = MetaData()
        venue = Table(VENUE, metadata,
                      Column('id', Integer, primary_key=True),
                      Column('venue', String),
                      Column('year', String)
                      )

        submission = Table(SUBMISSION, metadata,
                        Column('id', String, primary_key=True),
                        Column('venue', None, ForeignKey('venue.id')),
                        Column('original', String),
                        Column('cdate', Integer),
                        Column('tcdate', Integer),
                        Column('tmdate', Integer),
                        Column('ddate', Integer),
                        Column('number', Integer),
                           Column('title', String),
                           Column('abstract', String),
                           Column('replyto', String),
                           Column('authorid1', String),
                           Column('authorid2', String),
                           Column('authorid3', String),
                           Column('authorid4', String),
                           Column('authorid5', String),
                           Column('author1', String),
                           Column('author2', String),
                           Column('author3', String),
                           Column('author4', String),
                           Column('author5', String),
                           Column('pdf', String),
                           Column('forum', String),
                           Column('referent', String),
                           Column('invitation', String),
                        Column('replyCount', Integer)
                        )

        revision = Table(REVISIONS, metadata,
                        Column('id', String, primary_key=True),
                        Column('submission', None, ForeignKey('submission.id')),
                        Column('original', String),
                        Column('cdate', Integer),
                        Column('tcdate', Integer),
                        Column('tmdate', Integer),
                        Column('ddate', Integer),
                        Column('number', Integer),
                        Column('title', String),
                        Column('abstract', String),
                        Column('replyto', String),
                        Column('authorid1', String),
                        Column('authorid2', String),
                        Column('authorid3', String),
                         Column('authorid4', String),
                         Column('authorid5', String),
                         Column('author1', String),
                         Column('author2', String),
                         Column('author3', String),
                         Column('author4', String),
                         Column('author5', String),
                        Column('pdf', String),
                         Column('forum', String),
                         Column('referent', String),
                         Column('invitation', String),
                         Column('replyto', String)
                           )

        note = Table(NOTE, metadata,
                         Column('id', String, primary_key=True),
                         Column('submission', None, ForeignKey('submission.id')),
                         Column('original', String),
                         Column('cdate', Integer),
                         Column('tcdate', Integer),
                         Column('tmdate', Integer),
                         Column('ddate', Integer),
                         Column('number', Integer),
                         Column('title', String),
                         Column('decision', String),
                         Column('forum', String),
                         Column('referent', String),
                         Column('invitation', String),
                         Column('replyto', String),
                         Column('replyCount', String)
                         )

        note_revision = Table(NOTE_REVISION, metadata,
                      Column('id', String, primary_key=True),
                              Column('submission', None, ForeignKey('note.id')),
                              Column('original', String),
                              Column('cdate', Integer),
                              Column('tcdate', Integer),
                              Column('tmdate', Integer),
                              Column('ddate', Integer),
                              Column('number', Integer),
                              Column('title', String),
                              Column('decision', String),
                              Column('forum', String),
                              Column('referent', String),
                              Column('invitation', String),
                              Column('replyto', String),
                              Column('replyCount', String)
                              )
        try:
            metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!")
            print(e)

    # Insert, Update, Delete
    def execute_query(self, query=''):
        if query == '': return
        print(query)
        with self.db_engine.connect() as connection:
            try:
                connection.execute(query)
            except Exception as e:
                print(e)

    def insert_dict(self,dict):
        venues = []
        submissions = []
        revisions=[]
        notes=[]
        note_revisions=[]
        for i, el in enumerate(dict):
            venues.append({'id': i,'venue': el["venue"], 'year': el["year"]})
            for s in el["submissions"]:
                submissions.append({'id': s["id"], 'venue': i,
                                    'original': s["original"], 'cdate': s["cdate"],
                                    'tcdate': s["tcdate"],
                                    'tmdate': s["tmdate"],
                                    'ddate': s["ddate"], 'number': s["number"],
                                    'title': s['content']["title"], 'abstract': s['content']["abstract"],
                                    'replyto': s['content']["replyto"], 'authorid1': s['content']["authorids"][0] if s['content']["authorids"][0] else "",
                                    'authorid2': s['content']["authorids"][1] if s['content']["authorids"][1] else "",
                                    'authorid3': s['content']["authorids"][2] if s['content']["authorids"][2] else "",
                                    'authorid4': s['content']["authorids"][3] if s['content']["authorids"][3] else "",
                                    'authorid5': s['content']["authorids"][4] if s['content']["authorids"][4] else "",
                                    'author1': s['content']["authors"][0] if s['content']["authors"][0] else "",
                                    'author2': s['content']["authors"][1] if s['content']["authors"][1] else "",
                                    'author3': s['content']["authors"][2] if s['content']["authors"][2] else "",
                                    'author4': s['content']["authors"][3] if s['content']["authors"][3] else "",
                                    'author5': s['content']["authors"][4] if s['content']["authors"][4] else "",
                                    'pdf': s['content']["pdf"], 'forum': s["forum"],
                                    'referent': s["referent"], 'invitation': s["invitation"]
                                    , 'replyCount': s['details']["replyCount"]})

                for r in s['revisions']:
                    revisions.append({'id': r["id"], 'submission': s["id"],
                                        'original': r["original"], 'cdate': r["cdate"],
                                        'tcdate': r["tcdate"],
                                        'tmdate': r["tmdate"],
                                        'ddate': r["ddate"], 'number': r["number"],
                                        'title': r['content']["title"], 'abstract': r['content']["abstract"],
                                        'replyto': r['content']["replyto"],
                                        'authorid1': r['content']["authorids"][0] if r['content']["authorids"][
                                            0] else "",
                                        'authorid2': r['content']["authorids"][1] if r['content']["authorids"][
                                            1] else "",
                                        'authorid3': r['content']["authorids"][2] if r['content']["authorids"][
                                            2] else "",
                                        'authorid4': r['content']["authorids"][3] if r['content']["authorids"][
                                            3] else "",
                                        'authorid5': r['content']["authorids"][4] if r['content']["authorids"][
                                            4] else "",
                                        'author1': r['content']["authors"][0] if r['content']["authors"][0] else "",
                                        'author2': r['content']["authors"][1] if r['content']["authors"][1] else "",
                                        'author3': r['content']["authors"][2] if r['content']["authors"][2] else "",
                                        'author4': r['content']["authors"][3] if r['content']["authors"][3] else "",
                                        'author5': r['content']["authors"][4] if r['content']["authors"][4] else "",
                                        'pdf': r['content']["pdf"], 'forum': r["forum"],
                                        'referent': r["referent"], 'invitation': r["invitation"]
                                           })

                for n in s['notes']:
                    notes.append({'id': n["id"], 'submission': s["id"],
                                        'original': n["original"], 'cdate': n["cdate"],
                                        'tcdate': n["tcdate"],
                                        'tmdate': n["tmdate"],
                                        'ddate': n["ddate"], 'number': n["number"],
                                        'title': n['content']["title"], 'decision': n['content']["decision"],
                                        'forum': n["forum"],
                                        'referent': n['referent'], 'invitation': n["invitation"],
                                        'replyto': n["replyto"], 'replyCount': n['details']["replyCount"]
                                           })

                    for nr in n['revisions']:
                        note_revisions.append({'id': nr["id"], 'submission': n["id"],
                                      'original': nr["original"], 'cdate': nr["cdate"],
                                      'tcdate': nr["tcdate"],
                                      'tmdate': nr["tmdate"],
                                      'ddate': nr["ddate"], 'number': nr["number"],
                                      'title': nr['content']["title"], 'decision': nr['content']["decision"],
                                      'forum': nr["forum"],
                                      'referent': nr['referent'], 'invitation': nr["invitation"],
                                      'replyto': nr["replyto"], 'replyCount': nr['details']["replyCount"]
                                      })

        '''
        conn.execute(table.insert(),[
   {'l_name':'Hi','f_name':'bob'},
   {'l_name':'yo','f_name':'alice'}])
        '''

    def print_all_data(self, table='', query=''):
        query = query if query != '' else "SELECT * FROM '{}';".format(table)
        print(query)
        with self.db_engine.connect() as connection:
            try:
                result = connection.execute(query)
            except Exception as e:
                print(e)
            else:
                for row in result:
                    print(row)  # print(row[0], row[1], row[2])
                result.close()
        print("\n")