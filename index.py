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

with open('./policies/text/facebook.yaml') as file:
    # load the file as one continuous bit of memory
    content = "\n".join(file.readlines())

    tree = compact_arrays(yaml.load(content))

    print(json.dumps(tree))
    exit()

    # split the file into sentences
    sentences = sent_tokenize(content)

    # replace every consecutive whitespace character with a single space, cleans it up
    # `list` is needed here because `map` creates a generator :rolling_eyes:
    sentences = list(map(lambda s: re.sub(r'\s+', ' ', s), sentences))

    print(sentences)