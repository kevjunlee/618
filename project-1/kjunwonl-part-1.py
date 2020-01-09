'''
spark-submit --master yarn --num-executors 4 --executor-memory 4g --executor-cores 4 si618_project1_kjunwonl.py
hadoop fs -getmerge si618_project1_kjunwonl si618_project1_kjunwonl.csv
hadoop fs -getmerge si618_project1_kjunwonl si618_project1_kjunwonl.csv
'''

import math
import re
from pyspark.sql import *
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.ml.feature import Bucketizer
from pyspark.sql.functions import udf
from pyspark.sql.types import *

sc = SparkContext(appName="si618_project1_kjunwonl")
sqlc = SQLContext(sc)

#organize homeless data
homelessdf = spark.read.format("csv").option("header", "true").load("2007-2016-Homelessnewss-USA.csv")
homelessdf.registerTempTable("homeless")
q1 = sqlContext.sql("select * from homeless where Year like '1/1/2014%' and State != 'GU' and State != 'PR'")
q1.show()
q1.registerTempTable("2014homeless")

q2 = sqlContext.sql("select State, Count from 2014homeless")
    
rdd = q2.rdd.map(tuple)
rdd.take(10)
newRDD = rdd.map(lambda x: (x[0], x[1].replace(",", "")))
    
states = newRDD.mapValues(lambda x: int(x)).reduceByKey(lambda x,y: x+y)
states.collect()

states_df = sqlc.createDataFrame(states, ['StateCodes', 'Count'])
states_df.registerTempTable("states")

#bring in income data set
incomedf = spark.read.format("csv").option("header", "true").load("download.csv")
incomedf.registerTempTable("income")

energydf = spark.read.format("csv").option("header", "true").load("Energy_Census_and_Economic_Data_US_2010-2014.csv")
energydf.registerTempTable("energy")

#join income and consumption
qc1 = sqlContext.sql("select StateCodes, State, TotalC2014 from energy")
qc1.registerTempTable("Consumption")
qc2 = sqlContext.sql("select StateCodes, TotalC2014, 2014_GDP_per_Capita, t1.State from Consumption as t1 join income as t2 where t1.State = t2.State")
qc2.registerTempTable("incomeConsumption")
qc2.coalesce(1).write.format('com.databricks.spark.csv').save('incomeConsumption',header = 'true')

#join the incomeConsumption with homelessness
qc3 = sqlContext.sql("select TotalC2014, 2014_GDP_per_Capita, Count, t1.StateCodes from incomeConsumption as t1 join states as t2 where t1.StateCodes = t2.StateCodes")
qc3.registerTempTable("homelessconsumption")
qc3.coalesce(1).write.format('com.databricks.spark.csv').save('consumptionHomeless',header = 'true')

#binning consumption to see if more homeless people are in high consumption areas
qc4 = sqlContext.sql("select TotalC2014, Count, StateCodes from homelessconsumption order by TotalC2014")
crdd = qc4.rdd.map(tuple)
crdd = crdd.map(lambda x: (int(x[0]), x[1], x[2]))
consumption_df = spark.createDataFrame(crdd, ["TotalC2014", "Count", "StateCodes"])
bucketizer = Bucketizer(splits=[ 0, 500000, 2000000, float('Inf') ], inputCol="TotalC2014", outputCol="buckets")
consumption_df_buck = bucketizer.setHandleInvalid("keep").transform(consumption_df)
t = {0.0:"low Consumption", 1.0: "Medium Consumption", 2.0:"High Consumption"}
udf_foo = udf(lambda x: t[x], StringType())
consumption_df_buck.withColumn("consumption_bucket", udf_foo("buckets")).show()
c_df_bucket = consumption_df_buck.withColumn("consumption_bucket", udf_foo("buckets"))
c_df_bucket.registerTempTable("consumptionHomelessBuck")
qc5 = sqlContext.sql("select consumption_bucket, Count, buckets from consumptionHomelessBuck order by consumption_bucket")
qc5.registerTempTable("binnedC")
qc5.coalesce(1).write.format('com.databricks.spark.csv').save('binnedconsumptionHomeless',header = 'true')

#analysis for average
qc6 = sqlContext.sql("select consumption_bucket, Count from binnedC")
crdd2 = qc6.rdd.map(tuple)
crdd2 = crdd2.mapValues(lambda x: int(x)).reduceByKey(lambda x,y: x+y)
mapped_binnedc_df = sqlc.createDataFrame(crdd2, ['consumption_bucket', 'Count'])
mapped_binnedc_df.registerTempTable("mappedbinnedc")
qc7 = sqlContext.sql("select consumption_bucket, cast(round(Count/16) as int) as averagehigh, cast(round(Count/25) as int) as averagemedium, cast(round(Count/9) as int) as averagelow from mappedbinnedc")



#join income and production
qp1 = sqlContext.sql("select StateCodes, State, TotalP2014 from energy")
qp1.registerTempTable("Production")
qp2 = sqlContext.sql("select StateCodes, TotalP2014, 2014_GDP_per_Capita, t1.State from Production as t1 join income as t2 where t1.State = t2.State")
qp2.registerTempTable("incomeProduction")
qp2.coalesce(1).write.format('com.databricks.spark.csv').save('incomeProduction',header = 'true')

