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
# This file contains BitCurator NLP Tools curses code.
#

import curses                                                                
from curses import panel                                                     
import bcnlp_db
import bcnlp_query
from bcnlp_extract import *
import logging

# Set up logging location
logging.basicConfig(filename='/tmp/bcnlp.log', level=logging.DEBUG)

class Menu(object):                                                          

    def __init__(self, items, stdscreen):                                    
        self.window = stdscreen.subwin(0,0)                                  
        self.window.keypad(1)                                                
        self.panel = panel.new_panel(self.window)                            
        self.panel.hide()                                                    
        panel.update_panels()                                                

        self.position = 0                                                    
        self.items = items                                                   
        self.items.append(('exit','exit'))                                   

    def navigate(self, n):                                                   
        self.position += n                                                   
        if self.position < 0:                                                
            self.position = 0                                                
        elif self.position >= len(self.items):                               
            self.position = len(self.items)-1                                

    def display(self):                                                       
        self.panel.top()                                                     
        self.panel.show()                                                    
        self.window.clear()                                                  

        while True:                                                          
            self.window.refresh()                                            
            curses.doupdate()                                                
            for index, item in enumerate(self.items):                        
                if index == self.position:                                   
                    mode = curses.A_REVERSE                                  
                else:                                                        
                    mode = curses.A_NORMAL                                   

                msg = '%d. %s' % (index, item[0])                            
                self.window.addstr(1+index, 1, msg, mode)                    

            key = self.window.getch()                                        

            if key in [curses.KEY_ENTER, ord('\n')]:                         
                if self.position == len(self.items)-1:                       
                    break                                                    
                else:                                                        
                    self.items[self.position][1]()                           

            elif key == curses.KEY_UP:                                       
                self.navigate(-1)                                            

            elif key == curses.KEY_DOWN:                                     
                self.navigate(1)                                             

        self.window.clear()                                                  
        self.panel.hide()                                                    
        panel.update_panels()                                                
        curses.doupdate()

def report_func():
    global con, meta

    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)

    table = bcnlp_query.bnPrintMainTable(con, meta)
    i = 0
    pad = curses.newpad(100, 100)
    y =5
    x=5
    for record in table:
        i += 1
        rec_string = 'Document# ' + str(record[0]) + ', ' + str(record[1]) + ' has '+ str(record[2]) + ' words, '+ \
                 str(record[3])+' nouns, '+ str(record[4])+' verbs '+str(record[5])+' prepositions '
        rec_string_1 = 'Document# ' + str(record[0])  + ', ' + str(record[1]) + ' has '+ str(record[2]) + ' words,'
        rec_string_2 =  str(record[3])+' nouns, '+ str(record[4])+' verbs '+str(record[5])+' prepositions '

        ####curses.putp('\n' + rec_string + '\n') 
        pad.addstr(y,x, rec_string_1 )
        y += 1
        x += 2
        pad.addstr(y,x, rec_string_2 )
        y += 1
        x = 5
        
    pad.refresh(0,0, 5,5, 20,75)

    num_documents = i
    ## curses.putp("LOG: Num docs: "+ str(num_documents))
    
def get_entity_list():
    get_doc_index_or_pos('Entity')

def get_np_list():
    get_doc_index_or_pos('NP')

def get_vp_list():
    get_doc_index_or_pos('VP')

def get_pp_list():
    get_doc_index_or_pos('PP')

def drop_table():
    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)

    pad = curses.newpad(100, 100)
    query_text = '>> Enter Table name to drop '
    pad.move(5, 5)
    pad.addstr(query_text)
    pad.refresh(0,0, 5,5, 20,75)

    string = stdscr.getstr()
    query_text = "Entered table "+ string
    pad.move(5, 5)
    pad.addstr(query_text)
    pad.refresh(0,0, 5,5, 20,75)

    if bcnlp_db.dbu_does_table_exist(string):
        bcnlp_db.dbu_drop_table(string)
    else:
        query_text = ">> Table "+ string + " doesnt exist"
        pad.move(5, 5)
        pad.addstr(query_text)
        pad.refresh(0,0, 5,5, 20,75)

def get_semantic_similarity():
    get_similarity("semantic")

