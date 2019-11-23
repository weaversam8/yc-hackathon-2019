import re
import yaml
from nltk.tokenize import sent_tokenize

with open('./policies/text/facebook.yaml') as file:
    # load the file as one continuous bit of memory
    content = "\n".join(file.readlines())

    tree = yaml.load(content)
    print(tree)
    exit()

    # split the file into sentences
    sentences = sent_tokenize(content)

    # replace every consecutive whitespace character with a single space, cleans it up
    # `list` is needed here because `map` creates a generator :rolling_eyes:
    sentences = list(map(lambda s: re.sub(r'\s+', ' ', s), sentences))

    print(sentences)