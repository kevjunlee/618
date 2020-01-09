'''
spark-submit --master yarn --num-executors 4 --executor-memory 4g --executor-cores 4 si618_hw6_kjunwonl.py
hadoop fs -getmerge si618_hw6_kjunwonl_usefulreview si618_hw6_kjunwonl_usefulreview.txt
hadoop fs -getmerge si618_hw6_kjunwonl_uselessreview si618_hw6_kjunwonl_uselessreview.txt
'''
import json
import math
import re
from pyspark import SparkConf, SparkContext

sc = SparkContext(appName="si618_hw6_kjunwonl")

frequent_word_threshold=1000
WORD_RE = re.compile(r'\b[\w]+\b')

def convert_dict_to_tuples(d):
    text = d['text']
    useful = d['useful']
    tokens = WORD_RE.findall(text)
    tuples = []
    for w in tokens:
        tuples.append((useful, w))
    return tuples

input_file=sc.textFile("/var/umsi618/hw5/review.json")
# convert each json review into a dictionary
step_1a = input_file.map(lambda line: json.loads(line))

# convert a review's dictionary to a list of (useful, word) tuples
step_1b = step_1a.flatMap(lambda x : convert_dict_to_tuples(x))

# count all words from all reviews
step_2a2 = step_1b.map(lambda x: (x[1], 1)).reduceByKey(lambda a, b: a + b)

# filter out all word-tuples from useful reviews
step_2b1=step_1b.filter(lambda x:x[0]>5)

# count all words from useful reviews
step_2b2 = step_2b1.map(lambda x: (x[1], 1)).reduceByKey(lambda a, b: a + b)

# filter out all word-tuples from not usefull reviews
step_2c1 = step_1b.filter(lambda x: x[0] == 0)

# count all words from not useful reviews
step_2c2=step_2c1.map(lambda x:(x[1],1)).reduceByKey(lambda a,b:a+b)

# get total word count for all, useful, and not useful reviews
all_review_word_count = step_2a2.map(lambda x: x[1]).sum()
pos_review_word_count = step_2b2.map(lambda x:x[1]).sum()
neg_review_word_count = step_2c2.map(lambda x:x[1]).sum()

# filter to keep only frequent words, i.e. those with
# count greater than frequent_word_threshold.
freq_words=step_2a2.filter(lambda x:x[1]>frequent_word_threshold).cache()
# filter to keep only those word count tuples whose word can
# be found in the frequent list
step_3pos=freq_words.join(step_2b2)
step_3neg=freq_words.join(step_2c2)

# compute the log ratio score for each useful review word
unsorted_positive_words = step_3pos.map(lambda x: (x[0], math.log(float(x[1][1])/pos_review_word_count ) - math.log(float(x[1][0])/all_review_word_count)))
# sort by descending score to get the top-scoring useful words
sorted_positive_words = unsorted_positive_words.sortBy(lambda x: x[1], ascending = False)

# compute the log ratio score for each not useful review word
unsorted_negative_words = step_3neg.map(lambda x:(x[0],math.log(float(x[1][1])/neg_review_word_count) - math.log(float(x[1][0])/all_review_word_count)))
# sort by descending score to get the top-scoring not useful words
sorted_negative_words = unsorted_negative_words.sortBy(lambda x: x[1], ascending = False)

# write out the top-scoring useful words to a text file
sorted_positive_words.saveAsTextFile("si618_hw6_kjunwonl_usefulreview")
# write out the top-scoring not useful words to a text file
sorted_negative_words.saveAsTextFile("si618_hw6_kjunwonl_uselessreview")
