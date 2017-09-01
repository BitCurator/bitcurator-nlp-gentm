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
import numpy as np
global num_docs
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

ec = dict()
def bcnlpProcessFile(doc_index, infile, con, meta):
    """ Given the infile, do all necessary processing - identifying entities,
        parts of spech, etc., and add then to the appropriate tables in the DB.
    """
    #ec = BcnlpExtractEntity(infile)
    ec[doc_index] = BcnlpExtractEntity(infile)
    print "Calling bnSaveFieInfo with index: ", doc_index
    ec[doc_index].bnSaveFileInfo(infile, doc_index)

    #### Bag of words
    bow = ec[doc_index].bnGetBagOfWords()
    ## print("list bag of words:[len={}] : {} ".format(len(list(bow)), list(bow)[:10]))

    '''
    bot, bot_count = ec.bnGetBagOfTerms(is_sorted=True)
    '''

    #### bag of terms
    bot = ec[doc_index].bnGetBagOfTerms(is_sorted=False, ngrams=2)
    print "Bag Of Terms with ngrams 2: ", list(bot)[:10], len(list(bot))


    #### Named Entities Identification
    ne = ec[doc_index].bnIdentifyNamedEntities(ne_include_types=None, ne_exclude_types=u'NUMERIC')

    ##### POS Regex matches #####
    noun_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['NP']
    prep_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['PP']
    verb_pattern = textacy.constants.POS_REGEX_PATTERNS['en']['VP']

    pos_match_np=ec[doc_index].bnGetPosRegexMatches(noun_pattern)
    pos_match_pp=ec[doc_index].bnGetPosRegexMatches(prep_pattern)
    pos_match_vp=ec[doc_index].bnGetPosRegexMatches(verb_pattern)
    num_pos_np = len(list(pos_match_np))
    num_pos_pp = len(list(pos_match_pp))
    num_pos_vp = len(list(pos_match_vp))

    n_grams = ec[doc_index].bnGetNGrams(1)
    num_words = len(list(n_grams))
    ## print "Length of words list: ", len(list(n_grams))

    doc_name =os.path.basename(infile)
    # Insert {doc_index, num_words, num_pos_np, num_pos_pp, num_pos_vp}
    # into the db.
    main_table_list = {'doc_index':doc_index, 'doc_name':doc_name, \
         'num_words':num_words, \
         'num_pos_np':num_pos_np, 'num_pos_pp':num_pos_pp, 'num_pos_vp':num_pos_vp}  
    bndbInsert('bcnlp_main', main_table_list, doc_index, con, meta)

    ##### Now create a new table of entities for this document and populate.
    table_name = 'bcnlp_entity_doc' + str(doc_index) 
    print "Creating bcnlp_entity_x table :", table_name
    bndbCreateNeTable(table_name, con, meta)
    
    #### Insert the Named Entities into the table
    ne = ec[doc_index].bnIdentifyNamedEntities(ne_include_types=None, ne_exclude_types=u'NUMERIC')
    bow = ec[doc_index].bnGetBagOfWords()

    # For each word in the doc, insert a record into the docx_table with
    # term frequency
    i = 0
    for w in list(bow):
        i += 1
        try:
            tfw = ec[doc_index].bnGetCount(w)
            ##if (doc_index == 1):
                ## print("NAME: {}, TFW: {}".format(w, tfw))

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
    bcnlpMakePosTable(table_name, pos_match_np, ec[doc_index], con, meta)
    
    table_name = 'bcnlp_prepo_doc'+str(doc_index)
    bcnlpMakePosTable(table_name, pos_match_pp, ec[doc_index], con, meta)
    
    table_name = 'bcnlp_verb_doc'+str(doc_index)
    bcnlpMakePosTable(table_name, pos_match_vp, ec[doc_index], con, meta)
    

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
    i = 0
    if args.infile: 
        print "\n Infile: ", args.infile
        infile = os.getcwd() + '/' + args.infile
        if os.path.isdir(infile):
            print("{} is a directory".format(infile))
            # FIXME: Traverse through the directory tree and read in every file.
            # For now assume there is only one level
            for f in os.listdir(infile):
                print("file number {}: {}".format(i, f))
                #f_path = os.getcwd() + '/' + infile + '/' + f
                f_path = infile + '/' + f
                print "Processing file ", f_path
                bcnlpProcessFile(i, f_path, con, meta)
                i += 1
        else:
            bcnlpProcessFile(0, infile, con, meta)
         
    num_docs = i
    print "NUM DOCS: ", num_docs

    # Now for each doc, create a similarity matrix table in the following structure:
    # if num_docs = 3, for example:
    # doc0_sm_table:
    #                      doc1    doc2   doc3
    # semantic similarity   x1      x2      x3
    # Cosine similarity     y1      y2      y3
    # Euclidian similarity  z1      z2      z3

    # doc0          semantic_similarity  cosine_sim euclidian_sim
    # doc1              x_s1                x_c1         x_e1
    # doc2              x_s2                x_c2         x_e2
    # doc3              x_s3                x_c3         x_e3

    # First create a similarity table for each doc
    # Also we will maintain a matrix and mark with a 1 if the martix is calculated
    # for two documents. We will also mark the other position of the matrix
    # for the two documents, so we won't calculate the similarity number
    # for the same two documents twice. (doc0 and doc1, doc1 and doc0)

    simmatrix_str = ""
    for i in range (0, num_docs):
        simmatrix_str += "0"
        table_name = 'doc'+str(i)+'_sm_table'
        bndbCreateSimTable(table_name, con, meta)

    sim_matrix = np.array(list(simmatrix_str * num_docs)).reshape(num_docs, num_docs)
    print sim_matrix

    # Now populate each table
    for i in range (0, num_docs):
        # First get the spacy-doc and name of the document we are building the
        # similarity table for
        mydoc_name = bnGetDocNameFromIndex(i)
        print "LOG: Getting spacy_doc for doc {}: {} ".format(i,mydoc_name)
        mydoc_name, myspacy_doc = bnGetSpacyDocFromIndex(i)
        print("mydoc_name: {}".format(mydoc_name))

        # Now traverse through the documents and build a record for similarity
        # measures for 'mydoc' with each of the other documents present.
        for j in range (0, num_docs):
            table_name = 'doc'+str(i)+'_sm_table'
            # get the spacy doc for doc#i j
            if (i != j) and sim_matrix[i,j] == "0":
                print "Calculating similarity for i,j ", i, j
                doc_path, spacy_doc = bnGetSpacyDocFromIndex(j)
                doc_name = os.path.basename(doc_path)
                sem_sim = bnExtractDocSimilarity(myspacy_doc, spacy_doc, 'word2vec')
                cos_sim = bnExtractDocSimilarity(myspacy_doc, spacy_doc, 'cosine')
                euc_sim = bnExtractDocSimilarity(myspacy_doc, spacy_doc, 'Eiclidian')
                manh_sim = bnExtractDocSimilarity(myspacy_doc, spacy_doc, 'Manhattan')
                sim_table_list = {'Index':j, 'Name':doc_name, \
                     'Semantic':sem_sim,  'Cosine':cos_sim, \
                     'Euclidian':euc_sim, 'Manhattan':manh_sim}

                table_name_2 = 'doc'+str(j)+'_sm_table'
                sim_table_list_2 = {'Index':i, 'Name':doc_name, \
                     'Semantic':sem_sim,  'Cosine':cos_sim, \
                     'Euclidian':euc_sim, 'Manhattan':manh_sim}
                print("[LOG]Inserting to table {} record {}", table_name, sim_table_list)
                # Now insert the record into the table for doc-i
                bndbInsert(table_name, sim_table_list, i, con, meta)
                bndbInsert(table_name_2, sim_table_list_2, j, con, meta)
                sim_matrix[i,j] = "1"

                # Since the flag for i,j is the same as j,i, we will set both. This
                # will avoid building the similarity for the same tables once again.
                sim_matrix[j,i] = "1"

                print sim_matrix
