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

##global con, meta
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
    get_doc_index('Entity')

def get_np_list():
    get_doc_index('NP')

def get_vp_list():
    get_doc_index('VP')

def get_pp_list():
    get_doc_index('PP')

def get_doc_index(category):
    stdscr = curses.initscr()
    curses.cbreak()
    curses.noecho()
    stdscr.keypad(1)

    pad = curses.newpad(100, 100)
    y =6
    x=5
    query_text = '>> Enter Document Index> '

    # FIXME: mvaddstr doesn't seem to work. Try it again
    #pad.mvaddstr(5, 10, ord(query_text))
    pad.move(5, 5)
    pad.addstr(query_text)
    pad.refresh(0,0, 5,5, 20,75)
    c = stdscr.getch()
    doc_number =  c - 48
    ## print "Entered ", doc_number
    pad.refresh(0,0, 5,5, 20,75)

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

def display_doc_table():
    print "Disppay doc table"

def noop():
    pass

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
        
        submenu_entity = Menu(submenu_entity_items, self.screen) 
        submenu_np = Menu(submenu_np_items, self.screen)
        submenu_pp = Menu(submenu_pp_items, self.screen)
        submenu_vp = Menu(submenu_vp_items, self.screen)

        main_menu_items = [                                                  
                ('Report', report_func),
                ('Entity', submenu_entity.display),   
                ('POS-Noun', submenu_np.display),
                ('POS-Prepo', submenu_pp.display),
                ('POS-Verb', submenu_vp.display)
                ]                                                            
        main_menu = Menu(main_menu_items, self.screen)                       
        main_menu.display()                                                  

if __name__ == '__main__':                                                       
    curses.wrapper(MyApp)   
