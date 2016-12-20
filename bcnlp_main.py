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
# This file contains BitCurator NLP Tools main code
#

import textacy
import os
import codecs
import textract
import subprocess
from bcnlp_extract import *
from bcnlp_db import *
try:
    from argparse import ArgumentParser
except ImportError:
    raise ImportError("This script requires ArgumentParser which is in Python 2.7 or Python 3.0")

def replace_suffix(filename,orig, new):
    orig_suffix = '.' + orig
    new_suffix = '.' + new
    if filename.endswith(orig):
        filename = filename[:-len(orig_suffix)] + new_suffix

    return filename


def bcnlpInsertToPosTable(table_name, ec, pos_type_list, con, meta):
    """ Looking at the words in pos_type_list (list of nouns, or prepositions
        or verbs in a document - table_name has document number in its string.
    """
    ip = 0
    for pos_word in pos_type_list:
        ip += 1
        # num of pos type 
        tf_pos = ec.bnGetCount(pos_word)
        record_list = {'Index':ip, 'name':str(pos_word), 'Term Frequency':tf_pos}
        bndbInsert2(table_name, record_list, ip, con, meta)

def bcnlpMakePosTable(table_name, pos_list, ec, con, meta):
    """ Create POS table and insert records from the list provided.
    """
    # First create the table if it doesn't exist.
    print("\n\n>> Creating Table {} for NOUN POS ".format(table_name))
    bndbCreatePosTable(table_name, pos_list, con, meta)
    print("TABLE {} created.  Now inserting records to POS table".format(table_name))

    # Now insert records
    bcnlpInsertToPosTable(table_name, ec, pos_list, con, meta)
    print ">>> Inserted records to table"

def bcnlpProcessFile(doc_index, infile, con, meta):
    """ Given the infile, do all necessary processing - identifying entities,
        parts of spech, etc., and add then to the appropriate tables in the DB.
    """
    ec = BcnlpExtractEntity(infile)

    #### Bag of words
    bow = ec.bnGetBagOfWords()
    ## print("list bag of words:[len={}] : {} ".format(len(list(bow)), list(bow)[:10]))

    '''
    bot, bot_count = ec.bnGetBagOfTerms(is_sorted=True)
    '''

    #### bag of terms
    bot = ec.bnGetBagOfTerms(is_sorted=False, ngrams=2)
    print "Bag Of Terms with ngrams 2: ", list(bot)[:10], len(list(bot))


    #### Named Entities Identification
    ne = ec.bnIdentifyNamedEntities(ne_include_types=None, ne_exclude_types=u'NUMERIC')

    ##### POS Regex matches #####
    noun_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['NP']
    prep_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['PP']
    verb_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['VP']

    pos_match_np=ec.bnGetPosRegexMatches(noun_pattern)
    pos_match_pp=ec.bnGetPosRegexMatches(prep_pattern)
    pos_match_vp=ec.bnGetPosRegexMatches(verb_pattern)
    num_pos_np = len(list(pos_match_np))
    num_pos_pp = len(list(pos_match_pp))
    num_pos_vp = len(list(pos_match_vp))

    n_grams = ec.bnGetNGrams(1)
    num_words = len(list(n_grams))
    ## print "Length of words list: ", len(list(n_grams))

    # Insert {doc_index, num_words, num_pos_np, num_pos_pp, num_pos_vp}
    # into the db.
    main_table_list = {'doc_index':doc_index, 'num_words':num_words, \
         'num_pos_np':num_pos_np, 'num_pos_pp':num_pos_pp, 'num_pos_vp':num_pos_vp}  
    bndbInsert('bcnlp_main', main_table_list, doc_index, con, meta)

    ##### Now create a new table of entities for this document and populate.
    table_name = 'bcnlp_entity_' + str(doc_index) 
    print "Creating bcnlp_entity_x table :", table_name
    bndbCreateNeTable(table_name, con, meta)
    
    #### Insert the Named Entities into the table
    ne = ec.bnIdentifyNamedEntities(ne_include_types=None, ne_exclude_types=u'NUMERIC')
    bow = ec.bnGetBagOfWords()

    # For each word in the doc, insert a record into the docx_table with
    # term frequency
    i = 0
    for w in list(bow):
        i += 1
        try:
            tfw = ec.bnGetCount(w)
            record_list = {'Index':i, 'name':w, 'Term Frequency':tfw}
            ## print("[LOG-2]:Inserting ne: {} into table {}".format(record_list, tfw))
            bndbInsert(table_name, record_list, i, con, meta)
            
        except:
            # The record might already exist.
            ## print "exception for ", w
            continue

    # for each word in each of pos_np, vp and pp, create records in their respective
    # tables. For each doc, there will be one such table. As an alternative,
    # we can have one table for all documents with doc_index as paret of the record.
    # That way we will have just 3 tables irrespective of num docs. FIXME: See if
    # it is a better idea.

    table_name = 'bcnlp_noun_doc'+str(doc_index)
    bcnlpMakePosTable(table_name, pos_match_np, ec, con, meta)
    
    table_name = 'bcnlp_prepo_doc'+str(doc_index)
    bcnlpMakePosTable(table_name, pos_match_pp, ec, con, meta)
    
    table_name = 'bcnlp_verb_doc'+str(doc_index)
    bcnlpMakePosTable(table_name, pos_match_vp, ec, con, meta)
    

    '''
    if not infile.endswith('.txt'):
        print("infile {} doesnt end with txt. So textracting".format(infile))

        filename, file_ext = os.path.splitext(infile)
        print("Filename: {}, ext: {}".format(filename, file_ext))

        new_infile = replace_suffix(infile,file_ext, 'txt')
        print "new_infile: ", new_infile
        textract_cmd = 'textract ' + infile + ' > ' + new_infile 
        subprocess.check_output(textract_cmd, shell=True, stderr=subprocess.STDOUT)

        f = codecs.open(infile, "r", "utf-8")
        input_file_contents = f.read()
    else:
        f = codecs.open(infile, "r", "utf-8")
        input_file_contents = f.read()
        print "CMD: ", textract_cmd
    '''

if __name__ == "__main__":
    import sys

    parser = ArgumentParser(prog='bcnlp', description='')
    parser.add_argument('--infile', action='store', help="... ")
    ## parser.add_argument('--input_dir', action='store', help="... ")
    ## parser.add_argument('--outdir', action='store', help="... ")

    args = parser.parse_args()

    con, meta = dbinit()
    if args.infile: 
        print "\n Infile: ", args.infile
        infile = os.getcwd() + '/' + args.infile
        if os.path.isdir(infile):
            print("{} is a directory".format(infile))
            # FIXME: Travere through the directory tree and read in every file.
            # For now assume there is only one level
            i = 0
            for f in infile:
                print("file number {}: {}".format(i, f))
                f_path = os.getcwd() + '/' + infile + '/' + f
                print "Processing file ", f_path
                bcnlpProcessFile(i, f, con, meta)
                i += 1
        else:
            bcnlpProcessFile(0, infile, con, meta)
         
    #num_docs = i+1