def get_cosine_similarity():
    get_similarity("cosine")

def get_euclidian_similarity():
    get_similarity("euclidian")

def get_manhattan_similarity():
    get_similarity("manhattan")

def get_similarity(sim_type):
    pad = curses.newpad(100, 100)
    doc_index1, doc_index2 = get_doc_indices()
    logging.debug('get_similarity: type:%s doc_index 1:%s and 2:%s ', \
                                  sim_type, doc_index1, doc_index2)
    # Query from the table to get the right value
    table1_name = 'doc'+str(doc_index1)+'_sm_table'
    table2_name = 'doc'+str(doc_index2)+'_sm_table'

    # Now get the particular record
    sim_record = bcnlp_query.bnGetInfoForDoc(doc_index1, 'sim', con, meta)
    logging.debug('similarity record: %s ', sim_record)

    # Now extract the cosine similarity value for doc_index2 from this record.
    if sim_type == "semantic":
        array_position = 2
    elif sim_type == "cosine":
        array_position = 3
    elif sim_type == "euclidian":
        array_position = 4
    elif sim_type == "manhattan":
        array_position = 5

    i = 0
    for record_element in sim_record:
        if doc_index2 == i:
            print("{} similarity of documents {} and {} is : {}".format\
                     (sim_type, doc_index1, doc_index2, record_element[array_position]))
        i += 1

    pad.move(5, 5)
    pad.refresh(0,0, 5,5, 20,75)

def get_doc_tables():
    """ Sends prompt to input the indices of 2 tables, one after the other,
        and returns the tables correspinding to those indices
    """
    doc_index1 = get_doc_index_or_pos("Table1")
    doc_index2 = get_doc_index_or_pos("Table2")
    table1 = "bcnlp_entity_doc" + str(doc_index1)
    table2 = "bcnlp_entity_doc" + str(doc_index2)
    return table1, table2

def get_doc_indices():
    """ Sends prompt to input the indices of 2 tables, one after the other,
        and returns their indices
    """
    doc_index1 = get_doc_index_or_pos("Table1")
    doc_index2 = get_doc_index_or_pos("Table2")
    return doc_index1, doc_index2

def get_common_entities():
    """ As part of similarity feature, this compares two tables and lists
        the common entities into a new table and also saves it in an
        output file for user viewing.
    """
    doc_index1 = get_doc_index_or_pos("Table1")
    doc_index2 = get_doc_index_or_pos("Table2")
    table1 = "bcnlp_entity_doc" + str(doc_index1)
    table2 = "bcnlp_entity_doc" + str(doc_index2)

    pad = curses.newpad(100, 100)
    new_table = "andtable_"+table1+'_'+table2
    if bcnlp_db.dbu_does_table_exist(new_table):
        message_string = ">> Common Entities table \n " +new_table + " already exists"
    else:
        #bcnlp_db.execute_psql_cmd(table1, table2)
        bcnlp_db.db_execute_psql_cmd_to_get_common_entities_from_tables(table1, table2) 
        message_string = ">> Common Entities saved to table "+new_table
    pad.addstr(5,5, message_string )
    pad.refresh(0,0, 5,5, 20,75)

    # Save the list to a file
    outfile = "common_entity_list_"+str(doc_index1)+"_"+str(doc_index2)
    if os.path.exists(outfile):
        message_string = "File "+outfile+" already exists"
    else:
        logging.debug('get_common_entities: dumping table %s to records', new_table)
        records = bnPrintTable(new_table, con, meta)
        with open(outfile, "w") as of:
            for item in records:
                of.write("%s\n" % item)
        logging.debug('get_common_entities: Saved records to outfile: %s', outfile)
        message_string = "Common Entities saved to file "+outfile

    pad.addstr(5,5, message_string )
    pad.refresh(0,0, 5,5, 20,75)

