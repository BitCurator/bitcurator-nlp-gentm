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
# This file contains BitCurator NLP Tools File Extraction/Identification code
#

import textacy
import os
import codecs
import textract
import subprocess
from bcnlp_query import *

class ExtractFileContents:
    """ Using Textacy APIs, this defines methods to extract contents of a file.
    """
    def extractContents(self, infile):
        if not infile.endswith('.txt'):
            print("infile {} doesnt end with txt. So textracting".format(infile))
    
            filename, file_ext = os.path.splitext(infile)
            print("Filename: {}, ext: {}".format(filename, file_ext))
            
            new_infile = replace_suffix(infile,file_ext, 'txt')
            print "new_infile: ", new_infile
            textract_cmd = 'textract ' + infile + ' > ' + new_infile 
            ## print "CMD: ", textract_cmd
    
            # Fixme: subprocess is not needed. The above line where textract.process
            # works fine, but it gives UicodeDecode error. But doing sdubprocess also
            # gives the same error when f.read() is done. Need to fix this.
            # UnicodeDecodeError: 'utf8' codec can't decode byte 0xc7 in position 10: invalid continuation byte
            subprocess.check_output(textract_cmd, shell=True, stderr=subprocess.STDOUT)
    
            '''
            f = codecs.open(infile, "r", "utf-8")
            input_file_contents = f.read()
            '''
            input_file_contents = textacy.fileio.read.read_file(infile, mode=u'rt', encoding=None)
            
        else:
            '''
            f = codecs.open(infile, "r", "utf-8")
            input_file_contents = f.read()
            '''
            print "Extracting Contents of file", infile
            input_file_contents = textacy.fileio.read.read_file(infile, mode=u'rt', encoding=None)
            
        return input_file_contents
    
# fileDictList is a list of dictionaries, each dict consisting of document name 
# (filename) and its corresponding spacy_doc.
fileDictList = []
file_array = ['filename', 'spacy_doc']

class BcnlpExtractEntity:
    """ Using Textacy APIs, this defines methods for extracting useful information
        from the given files.
    """
    
    def __init__(self, infile):
        efc = ExtractFileContents()
        print ("INIT: Extract contents for infile: ", infile)

        input_file_contents = efc.extractContents(infile)
        metadata = {'filename': infile}
        self.doc = textacy.Doc(input_file_contents, metadata=metadata)

    def bnSaveFileInfo(self, filename, file_index):
        print("Adding filename:{} and file_index: {}".format(filename, file_index))
        #fileDictList[file_index].append({file_array[0]:filename, file_array[1]:self.doc})
        fileDictList.append({file_array[0]:filename, file_array[1]:self.doc})

    def bnGetBagOfWords(self):
        # FIXME: Keeping Lemmatize=True doesn't work. Fix it
        bow = self.doc.to_bag_of_words(lemmatize=False, as_strings=True)
        return bow

    def bnGetBagOfTerms(self, is_sorted, ngrams):
        bot = self.doc.to_bag_of_terms(ngrams=ngrams, named_entities=True, lemmatize=False, as_strings=True)
        #term_count = self.doc.count()
        #print("BOT: term count:{}  \n\n".format(term_count))
        
        if is_sorted == True:
            bot_sorted = sorted(bot.items(), key=lambda x: x[1], reverse=True)
            return bot_sorted
        else:
            return bot

    def bnGetCount(self, term):
        ####print("Getting count for term:{}, doc:{} ".format(term, self.doc))
        return self.doc.count(term)

    def bnGetNGrams(self, n):
        ng = textacy.extract.ngrams(self.doc, n, filter_stops=True, filter_punct=True, filter_nums=False, include_pos=None, exclude_pos=None, min_freq=1)
        return ng
        
    def bnIdentifyNamedEntities(self, ne_include_types, ne_exclude_types):
        if ne_exclude_types == None:
            #ne = textacy.extract.named_entities(self.doc, include_types=ne_include_types, drop_determiners=True, min_freq=1) 
            #ne = textacy.extract.named_entities(self.doc, exclude_types=u'NUMERIC', drop_determiners=True, min_freq=1) 
            ne = textacy.extract.named_entities(self.doc, include_types=u'PERSON', drop_determiners=True, min_freq=1) 
        else:
            ne = textacy.extract.named_entities(self.doc, include_types=ne_include_types, exclude_types=ne_exclude_types, drop_determiners=True, min_freq=1) 

        len_ne = len(list(ne))
        return ne

    def bnTextRank(self):
        text_rank = list(textacy.keyterms.textrank(self.doc, n_keyterms=10))
        return text_rank

    def bnGetPosRegexMatches(self, pattern):
        matches = textacy.extract.pos_regex_matches(self.doc ,pattern)
        return list(matches)
       
    def bnGetCountOfWord(self, word):
        freq_of_word = self.doc.count(word)
        print("Freq of the word {} is {}".format(word, freq_of_word))



