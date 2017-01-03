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
import bcnlp_db

#def bnGetEntitiesForDoc(doc_index, con, meta):
def bnGetInfoForDoc(doc_index, category, con, meta):
    # First query the main table to see if this doc is there in the list 
    # and get its index.
    records = []
    outfile = ""
    for table in meta.tables:
        if table == "bcnlp_main":
            table_obj = meta.tables['bcnlp_main']
            for record in con.execute(table_obj.select()):
                if record[0] == doc_index:
                    # Get the entities from the entity table for this doc
                    # Command to be executed: select * from <entity_table>;
                    if category == 'Entity':
                        entity_table = "bcnlp_entity_doc"+str(doc_index)
                        records = bnPrintTable(entity_table, con, meta)
                        outfile = entity_table+".txt"
                    elif category == 'NP':
                        np_table = "bcnlp_noun_doc"+str(doc_index)
                        records = bnPrintTable(np_table, con, meta)
                        outfile = np_table+".txt"
                    elif category == 'VP':
                        vp_table = "bcnlp_verb_doc"+str(doc_index)
                        records = bnPrintTable(vp_table, con, meta)
                        outfile = vp_table+".txt"
                    elif category == 'PP':
                        pp_table = "bcnlp_verb_doc"+str(doc_index)
                        records = bnPrintTable(pp_table, con, meta)
                        outfile = pp_table+".txt"
    if outfile == "":
        return None

    with open(outfile, "w") as of:
        for item in records:
            of.write("%s\n" % item)
    return outfile
        

'''
def bnGetEntitiesForDoc(doc_index, con, meta):
    table_name = "bcnlp_entity_doc" + str(doc_index)
    for table in meta.tables:
        if table == table_name:
            table_obj = meta.tables[table_name]
            for record in con.execute(table_obj.select()):
'''
                   
def bnGetDocIndexForDoc(con, meta, doc_name):
    for table in meta.tables:
        if table == "bcnlp_main":
            print "found bcnlp_main table"
            table_obj = meta.tables['bcnlp_main']
            #doc_name = table['doc_name']
            select_phrase = table_obj.select().where(table_obj.c.doc_name == doc_name)
            for row in con.execute(select_phrase):
                print row
                return row[0]

def bnPrintMainTable(con, meta):
    row_list = []
    for table in meta.tables:
        if table == "bcnlp_main":
            table_obj = meta.tables['bcnlp_main']
            #doc_name = table['doc_name']
            ##for col in table_obj.c:  
                ##print col
            for row in con.execute(table_obj.select()):
                ## print row
                row_list.append(row)
            return row_list
def bnPrintTable(table_name, con, meta):
    #print "Printing table ", table_name
    row_list = []
    for table in meta.tables:
        if table == table_name:
            table_obj = meta.tables[table_name]
            for row in con.execute(table_obj.select()):
                ## print row
                row_list.append(row)
            return row_list
            


if __name__ == "__main__":
    parser = ArgumentParser(prog='bcnlp_query.py', description='Queru the DB')
    parser.add_argument('--i', action='store', help="... ")
    parser.add_argument('--outdir', action='store', help="... ")

    args = parser.parse_args()
    con, meta = bcnlp_db.dbinit()
    bnPrintMainTable(con, meta)
    doc_index = bnGetDocIndexForDoc(con, meta, "13030.Smalltalk.Hugh+Brinkman.txt")
    
