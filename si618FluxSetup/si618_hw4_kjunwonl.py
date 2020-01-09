# Calculate the average stars for each business category
# Written by Dr. Yuhang Wang and Josh Gardner
'''
To run on Fladoop cluster:
spark-submit --master yarn --num-executors 16 --executor-memory 1g --executor-cores 2 hw4.py

To get results:
hadoop fs -getmerge avg_stars_per_category_output avg_stars_per_category_output.txt
'''

import json
from pyspark import SparkContext
sc = SparkContext(appName="PySparksi618f19avg_stars_per_category")

input_file = sc.textFile("hdfs:///var/umsi618/hw4/business.json")

def cat_city(data):
    cat_cities_list = []
    stars = data.get('stars', None)
    categories_raw = data.get('categories', None)
    city = data.get('city', None)
    review = data.get('review_count', None)
    if categories_raw:
        categories = categories_raw.split(', ')
        for c in categories:
            if stars != None and review != None:
                cat_city_list.append(((city, c), (1, review, stars)))
    else:
        cat_city_list.append(((city, "Unknown"),(1, review, stars)))
    return cat_city_list

cat_stars = input_file.map(lambda line: json.loads(line)) \
                      .flatMap(cat_city) \
                      .mapValues(lambda x: (x[0], x[1], 1) if x[2]>=4 else (x[0], x[1], 0)) \
                      .reduceByKey(lambda x, y: (x[0] + y[0], x[1] + y[1], x[2] + y[2])) \
                      .sortBy(lambda x: (x[0][0], -x[1][0], -x[1][1], -x[1][2], x[0][1]), numPartitions = 1) \
                      .map(lambda t: t[0][0] + '\t' + t[0][1] + '\t' + str(t[1][0]) + '\t' + str(t[1][1]) + '\t' + str(t[1][2]))

cat_stars.collect()
cat_stars.saveAsTextFile("si618_hw4_output_kjunwonl")
