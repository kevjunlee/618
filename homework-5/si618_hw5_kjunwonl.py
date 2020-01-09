'''
spark-submit --master yarn --num-executors 4 --executor-memory 4g --executor-cores 4 si618_hw5_kjunwonl.py
hadoop fs -getmerge si618_hw5_kjunwonl si618_hw5_kjunwonl.csv
hadoop fs -getmerge si618_hw5_kjunwonl_goodreview si618_hw5_kjunwonl_goodreview.csv
hadoop fs -getmerge si618_hw5_kjunwonl_badreview si618_hw5_kjunwonl_badreview.csv
'''
#worked with Iain Graham and Shrijesh Siwakoti
import json
from pyspark.sql import *
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark import SparkContext
from pyspark.sql import SQLContext
sc = SparkContext(appName="si618_hw5_kjunwonl")
sqlContext = SQLContext(sc)

businessdf = sqlContext.read.json("hdfs:///var/umsi618/hw5/business.json")
reviewdf = sqlContext.read.json("hdfs:///var/umsi618/hw5/review.json")
businessdf.registerTempTable("Business")
reviewdf.registerTempTable("Review")
q1 = sqlContext.sql("select t1.business_id as Business_ID, t1.stars as Stars_from_review, t1.user_id , t2.city from review as t1 join business as t2 where t1.business_id = t2.business_id sort by t1.user_id")
q1.registerTempTable("tablesJoined")
q2 = sqlContext.sql("select t1.user_id as user_id1, t2.user_id as user_id2, t1.Stars_from_review, t1.city from tablesJoined as t1 join tablesJoined as t2 where t1.user_id = t2.user_id")
q2.show()
q2.registerTempTable("final")
q3 = sqlContext.sql("select user_id1, count(distinct city) as city_count from final where user_id1 = user_id2 and Stars_from_review > 1 group by user_id1")
q3.registerTempTable("last")
q4 = sqlContext.sql("select city_count from last")
hist = q4.rdd.flatMap(lambda x : x).histogram(range(1,82))
countTuples1 = zip(hist[0],hist[1])
save1 = sqlContext.createDataFrame(countTuples1,['city','yelp users'])
save1.coalesce(1).write.format("com.databricks.spark.csv").save("si618_hw5_kjunwonl", header = True)

# Good Reviews:
q5 = sqlContext.sql("select user_id1, count(distinct city) as city_count from final where user_id1 = user_id2 and Stars_from_review > 3 group by user_id1")
q5.registerTempTable("lastgood")
q6 = sqlContext.sql('select city_count from lastgood')
hist2 = q6.rdd.flatMap(lambda x : x).histogram(range(1,79))
countTuples2 = zip(hist2[0],hist2[1])
save2 = sqlContext.createDataFrame(countTuples2,['city','yelp users'])
save2.coalesce(1).write.format("com.databricks.spark.csv").save("si618_hw5_kjunwonl_goodreview", header = True)


# Bad Reviews:
q7 = sqlContext.sql("select user_id1, count(distinct city) as city_count from final where user_id1 = user_id2 and Stars_from_review < 3 group by user_id1 ")
q7.registerTempTable("lastbad")
q8 = sqlContext.sql("select city_count from lastbad")
hist3 = q8.rdd.flatMap(lambda x : x).histogram(range(1,39))
countTuples3 = zip(hist3[0],hist3[1])
save3 = sqlContext.createDataFrame(countTuples3,['city','yelp users'])
save3.coalesce(1).write.format("com.databricks.spark.csv").save("si618_hw5_kjunwonl_badreview", header = True)
