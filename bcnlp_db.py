#!/usr/bin/python
# coding=UTF-8
#
# BitCurator NLP Tools
# Copyright (C) 2016 -2017 
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
# This file contains BitCurator NLP Tools database support.
#

import sqlalchemy
from sqlalchemy import *
import psycopg2
from sqlalchemy_utils import database_exists, create_database
import sys

#from sqlalchemy.ext.declarative import declarative_base
#metadata = MetaData()
#SQLALCHAMY_DATABASE_URI = "postgresql://sunitha:sunitha@localhost/bcnlp_db"
#bcnlp_db = SQLAlchemy()
#engine = create_engine("postgres://localhost/bcnlp_db")
#Base = declarative_base()
#bcnlp_db = create_engine("postgres://localhost/bcnlp_db")

db_index = dict()
db_list = []
dbinfo_array = ["db_name", "con", "meta"]
#global con, meta
def dbinit():
    global con, meta
    #engine = sqlalchemy.create_engine("postgres://postgres@/postgres")

    """
    db_connect connects to the database 'bcanlp_db' and returns
    a connection object and a metadata object
    We will use the user-name and passwd as bcnlp and bcnlp.
    Note: We created this db externally using the following procedure:
    -> Connect to postgres:
    sudo -i -u postgres  (Provide the sudo password of the user typing it)
    -> Create a db with a user and passwd:
    psql
        postgres=#
        postgres=# create db bcanlp_db;
        CREATE DATABASE
        postgres=# create user testuser with password 'testuser';
        CREATE ROLE
        postgres=# grant all privileges on database testdb to testuser;
        GRANT
        postgres=# \q
    -> Now log into the DB as the given user. -W prompts for a passwd.
       $ psql -h localhost -d bcanlp_db -U bcnlp -W
       Password  (bcnlp)
    """
    con, meta = db_connect('bcnlp', 'bcnlp', 'bcanlp_db')

    print("[LOG]: dbinit: Tables created")
    print "[LOG]:dbinit: con: ", con
    print "[LOG]:dbinit: meta: ", meta

    # Create the main table if not already created.
    bndbCreateMainTable(con, meta)

    # Create a list of dictionaries to return the con and meta values for
    # the given db
    bndbAddToDbList('bcanlp_db', con, meta)

    return con, meta

def bndbAddToDbList(db_name, con, meta):
    db_list.append({dbinfo_array[0]:db_name, dbinfo_array[1]:con, dbinfo_array[2]:meta})

def db_connect(user, password, db, host='localhost',port=5432):
    '''Returns a connection and a metadata object
       NOTE: check if the port number is ok. It was copied from a site
       with some examples.
    '''

    print ">> Conencting to the DB"
    # We connect with the help of the PostgreSQL URL
    url = 'postgresql://{}:{}@{}:{}/{}'
    url = url.format(user, password, host, port, db)

    # The return value of create_engine() is our connection object
    con = sqlalchemy.create_engine(url, client_encoding='utf8')

    # We then bind the connection to MetaData()
    meta = sqlalchemy.MetaData(bind=con, reflect=True)

    return con, meta

def bndbCreateMainTable(con, meta):
    """
        Creates the main table which has the global information about all
        the documents read, doc index for reference, and some numbers
        derived from Textacy APIs.
    """
    create_table = False
    if dbu_does_table_exist("bcnlp_main") == True:
        print("Table bcnlp_main already exists")
    else:
        bcnlp_main_table = Table('bcnlp_main', meta,
            Column('doc_index', Integer, primary_key=True),
            Column('doc_name', String),
            Column('num_words', Integer),
            Column('num_pos_np',Integer),
            Column('num_pos_vp',Integer),
            Column('num_pos_pp',Integer)
        )
        create_table = True

    if dbu_does_table_exist("bcnlp_words") == True:
        print("Table bcnlp_words already exists")
    else:
        bcnlp_words_table = Table('bcnlp_words', meta,
            Column('name_index', Integer, primary_key=True),
            Column('doc_index', Integer),
            Column('word', String),
            Column('pos', String)
        )
        create_table = True

    if create_table == True:
        meta.create_all(con)

def bndbCreateNeTable(table_name, con, meta):
    """ one table per document.
    """
    if dbu_does_table_exist(table_name) == True:
        print("Table {} already exists".format(table_name))
        return
    else:
        bcnlp_ne_table = Table(table_name, meta,
            Column('Index', Integer, primary_key=True),
            Column('name', String),
            Column('Term Frequency', Integer)
        )
        print ">>bndbCreateNEtAble: Creating table ", table_name
        meta.create_all(con)