#join incomeProduction with homelessness
qp3 = sqlContext.sql("select TotalP2014, 2014_GDP_per_Capita, Count, t1.StateCodes from incomeProduction as t1 join states as t2 where t1.StateCodes = t2.StateCodes")
qp3.coalesce(1).write.format('com.databricks.spark.csv').save('productionHomeless',header = 'true')
qp3.registerTempTable("homelessproduction")

#binning production
qp4 = sqlContext.sql("select TotalP2014, Count, StateCodes from homelessproduction order by TotalP2014")
prdd = qp4.rdd.map(tuple)
prdd = prdd.map(lambda x: (int(x[0]), x[1], x[2]))
production_df = spark.createDataFrame(prdd, ["TotalP2014", "Count", "StateCodes"])
bucketizer = Bucketizer(splits=[ 0, 500000, 2000000, float('Inf') ],inputCol="TotalP2014", outputCol="buckets")
production_df_buck = bucketizer.setHandleInvalid("keep").transform(production_df)
t = {0.0:"low Production", 1.0: "Medium Production", 2.0:"High Production"}
udf_foo2 = udf(lambda x: t[x], StringType())
production_df_buck.withColumn("production_bucket", udf_foo2("buckets")).show()
p_df_bucket = production_df_buck.withColumn("production_bucket", udf_foo2("buckets"))
p_df_bucket.registerTempTable("productionHomelessBuck")
qp5 = sqlContext.sql("select production_bucket, buckets, Count from productionHomelessBuck order by production_bucket")
qp5.registerTempTable("binnedP")
qp5.coalesce(1).write.format('com.databricks.spark.csv').save('binnedproductionHomeless',header = 'true')

#analysis for production
qp6 = sqlContext.sql("select production_bucket, Count from binnedP")
prdd2 = qp6.rdd.map(tuple)
prdd2 = prdd2.mapValues(lambda x: int(x)).reduceByKey(lambda x,y: x+y)
mapped_binnedp_df = sqlc.createDataFrame(prdd2, ['production_bucket', 'Count'])
mapped_binnedp_df.registerTempTable("mappedbinnedp")
qp7 = sqlContext.sql("select production_bucket, cast(round(Count/12) as int) as averagehigh, cast(round(Count/18) as int) as averagemedium, cast(round(Count/21) as int) as averagelow from mappedbinnedp")

#join income and expenditure
qe1 = sqlContext.sql("select StateCodes, State, TotalE2014 from energy")
qe1.registerTempTable("Expenditure")
qe2 = sqlContext.sql("select StateCodes, TotalE2014, 2014_GDP_per_Capita, t1.State from Expenditure as t1 join income as t2 where t1.State = t2.State")
qe2.registerTempTable("incomeExpenditure")
qe2.coalesce(1).write.format('com.databricks.spark.csv').save('incomeExpenditure',header = 'true')

#join incomeExpenditure with homelessness
qe3 = sqlContext.sql("select TotalE2014, 2014_GDP_per_Capita, Count, t1.StateCodes from incomeExpenditure as t1 join states as t2 where t1.StateCodes = t2.StateCodes")
qe3.coalesce(1).write.format('com.databricks.spark.csv').save('expenditureHomeless',header = 'true')
qe3.registerTempTable("homelessexpenditure")

#binning expenditure
qe4 = sqlContext.sql("select TotalE2014, Count, StateCodes from homelessexpenditure order by TotalE2014")
erdd = qe4.rdd.map(tuple)
erdd = erdd.map(lambda x: ((int(round(float(x[0])))), x[1], x[2]))
expenditure_df = spark.createDataFrame(erdd, ["TotalE2014", "Count", "StateCodes"])
bucketizer = Bucketizer(splits=[ 0, 30000, 100000, float('Inf') ],inputCol="TotalE2014", outputCol="buckets")
expenditure_df_buck = bucketizer.setHandleInvalid("keep").transform(expenditure_df)
t = {0.0:"low Expenditure", 1.0: "Medium Expenditure", 2.0:"High Expenditure"}
udf_foo3 = udf(lambda x: t[x], StringType())
expenditure_df_buck.withColumn("expenditure_bucket", udf_foo3("buckets")).show()
e_df_bucket = expenditure_df_buck.withColumn("expenditure_bucket", udf_foo3("buckets"))
e_df_bucket.registerTempTable("expenditureHomelessBuck")
qe5 = sqlContext.sql("select expenditure_bucket, buckets, Count from expenditureHomelessBuck order by expenditure_bucket")
qe5.registerTempTable("binnedE")
qe5.coalesce(1).write.format('com.databricks.spark.csv').save('binnedexpenditureHomeless',header = 'true')

#analysis for expenditure
qe6 = sqlContext.sql("select expenditure_bucket, Count from binnedE")
erdd2 = qe6.rdd.map(tuple)
erdd2 = erdd2.mapValues(lambda x: int(x)).reduceByKey(lambda x,y: x+y)
mapped_binnede_df = sqlc.createDataFrame(erdd2, ['expenditure_bucket', 'Count'])
mapped_binnede_df.registerTempTable("mappedbinnede")
qe7 = sqlContext.sql("select expenditure_bucket, cast(round(Count/2) as int) as averagehigh, cast(round(Count/12) as int) as averagemedium, cast(round(Count/37) as int) as averagelow from mappedbinnede")




