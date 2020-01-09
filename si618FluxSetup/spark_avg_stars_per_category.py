# Calculate the average stars for each business category
# Written by Dr. Yuhang Wang and Josh Gardner
'''
To run on Fladoop cluster:
spark-submit --master yarn --num-executors 16 --executor-memory 1g --executor-cores 2 spark_avg_stars_per_category.py

To get results:
hadoop fs -getmerge avg_stars_per_category_output avg_stars_per_category_output.txt
'''

import json
from pyspark import SparkContext
sc = SparkContext(appName="PySparksi618f19avg_stars_per_category")

input_file = sc.textFile("hdfs:///var/umsi618/hw4/business.json")

def cat_star(data):
    cat_star_list = []
    stars = data.get('stars', None)
    categories_raw = data.get('categories', None)
    if categories_raw:
        categories = categories_raw.split(', ')
        for c in categories:
            if stars != None:
                cat_star_list.append((c, stars))
    return cat_star_list


cat_stars = input_file.map(lambda line: json.loads(line)) \
                      .flatMap(cat_star) \
                      .mapValues(lambda x: (x, 1)) \
                      .reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1])) \
                      .map(lambda x: (x[0], x[1][0]/x[1][1]))

cat_stars.collect()
cat_stars.saveAsTextFile("avg_stars_per_category_output")