def bnExtractDocSimilarity(doc1, doc2, similarity):
    """Measure the semantic similarity between two documents using
       Word Movers Distance. Uses Textacy API
       textacy.similarity.word_movers(doc1, doc2, metric=u'cosine')
    """

    #if similarity == 'Word Movers':
    if similarity == 'cosine':
        # Metric can be cosine, euclidian, I1, I2, or manhattan
        s = textacy.similarity.word_movers(doc1, doc2,metric=u'cosine')
        print(" Cosine Similarity between docs {} and {} is: {}".format( \
                  bnGetDocName(doc1), bnGetDocName(doc2), s))
    elif similarity == 'Euclidian':
        s = textacy.similarity.word_movers(doc1, doc2,metric=u'euclidian')
        print(" Euclidian Similarity between docs {} and {} is: {}".format( \
                  bnGetDocName(doc1), bnGetDocName(doc2), s))
    elif similarity == 'Manhattan':
        s = textacy.similarity.word_movers(doc1, doc2,metric=u'manhattan')
        print(" Manhattan Similarity between docs {} and {} is: {}".format( \
                  bnGetDocName(doc1), bnGetDocName(doc2), s))
    elif similarity == 'word2vec':
        s = textacy.similarity.word2vec(doc1, doc2)
        print(" Semantic Similarity between docs {} and {} is: {}".format( \
                  bnGetDocName(doc1), bnGetDocName(doc2), s))
    else:
        # Unsupported similarity method
        s = 0

    return round(s, 5)

def bnGetDocName(doc):
    i = 0
    doc_name = ""
    Found = False
    while not Found:
        spacy_doc = fileDictList[i]['spacy_doc']
        if doc == spacy_doc:
            doc_name = fileDictList[i]['filename']
            Found = True
        else:
            i += 1
    return doc_name

def bnGetDocNameFromIndex(doc_index):
    i = 0
    doc_name = ""
    Found = False
    while not Found:
        doc_name = fileDictList[i]['filename']
        if i==doc_index:
            return doc_name
        i += 1

def bnGetNumDocs():
    i = 0
    #print fileDictList
    '''
    doc_name = fileDictList[i]['filename']
    while doc_name!= None:
        doc_name = fileDictList[i]['filename']
        i+=1
    return i
    '''

def bnGetSpacyDocFromIndex(doc_index):
    """ Given the document index, it returns the corresponding "spacy" document
        object. This is needed for calling many Textacy APIs.
    """
    global con, meta
    Found = False
    i = 0

    spacy_doc = None
    filename = ""
    num_docs = bcnlp_db.dbu_execute_dbcmd("get_num_records", table="bcnlp_main")
    logging.debug('bnGetSpacyDocFromIndex: num_docs: %s', str(num_docs))
    while not Found:
        if doc_index == i:
            logging.debug('Found spacy_doc for doc: %s ', str(doc_index))
            spacy_doc = fileDictList[i]['spacy_doc']
            filename = fileDictList[i]['filename']
            Found = True
        else:
            i+=1
            if i > num_docs:
                break
    else:
        logging.debug('bnGetSpacyDocFromIndex: doc info not found for doc index: %s ', str(doc_index))
    return filename, spacy_doc