def bndbCreatePosTable(table_name, pos, con, meta):
    """ One table per document: bcnlp_docx_<n/p/v>p
    """
    if dbu_does_table_exist(table_name) == True:
        print("Table {} already exists".format(table_name))
        return
    else:
        bcnlp_ne_table = Table(table_name, meta,
            Column('Index', Integer, primary_key=True),
            Column('name', String),
            Column('Term Frequency', Integer)
        )
        print ">>bndbCreateNEtAble: Creating table ", table_name
        meta.create_all(con)
    
def bndbCreateSimTable(table_name, con, meta):
    """ One table per document: bcnlp_docx_<n/p/v>p
    """
    if dbu_does_table_exist(table_name) == True:
        print("Table {} already exists".format(table_name))
        return
    else:
        bcnlp_ne_table = Table(table_name, meta,
            Column('Index', Integer, primary_key=True),
            Column('Name', String),
            Column('Semantic', Float),
            Column('Cosine', Float),
            Column('Euclidian', Float),
            Column('Manhattan', Float)
        )
        print ">>bndbCreateSimtAble: Creating table ", table_name
        meta.create_all(con)

def bndbInsert(table, record, doc_index, con, meta):
    ## print("[LOG-Verbose]Inserting record {} to table {}".format(record, table))
    try:
        con.execute(meta.tables[table].insert(), record)
    except:
        ## sys.stderr.write("exception for {}".format(record))
        ## print "[Info-LOG-Verbose]: Record already exists for this index? ", doc_index
        pass

def bndbInsert2(table, record, doc_index, con, meta):
    ## print("[Info-LOG-Verbose]Inserting record {} to table {}".format(record, table))
    clause = meta.tables[table].insert().values(record)
    try:
        con.execute(clause)
    except:
        ## sys.stderr.write("exception for {}".format(record))
        ## print "[Info-LOG-Verbose]: Record already exists for this index? ", doc_index
        pass


# DB Utility functions
def dbu_get_conn():
    """ DB utility function to get the connection handle for
        the database.
    """
    conn = psycopg2.connect("\
        dbname='bcanlp_db'\
        user='bcnlp'\
        host = '127.0.0.1' \
        password='bcnlp'\
    ");
    return conn

def dbu_does_table_exist(table_name):
    conn = dbu_get_conn()
    c = conn.cursor()
    exec_cmd = "SELECT * FROM " + table_name
    try:
        c.execute(exec_cmd)
        return(True)
    except:
        return(False)
   
    
def dbu_drop_table(table_name):
    """ DB utility function to drop the specified table from the DB
    """
    conn = dbu_get_conn()
    c = conn.cursor()
    psql_cmd = "drop table " + table_name + ";"
    try:
        c.execute(psql_cmd)
        debug('>> Dropped table %s', table_name)
        # print ">> Dropped table ", table_name
        conn.commit()
        message_string = "Dropped table "+ table_name

        '''
        # update the image_matrix
        print "D: dbu_drop_table: Updating the matrix for img_db_exists " 
        print "Calling bcawSetFlagInMatrix "
        bcawSetFlagInMatrix('img_db_exists', False)

        '''
        ## print "[D]:execute_cmd: returning message_str ", message_string
        return(0, message_string)
    except:
        # Table doesn't exist
        print('>> Table {} does not exist '.format(table_name))
        # print ">> Table {} does not exist ".format(table_name)
        message_string = "Table "+ table_name + " does not exist"
        return(-1, message_string)

def dbu_list_tables(meta):
    print "The following tables are present in the db "
    for table in meta.tables:
        print table