def get_doc_index_or_pos(category):
    """ Based on the 'category', it just returns the document index for
        the given table or calls the query function to get the pos info
        if category is a parts-of-speech
    """
    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)

    pad = curses.newpad(100, 100)
    pad.refresh(0,0, 5,5, 20,75)
    pad.move(5,5)

    if category == "Table1" or category == "Table2":
        query_text = '>> Enter Document Index for ' + category + ": "
    else:
        query_text = '>> Enter Document Index: '

    # FIXME: mvaddstr doesn't seem to work. Try it again
    #pad.mvaddstr(5, 10, ord(query_text))
    pad.addstr(query_text)
    pad.refresh(0,0, 5,5, 20,75)
    curses.echo()
    pad.move(5, 5)
    c = stdscr.getch()
    doc_number =  c - 48
    ## print "Entered ", doc_number
    pad.refresh(0,0, 5,5, 20,75)

    if category == "Table1" or category == "Table2":
        return doc_number
    # IF doc index provided doesn't exist, return with message
    

    if category == 'Entity':
        outfile = bcnlp_query.bnGetInfoForDoc(doc_number, 'Entity', con, meta)
        message_string  = ">> Entities saved to file "+ str(outfile) 
    elif category == 'NP':
        outfile = bcnlp_query.bnGetInfoForDoc(doc_number, 'NP', con, meta)
        message_string  = ">> Noun Phrases saved to file "+ str(outfile) 
    elif category == 'VP':
        outfile = bcnlp_query.bnGetInfoForDoc(doc_number, 'VP', con, meta)
        message_string  = ">> Verb Phrases saved to file "+ str(outfile) 
    elif category == 'PP':
        outfile = bcnlp_query.bnGetInfoForDoc(doc_number, 'PP', con, meta)
        message_string  = ">> Prepositions saved to file "+ str(outfile) 
    
    if outfile == None:
        # Wrong doc index entered. return
        message_string = ">> Wrong document index entered"

    pad.addstr(5,5, message_string )
    #pad.addstr(y,x, message_string )

    #  Displays a section of the pad in the middle of the screen
    pad.refresh(0,0, 5,5, 20,75)

class MyApp(object):                                                         

    def __init__(self, stdscreen):                                           
        self.screen = stdscreen                                              
        curses.curs_set(0)                                                   
        stdscr = curses.initscr()
        global con, meta 
        con, meta = bcnlp_db.dbinit()

        submenu_entity_items = [                                                    
                ('Get Enitity List', get_entity_list),                                       
                ('Display Documents', report_func)
                ]                                                            
        
        submenu_np_items = [                                                    
                ('Get Noun Phrases', get_np_list),                                       
                ('Display Documents', report_func)
                ]                                                            
        
        submenu_pp_items = [                                                    
                ('Get Prepositions', get_pp_list),                                       
                ('Display_Documents', report_func)
                ]                                                            
        
        submenu_vp_items = [                                                    
                ('Get verb phrases', get_vp_list),                                       
                ('Display_Documents', report_func)
                ]                                                            

        submenu_wms_items = [
                ('Semantic Similarity', get_semantic_similarity),
                ('Cosine Similarity', get_cosine_similarity),
                ('Euclidian Similarity', get_euclidian_similarity),
                ('Manhattan Similarity', get_manhattan_similarity)
                ]

        submenu_wms = Menu(submenu_wms_items, self.screen)
        submenu_simi_items = [
                ('Common Entity List', get_common_entities),
                ('Similarity measures', submenu_wms.display),
                ('Display_Documents', report_func)
                ]


        submenu_util_items = [
                ('Drop Table', drop_table),
                ('Display_Documents', report_func)
                ]

        submenu_entity = Menu(submenu_entity_items, self.screen) 
        submenu_np = Menu(submenu_np_items, self.screen)
        submenu_pp = Menu(submenu_pp_items, self.screen)
        submenu_vp = Menu(submenu_vp_items, self.screen)
        submenu_simi = Menu(submenu_simi_items, self.screen)
        submenu_util = Menu(submenu_util_items, self.screen)

        main_menu_items = [                                                  
                ('Report', report_func),
                ('Entity', submenu_entity.display),   
                ('POS-Noun', submenu_np.display),
                ('POS-Prepo', submenu_pp.display),
                ('POS-Verb', submenu_vp.display),
                ('Similarity', submenu_simi.display),
                ('Util', submenu_util.display)
                ]                                                            
        main_menu = Menu(main_menu_items, self.screen)                       
        main_menu.display()                                                  

if __name__ == '__main__':                                                       
    curses.wrapper(MyApp)   
