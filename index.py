from nltk.tokenize import sent_tokenize

with open('./policies/text/facebook.txt') as file:
    content = "\n".join(file.readlines())

    sentences = sent_tokenize(content)

    print(sentences)