def dbu_execute_dbcmd(function, **kwargs):
    """ DB utility function to execute the command specified by 'function'
        for the given image.
    """
    conn = dbu_get_conn()
    c = conn.cursor()
    if function in "compare_two_tables":
        # Takes 2 args: table1 and table2 to be compared. The words
        # common in both the tables are put into a new table
        # "andtable_<table1>_<table2>
        for k,v in kwargs.iteritems():
            #print "k-%s = v-%s" % (k, v)
            if k == 'table1': table1 = v
            if k == 'table2': table2 = v

        logging.debug('dbu_execute_dbcmd: TABLE1: %s TABLE2: %s', table1, table2)
        #psql_cmd = "create table newtable as (select * from bcnlp_entity_doc0 where name in (select name from bcnlp_entity_doc1));"
        psql_cmd = 'create table andtable_' + table1 + '_'+table2+' '+ \
           ' as (select * from ' +table1 + ' where name in (select name from ' +\
           table2+'));'
        try:
            c.execute(psql_cmd)
            conn.commit()
        except IOError as err:
            print("Command {} failed".format(psql_cmd))
    elif function in "compare_tables":
        # FIXME: Incomplete code
        i = 0
        new_table_name = "andtable_"
        psql_cmd_part = ""
        for k,v in kwargs.iteritems():
            #print "k-%s = v-%s" % (k, v)
            i += 1
            con, meta = db_connect('bcnlp', 'bcnlp', 'bcanlp_db')
            doc_index = bnGetDocIndexForDoc(con, meta, v)
            #tablename = table+str(i)
            new_table_name += str(doc_index)
    elif (function in "get_num_records"):
        for k,v in kwargs.iteritems():
            #print "k-%s = v-%s" % (k, v)
            if k == 'table': table = v
        #psql_cmd = 'select count(*) '+ table
        psql_cmd = 'select * from '+ table
        try:
            c.execute(psql_cmd)
            rows = c.fetchall()
            num_recs = len(rows)
            conn.commit()
        except IOError as err:
            print("Command {} failed".format(psql_cmd))
            num_recs = -1
        return num_recs

#def execute_psql_cmd(table1, table2, newtable):

def db_execute_psql_cmd_to_get_common_entities_from_tables(table1, table2):
    conn = dbu_get_conn()
    c = conn.cursor()
    psql_cmd = 'create table andtable_' + table1 + '_'+table2+' '+ \
       ' as (select * from ' +table1 + ' where name in (select name from ' +\
       table2+'));'
    try:
        c.execute(psql_cmd)
        conn.commit()
    except IOError as err:
        print("Command {} failed".format(psql_cmd))

'''
def operate_on_2_tables(table1, table2, function):
    conn = dbu_get_conn()
    c = conn.cursor()

    if function == 'common_entity_table':
        psql_cmd = 'create table andtable_' + table1 + '_'+table2+' '+ \
           ' as (select * from ' +table1 + ' where name in (select name from ' +\
           table2+'));'
        print "PSQL CMD: ", psql_cmd
        try:
            c.execute(psql_cmd)
            conn.commit()
        except IOError as err:
            print("Command {} failed".format(psql_cmd))
    elif function == 'semantic_similarity':
        textacy.similarity.ord2vec(table1, table2)
'''



'''
#class bcnlpTable(bcnlp_db.Model):
class bcnlpTable(Base):
    __tablename__ = 'bcnlp_main'
    doc_index = bcnlp_db.Column(bcnlp_db.Integer, primary_key = True)
    num_words = bcnlp_db.Column(bcnlp_db.Integer)
    num_pos_np = bcnlp_db.Column(bcnlp_db.Integer) 
    num_pos_vp = bcnlp_db.Column(bcnlp_db.Integer) 
    num_pos_pp = bcnlp_db.Column(bcnlp_db.Integer) 

#class bcnlpWordsTable(bcnlp_db.Model):
class bcnlpWordsTable(Base):
    __tablename__ = 'bcnlp_words'
    name_index = bcnlp_db.Column(bcnlp_db.Integer, primary_key = True)
    doc_index = bcnlp_db.Column(bcnlp_db.Integer)
    word = bcnlp_db.Column(bcnlp_db.String(60))
    pos = bcnlp_db.Column(bcnlp_db.String(60))

    def __init(self, doc_index = None, word = None, pos = None):
        self.doc_index = doc_index
        self.word - word
        self.pos = pos

class bcnlpNamedEntitiesTable(Base):
    __tablename__ = 'bcnlp_main'
    name_index = bcnlp_db.Column(bcnlp_db.Integer, primary_key = True)
    doc_index = bcnlp_db.Column(bcnlp_db.Integer)
    word = bcnlp_db.Column(bcnlp_db.String(60))
    pos = bcnlp_db.Column(bcnlp_db.String(60))
    def __init(self, doc_index = None, word = None, pos = None):
        self.doc_index = doc_index
        self.word - word
        self.pos = pos
   
'''

