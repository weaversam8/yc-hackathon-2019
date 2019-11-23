import re
import yaml
import json
from nltk.tokenize import sent_tokenize

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
        report.write("<html>\n<head>\n<style>html, body {font-family:sans-serif;} .s { margin: 2em; }</style>\n</head>\n<body>\n")
        report.write("<h1>Sentence Report</h1>\n")
        for sentence in sentences:
            report.write("  <div class='s'>" + sentence + "</div>\n")
        report.write("</body>\n</html>\n")
    
    print("report generated")

with open('./policies/text/facebook.yaml') as file:
    # load the file as one continuous bit of memory
    content = "\n".join(file.readlines())

    # parse it into YAML and concat adjacent strings in lists
    tree = compact_arrays(yaml.load(content, Loader=yaml.FullLoader))

    # separate single strings into lists of sentences
    tree = sentence_parse(tree)

    # get a list of all the sentences
    sentences = all_sentences(tree, list())

    # generate an HTML report
    generate_report(sentences)
