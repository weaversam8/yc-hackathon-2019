import re
import yaml
import json
import sys
from io import StringIO

# import tokenizers and wordnet
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import wordnet as wn

# import tagging stuff
from nltk import pos_tag
from nltk.help import upenn_tagset
from nltk import RegexpParser as NLTKRegexpParser

# import plantuml
from plantuml import PlantUML
planty = PlantUML(url='http://www.plantuml.com/plantuml/img/')

# merges adjacent text nodes into one text node in a nested object
# really annoying and please don't mess with it
def compact_arrays(tree):

    if isinstance(tree, dict):
        new_tree = {k: compact_arrays(v) for k, v in tree.items()}
        return new_tree
    
    if isinstance(tree, list):
        new_tree = []
        for item in tree:
            if len(new_tree) == 0:
                if isinstance(item, str):
                    new_tree.append(item)
                else:
                    new_tree.append(compact_arrays(item))
            elif isinstance(new_tree[-1], str) and isinstance(item, str):
                new_tree[-1] += ' ' + item
            elif isinstance(item, str):
                new_tree.append(item)
            else:
                new_tree.append(compact_arrays(item))
        return new_tree
    
    return tree

# splits strings in the dict into lists of sentences
def sentence_parse(tree):
    if isinstance(tree, dict):
        new_tree = {k: sentence_parse(v) for k, v in tree.items()}
        return new_tree
    
    if isinstance(tree, list):
        new_tree = []
        for item in tree:
            if isinstance(item, str):
                # if we're handling just a string, tokenize it by sentence via NLTK
                new_tree += sent_tokenize(item)
            else:
                new_tree.append(sentence_parse(item))
        return new_tree
    
    return tree

# gets all sentences from the tree
def all_sentences(tree, arr):
    if isinstance(tree, dict):
        for k, v in tree.items():
            arr = all_sentences(v, arr)
        return arr
    
    if isinstance(tree, list):
        for item in tree:
            arr = all_sentences(item, arr)
        return arr

    if isinstance(tree, str):
        arr.append(tree)
        return arr

    return arr

def generate_report(sentences):
    with open('./report.html', 'w') as report:
        report.write("<html>\n<head>\n<style>html, body {font-family:sans-serif;} sub { font-size: 0.5em; } .s { margin: 2em; } .we { color: #ff0000; font-weight: bold; } .you { color: #00cc33; font-weight: bold; } .noun { color: #0000ff; } .verb { color: #f08415; } </style>\n</head>\n<body>\n")
        report.write("<h1>Sentence Report</h1>\n")
        for sentence in sentences:
            report.write("  <div class='s'>" + sentence + "</div>\n")
        report.write("</body>\n</html>\n")
    
    print("report generated")

def highlight(words, word, cls):
    return list(map(lambda x: ('<span class="'+cls+'">' + x[0], x[1], x[2] + '</span>') if x[1][0].lower() == word else x, words))

def highlight_pos_arr(words, pos_arr, cls):
    return list(map(lambda x: ('<span class="'+cls+'">' + x[0], x[1], x[2] + '</span>') if x[1][1] in pos_arr else x, words))


def tag_wn(words):
    return list(map(lambda x: ('<u>' + x[0], x[1], x[2] + '</u>') if len(wn.synsets(x[1][0].lower())) == 0 else ('<span title="'+ str(wn.synsets(x[1][0].lower())[0]) +'">' + x[0], x[1], x[2] + '</span>'), words))

def add_pos(words):
    def get_help_tagset(tagset):
        # https://stackoverflow.com/a/1218951/4196127
        sys.stdout = StringIO()
        upenn_tagset(tagset)
        val = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
        return val

    return list(map(lambda x: (x[0], x[1], x[2] + '<sub title="'+get_help_tagset(x[1][1]).split("\n")[0]+'">' + x[1][1] + '</sub>'), words))

