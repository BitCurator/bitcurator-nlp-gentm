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
            input_file_contents = textacy.fileio.read.read_file(infile, mode=u'rt', encoding=None)
            
        return input_file_contents
    
class BcnlpExtractEntity:
    """ Using Textacy APIs, this defines methods for extracting useful information
        from the given files.
    """
    
    def __init__(self, infile):
        ec = ExtractFileContents()

        input_file_contents = ec.extractContents(infile)        
        self.doc = textacy.Doc(input_file_contents)

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

