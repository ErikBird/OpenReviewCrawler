from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database_model as model
import json
# Global Variables
SQLITE                  = 'sqlite'




class SQLDatabase:
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}'
    }
    # Main DB Connection Ref Obj
    db_engine = None
    Session = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            self.Session= sessionmaker(bind=self.db_engine)
            print(self.db_engine)
        else:
            print("DBType is not found in DB_ENGINE")

    def create_db_tables(self):
        try:
            model.Base.metadata.create_all(self.db_engine)
            print("Tables created")
        except Exception as e:
            print("Error occurred during Table creation!" )
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
        session = self.Session()
        for i, el in enumerate(dict):
            session.add(model.Venue(id=i,venue =el["venue"],year= el["year"]))
            session.commit()
            for s in el["submissions"]:
                sub_dict = {'id': s["id"], 'venue': i,
                                    'original': s["original"], 'cdate': s["cdate"],
                                    'tcdate': s["tcdate"],
                                    'tmdate': s["tmdate"],
                                    'ddate': s["ddate"], 'number': s["number"],
                                    'title': s['content']["title"], 'abstract': s['content']["abstract"],
                                    'replyto': s['content']["replyto"] if "replyto" in s['content'].keys()  else "",
                                    'pdf': s['content']["pdf"] if "pdf" in s['content'].keys()  else "",
                                    'forum': s["forum"],
                                    'referent': s["referent"], 'invitation': s["invitation"]
                                    , 'replyCount': s['details']["replyCount"]}
                for i,authorid in enumerate(s['content']["authorids"][:12]):
                    sub_dict.update({'authorid'+str(i) : s['content']["authorids"][i]})
                for i,authorid in enumerate(s['content']["authors"][:12]):
                    sub_dict.update({'author' + str(i): s['content']["authors"][i]})
                session.add(model.Submission(**sub_dict))
                session.commit()

                for r in s['revisions']:
                    rev_dict={'id': r["id"],
                                  'submission': s["id"],
                                    'original': r["original"], 'cdate': r["cdate"],
                                    'tcdate': r["tcdate"],
                                    'tmdate': r["tmdate"],
                                    'ddate': r["ddate"], 'number': r["number"],
                                    'title': r['content']["title"], 'abstract': r['content']["abstract"],
                                    'replyto': r['content']["replyto"] if "replyto" in r['content'].keys() else "",
                                    'pdf': r['content']["pdf"] if "pdf" in r['content'].keys() else "",
                                    'forum': r["forum"],
                                    'referent': r["referent"], 'invitation': r["invitation"]}
                    for i, authorid in enumerate(s['content']["authorids"][:12]):
                        rev_dict.update({'authorid' + str(i): s['content']["authorids"][i]})
                    for i, authorid in enumerate(s['content']["authors"][:12]):
                        rev_dict.update({'author' + str(i): s['content']["authors"][i]})
                    session.add(model.Revision(**rev_dict))
                session.commit()
                for n in s['notes']:
                    notes={'id': n["id"], 'submission': s["id"],
                                        'original': n["original"], 'cdate': n["cdate"],
                                        'tcdate': n["tcdate"],
                                        'tmdate': n["tmdate"],
                                        'ddate': n["ddate"], 'number': n["number"],
                                        'title': n['content']["title"] if "title" in n['content'].keys() else "",
                                        'decision': n['content']["decision"]if "decision" in n['content'].keys() else "", #@TODO MIT PARSER VERBINDEN
                                        'forum': n["forum"],
                                        'referent': n['referent'], 'invitation': n["invitation"],
                                        'replyto': n["replyto"], 'replyCount': n['details']["replyCount"]
                                           }
                    session.add(model.Note(**notes))
                    session.commit()
                    for nr in n['revisions']:
                        note_revisions={'id': nr["id"], 'submission': n["id"],
                                      'original': nr["original"], 'cdate': nr["cdate"],
                                      'tcdate': nr["tcdate"],
                                      'tmdate': nr["tmdate"],
                                      'ddate': nr["ddate"], 'number': nr["number"],
                                      'title': nr['content']["title"] if "title" in nr['content'].keys() else "",
                                      'decision': nr['content']["decision"] if "decision" in nr['content'].keys() else "",#@TODO MIT PARSER VERBINDEN
                                      'forum': nr["forum"],
                                      'referent': nr['referent'], 'invitation': nr["invitation"],
                                      'replyto': nr["replyto"], 'replyCount': nr['details']["replyCount"]
                                      }
                        session.add(model.NoteRevision(**note_revisions))
                    session.commit()

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