# splits each sentence not just into words but into lists of size 3
# the beginning and end of the list are there to allow the highlight
# functions to append without losing the original word
def word_tokenize_extra(sentence):
    words = word_tokenize(sentence)
    words = pos_tag(words)
    return list(map(lambda w: ('', w, ''),  words))

# see above, rejoins properly, concating the beginning and end
def rejoin(sentence):
    # trim away the part of speech
    sentence = map(lambda s: (s[0], s[1][0], s[2]), sentence)
    return " ".join(list(map(lambda s: "".join(s), sentence)))

# extract the word and POS from the 3-tuple
def extract_sentence_tuples(sentence):
    return list(map(lambda s: s[1], sentence))

with open('./policies/text/facebook.yaml') as file:
    # load the file as one continuous bit of memory
    content = "\n".join(file.readlines())

    # parse it into YAML and concat adjacent strings in lists
    tree = compact_arrays(yaml.load(content, Loader=yaml.FullLoader))

    # separate single strings into lists of sentences
    tree = sentence_parse(tree)

    # get a list of all the sentences
    sentences = all_sentences(tree, list())

    # tokenize the sentences using my new tokenizer
    sentences_tokenized = map(lambda s: word_tokenize_extra(s), sentences)

    # highlight "we" and "you"
    sentences_tokenized = map(lambda s: highlight(s, "we", "we"), sentences_tokenized)
    sentences_tokenized = map(lambda s: highlight(s, "you", "you"), sentences_tokenized)

    # underline any words that are not in WordNet and tag the synsets of those that are
    sentences_tokenized = map(lambda s: tag_wn(s), sentences_tokenized)

    # add the parts of speech
    sentences_tokenized = map(lambda s: add_pos(s), sentences_tokenized)

    # highlight nouns
    sentences_tokenized = map(lambda s: highlight_pos_arr(s, ["NN", "NNS"], "noun"), sentences_tokenized)
    sentences_tokenized = map(lambda s: highlight_pos_arr(s, ["VB", "VBP", "MD"], "verb"), sentences_tokenized)

    grammar = r"""
  STATEMENT: {<PRP><MD>?<VB|VBP><NN|NNS>}
"""

    parser = NLTKRegexpParser(grammar)
    test_sentences = map(lambda s: extract_sentence_tuples(s), sentences_tokenized)
    parsed_results = map(lambda s: parser.parse(s), test_sentences)

    list_of_statements = list()

    for result in parsed_results:
        for subtree in result.subtrees():
            if subtree.label() == 'STATEMENT':
                list_of_statements.append(subtree)
    
    plantuml = "@startuml\n\n"

    added_actors = set()
    added_relations = set()

    for tree in list_of_statements:

        words = tree.pos()
        actor_name = words[0][0][0].lower()
        if actor_name not in added_actors:
            last_node = ":" + actor_name + ":"
            plantuml += last_node + "\n"
            added_actors.add(actor_name)
        
        plantuml += "\n"
        
        if len(words) > 3:
            md_word = words[1][0][0]
            relation = (last_node, md_word)
            last_node = "("+md_word+")"
            if relation not in added_relations:
                plantuml += relation[0] + " --> "+last_node+"\n"
                added_relations.add(relation)
            # pretend like the MD isn't even there
            del words[1]
        
        verb = words[1][0][0]
        relation = (last_node, verb)
        last_node = "(" + verb + ")"
        if relation not in added_relations:
            plantuml += relation[0] + " --> " + last_node+"\n"
            added_relations.add(relation)
        
        noun = words[2][0][0]
        relation = (last_node, noun)
        last_node = "("+noun+")"
        if relation not in added_relations:
            plantuml += relation[0] + " --> " + last_node + "\n"
        
    plantuml += "@enduml\n"

    print(planty.get_url(plantuml))

    with open('./facebook.plantuml', 'w') as planty_output:
        planty_output.write(plantuml)
        print("plantuml output saved")

    # rejoin the sentences using my rejoiner function
    sentences = map(lambda s: rejoin(s), sentences_tokenized)

    # generate an HTML report
    generate_report(sentences)
