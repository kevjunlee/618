'''
spark-submit --master yarn --num-executors 4 --executor-memory 4g --executor-cores 4 si618_hw5_kjunwonl.py
hadoop fs -getmerge si618_hw6_kjunwonl_usefulreview si618_hw6_kjunwonl_usefulreview.txt
hadoop fs -getmerge si618_hw6_kjunwonl_uselessreview si618_hw6_kjunwonl_uselessreview.txt
'''
import json
import math
import re
from pyspark import SparkConf, SparkContext

sc = SparkContext(appName="si618_lab6_kjunwonl")
sqlContext = SQLContext(sc)

input_file = sc.textFile("/var/umsi618/hw5/review.json")
input_file.take(10)
input = input_file.map(lambda line: json.loads(line))
WORD_RE = re.compile(r'\b[\w]+\b')

def convert_dict_to_tuples(d):
    text = d['text']
    rating = d['stars']
    tuples = []
    tokens = WORD_RE.findall(text.lower())
    for t in tokens:
        tuples.append((rating, t))
    return tuples

rating_word1a = input
rating_word1b = input.flatMap(lambda x: convert_dict_to_tuples(x))
rating_word1b.take(10)

rating_word2a2 = rating_word.map(lambda x: x[1], 1).reduceByKey(lambda x, y: x + y)
rating_word2a2.take(10)
rating_word2b1 = rating_word1b.filter(lambda x: x[0] >=5)
rating_word2b2 = rating_word2b1.map(lambda x: x[1], 1).reduceByKey(lambda x, y: x + y)
rating_word2b2.take(10)

rating_word2c1 rating_word1b.filter(lambda x: x[0] == 0)
rating_word2c2 = rating_word2c1.map(lambda x: x[1], 1).reduceByKey(lambda x, y: x + y)
all_review_count = rating_word2a2.map(lambda x: x[1]).sum()

useful_review_count = rating_word2b2.map(lambda x: x[1]).sum()
useless_review_count = rating_word2c2.map(lambda x: x[1]).sum()

freq_words = rating_word2a2.filter(lambda x: x[1] > 1000).cache()
rating_words3useful = freq_words.join(rating_word2b2)
rating_words3useful.take(10)
rating_words3useless = freq_words.join(rating_word2c2)
rating_words3useless.take(10)

useful = rating_words3useful.map(lambda x: x[0], (math.log(float(x[1][1])/useful_review_count)- math.log(float(x[1][0])/all_review_count)))

sorted_useful = useful.sortBy(lambda x: x[1], ascending =False)
sorted_useful.take(10)

useless = rating_words3useless.map(lambda x: x[0], (math.log(float(x[1][1])/useless_review_count)- math.log(float(x[1][0])/all_review_count)))
sorted_useless = useless.sortBy(lambda x: x[1], ascending =False)

sorted_useful.saveAsTextFile("si618_hw6_kjunwonl_usefulreview")
sorted_useless.saveAsTextFile("si618_hw6_kjunwonl_uselessreview")

