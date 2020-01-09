import mrjob
from mrjob.job import MRJob
import re

#regular expression
word_RE = re.compile(r"\w{5,}")

class MRMostUsedWord(MRJob):
    pass
    
    def mapper(self, _, line):
        words = word_RE.findall(line)
        for word in words:
            yield word.lower(), 1

    def combiner(self, word, counts):
        yield word, sum(counts)

    def reducer(self, word, counts):
        yield word, sum(counts)

if __name__ == "__main__":
    MRMostUsedWord.run()

