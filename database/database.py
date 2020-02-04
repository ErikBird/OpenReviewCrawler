import threading
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.inspection import inspect
from . import database_model as model
import progressbar
from sqlalchemy.orm import scoped_session
import queue
import logging
from sqlalchemy.dialects.postgresql import insert
# Global Variables
SQLITE                  = 'sqlite'
POSTGRES                = 'postgres'


def object_as_dict(obj, skip_keys=[]):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs
            if c.key not in skip_keys}


class SQLDatabase(threading.Thread):
    # http://docs.sqlalchemy.org/en/latest/core/engines.html
    DB_ENGINE = {
        SQLITE: 'sqlite:///{DB}',
        POSTGRES: '"postgres://SCHWAN:donotusethispassword@dasp.ukp.informatik.tu-darmstadt.de:22/dasp2"'
    }
    # Main DB Connection Ref Obj
    db_engine = None
    Session = None
    def __init__(self, dbtype, username='', password='', dbname=''):
        threading.Thread.__init__(self)
        dbtype = dbtype.lower()
        if dbtype in self.DB_ENGINE.keys():
            self.log = logging.getLogger("crawler")
            self.model = model
            engine_url = self.DB_ENGINE[dbtype].format(DB=dbname)
            self.db_engine = create_engine(engine_url)
            session_factory= sessionmaker(bind=self.db_engine)
            self.Session = scoped_session(session_factory)
            self.q = queue.Queue()
        else:
            print("DBType is not found in DB_ENGINE")

    def run(self):
        while True:
            session = self.Session()
            cmd,data= self.q.get()
            if cmd == "quit":
                break
            elif cmd == "add" or cmd == "merge":
                session.merge(data)
                session.commit()
                self.log.debug('Value inserted into db')
            else:
                print("Database Command not found: ",cmd)


    def close(self):
        self.q.put(("quit","quit"))
        self.log.info('Last Value has been added to the database queue')

    def command(self, cmd,data):
        # Kommando in Warteschlange einreihen
        self.q.put((cmd,data))

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

    def get_venues(self):
        session = self.Session()
        return [object_as_dict(venue) for venue in session.query(model.Venue).all()]

    def insert_submission(self, venue_id,submission_id,pdf=None):

        sub_dict = {'id': submission_id, 'venue': venue_id,
                    'pdf_binary': pdf }
        self.command("add",model.Submission(**sub_dict))

    def insert_revision(self, revision_id,submission_id,pdf=None):
        rev_dict = {'id': revision_id, 'submission': submission_id,
                    'pdf_binary': pdf }
        self.command("add",model.Revision(**rev_dict))

    def insert_dict(self,dict):
        '''
        This method stores a dictionary containing the crawled data into an SQL Database
        :param dict: The data dictionary
        :return: Stores values into the database
        '''

        for el in dict:
            self.command("merge", model.Venue(id=el["venue_id"],venue =el["venue"],year= el["year"]))
            for s in progressbar.progressbar(el["submissions"]):
                sub_dict = {'id': s["id"], 'venue': el["venue_id"],
                                    'original': s["original"], 'cdate': s["cdate"],
                                    'tcdate': s["tcdate"],
                                    'tmdate': s["tmdate"],
                                    'ddate': s["ddate"], 'number': s["number"],
                                    'title': s['content']["title"] if "title" in s['content'].keys()  else "",
                                    'abstract': s['content']["abstract"] if "abstract" in s['content'].keys()  else "",
                                    'replyto': s["replyto"] if "replyto" in s['content'].keys()  else "",
                                    'acceptance_tag': s['acceptance_tag'] if "acceptance_tag" in s.keys() else "",
                                    'pdf_ref': s['content']["pdf"] if "pdf" in s['content'].keys()  else "",
                                    'forum': s["forum"],
                                    'referent': s["referent"], 'invitation': s["invitation"]
                                    , 'replyCount': s['details']["replyCount"],
                                    'submission_content': str(s["content"])}
                for i,authorid in enumerate(s['content']["authorids"][:12]):
                    sub_dict.update({'authorid'+str(i) : s['content']["authorids"][i]})
                for i,authorid in enumerate(s['content']["authors"][:12]):
                    sub_dict.update({'author' + str(i): s['content']["authors"][i]})
                self.command("merge", model.Submission(**sub_dict))

                for r in s['revisions']:
                    rev_dict={'id': r["id"],
                                  'submission': s["id"],
                                    'original': r["original"], 'cdate': r["cdate"],
                                    'tcdate': r["tcdate"],
                                    'tmdate': r["tmdate"],
                                    'ddate': r["ddate"], 'number': r["number"],
                                    'title': r['content']["title"] if "title" in r['content'].keys() else "",
                                    'abstract': r['content']["abstract"]if "abstract" in r['content'].keys() else "",
                                    'replyto': r["replyto"] if "replyto" in r['content'].keys() else "",
                                    'pdf_ref': r['content']["pdf"] if "pdf" in r['content'].keys() else "",
                                    'forum': r["forum"],
                                    'referent': r["referent"], 'invitation': r["invitation"],
                                    'revision_content': str(r["content"])}
                    for i, authorid in enumerate(r['content']["authorids"][:12]):
                        rev_dict.update({'authorid' + str(i): r['content']["authorids"][i]})
                    for i, authorid in enumerate(r['content']["authors"][:12]):
                        rev_dict.update({'author' + str(i): r['content']["authors"][i]})
                    self.command("merge", model.Revision(**rev_dict))

                for n in s['notes']:
                    notes={'id': n["id"], 'submission': s["id"],
                                        'original': n["original"], 'cdate': n["cdate"],
                                        'tcdate': n["tcdate"],
                                        'tmdate': n["tmdate"],
                                        'ddate': n["ddate"], 'number': n["number"],
                                        'title': n['content']["title"] if "title" in n['content'].keys() else "",
                                        'decision': n['content']["decision"]if "decision" in n['content'].keys() else "",
                                        'forum': n["forum"],
                                        'referent': n['referent'], 'invitation': n["invitation"],
                                        'replyto': n["replyto"], 'replyCount': n['details']["replyCount"],
                                        'note_content': str(n["content"])
                                           }
                    self.command("merge", model.Note(**notes))

                    for nr in n['revisions']:
                        note_revisions={'id': nr["id"], 'submission': n["id"],
                                      'original': nr["original"], 'cdate': nr["cdate"],
                                      'tcdate': nr["tcdate"],
                                      'tmdate': nr["tmdate"],
                                      'ddate': nr["ddate"], 'number': nr["number"],
                                      'title': nr['content']["title"] if "title" in nr['content'].keys() else "",
                                      'decision': nr['content']["decision"] if "decision" in nr['content'].keys() else "",
                                      'forum': nr["forum"],
                                      'referent': nr['referent'], 'invitation': nr["invitation"],
                                      'replyto': nr["replyto"], 'replyCount': nr['details']["replyCount"],
                                      'note_content': str(n["content"])
                                      }
                        self.command("merge", model.NoteRevision(**note_revisions))


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
                    print(row)
                result.close()
        print("\n")
