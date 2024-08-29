---
date: 2024-08-12
modified: 2024-08-26T22:22:19+02:00
---
These notes about **Partitioning** will be "notebook-style" and only important and useful operations will be shown in this article (hence, very probably, no such operations will be shown: DataFrame creation, session state creation, etc.). For the complete code, refers to these notebooks I uploaded on a specific repository on [this link](metti!!!).
# 0. Resources
* [*Data with Nikk the Greek* YouTube Channel](https://www.youtube.com/@DataNikktheGreek)
# 1. First sneak peak into Spark Partitions
 General hints:
 * `df.rdd.getNumPartitions()` returns the number of partitions of the current Spark DataFrame;
 * `df.write.format("noop").mode("overwrite")` is used to specify a no-operation (noop) data sink, which effectively performs no action, often for testing or debugging purposes.

Let's understand what's the default parallelism by running:
```python
spark: SparkSession = SparkSession \
    .builder \
    .appName("Partitioning 1") \
    .master("local[4]") \
    .enableHiveSupport() \
    .getOrCreate()

sc = spark.sparkContext
spark.sparkContext.defaultParallelism
```
* The variable `spark.sparkContext.defaultParallelism` returns the level of parallelism and, by default, it's the number of cores available to application. Indeed from the above code we got `4`.
* The number of cores is the maximum number of tasks you can execute in parallel.

In the following three sub-chapters we'll see **two ways to influence the number of partitions during the creation of a DataFrame** (either with `spark.CreateDataFrame()` and `spark.range()` functions):
1. set the number of cores available to application;
2. use the `num_partitions` argument of the `spark.range()` function.
## 1.1. Partition Size based on Cores and Data Amount with `spark.CreateDataFrame()`
Let' use define a function using the `spark.CreateDataFrame()` to create a DataFrame:
```python
def sdf_generator1(num_iter: int = 1) -> DataFrame:
    d = [
        {"a":"a", "b": 1},
        {"a":"b", "b": 2},
        {"a":"c", "b": 3},
        {"a":"d", "b": 4},
        {"a":"e", "b": 5},
        {"a":"e", "b": 6},
        {"a":"f", "b": 7},
        {"a":"g", "b": 8},
        {"a":"h", "b": 9},
        {"a":"i", "b": 10},
    ]

    data = []
    for _ in range(0, num_iter):
        data.extend(d)
    ddl_schema = "a string, b int"
    df = spark.createDataFrame(data, schema=ddl_schema)
    return df
```

If we create a DataFrame by running `sdf_gen1 = sdf_generator1(2)` and we take a look at the number of partitions by runnning `sdf_gen1.rdd.getNumPartitions()`, we'll get `4`:

Also, you can check in the *Executor* tab in the Spark UI:
![](Apache%20Spark/attachments/Pasted%20image%2020240812144551.png)

We can also visualize which partition each row of the DataFrame belongs to:
```python
sdf_part1 = sdf_gen1.withColumn("partition_id", f.spark_partition_id())
sdf_part1.show()
```
Output:
```
+---+---+------------+
|  a|  b|partition_id|
+---+---+------------+
|  a|  1|           0|
|  b|  2|           0|
|  c|  3|           0|
|  d|  4|           0|
|  e|  5|           0|
|  e|  6|           1|
|  f|  7|           1|
|  g|  8|           1|
|  h|  9|           1|
|  i| 10|           1|
|  a|  1|           2|
|  b|  2|           2|
|  c|  3|           2|
|  d|  4|           2|
|  e|  5|           2|
|  e|  6|           3|
|  f|  7|           3|
|  g|  8|           3|
|  h|  9|           3|
|  i| 10|           3|
+---+---+------------+
```

From this output we can see that data is distributed quite uniformly among partitions and we can prove that by running:
```python
row_count = sdf_gen1.count()
sdf_part_count1 = sdf_part1.groupBy("partition_id").count()
sdf_part_count1 = sdf_part_count1.withColumn("count_perc", 100*f.col("count")/row_count)
sdf_part_count1.show()
```
Output:
```
+------------+-----+----------+
|partition_id|count|count_perc|
+------------+-----+----------+
|           0|    5|      25.0|
|           1|    5|      25.0|
|           2|    5|      25.0|
|           3|    5|      25.0|
+------------+-----+----------+
```

This uniformity reflects also on the computation time. Indeed if we run this code
```python
sc.setJobDescription("Gen1_Exp1")
sdf_gen1_1.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")
```
we can notice that uniformity in this job detail's page in the Spark UI:
![](Apache%20Spark/attachments/Pasted%20image%2020240812150330.png)

Let's repeat this experiment for a bigger dataframe:
```python
sdf_gen1_2 = sdf_generator1(2000)

sdf_part1_2 = sdf_gen1_2.withColumn("partition_id", f.spark_partition_id())
row_count = sdf_gen1_2.count()
sdf_part_count1_2 = sdf_part1_2.groupBy("partition_id").count()
sdf_part_count1_2 = sdf_part_count1_2.withColumn("count_perc", 100*f.col("count")/row_count)
sdf_part_count1_2.show()
```
Output:
```
+------------+-----+----------+
|partition_id|count|count_perc|
+------------+-----+----------+
|           0| 5120|      25.6|
|           1| 5120|      25.6|
|           2| 5120|      25.6|
|           3| 4640|      23.2|
+------------+-----+----------+
```
And let's trigger a job with:
```python
sc.setJobDescription("Gen1_Exp2")
sdf_gen1_2.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")
```

The bejaviour looks very similar to the previous one:
![](Apache%20Spark/attachments/Pasted%20image%2020240812151410.png)

>[!note]
>The size of the data does not have any influence on the number of partitions (if you load a file there will be some influence as we'll see later on).
>
## 1.2. Partition Size based on Cores and Data Amount with `spark.range()`
Now we use another function to create a dataframe:
```python
def sdf_generator2(num_rows: int, num_partitions: int = None) -> DataFrame:
    return (
        spark.range(num_rows, numPartitions=num_partitions)
        .withColumn("date", f.current_date())
        .withColumn("timestamp",f.current_timestamp())
        .withColumn("idstring", f.col("id").cast("string"))
        .withColumn("idfirst", f.col("idstring").substr(0,1))
        .withColumn("idlast", f.col("idstring").substr(-1,1))
        )
        
sdf_gen2 = sdf_generator2(2000000)
sdf_gen2.rdd.getNumPartitions()
```
We got `4` still here.

All the considerations we did in the previous chapter are still valid here and you'll get the same results.
## 1.3. Influence on Spark partitions to the performance
As we mentioned above, the `spark.range()` function allows us to influence the number of partitions. Let's create a bunch of new dataframes:
```python
sdf4 = sdf_generator2(20000000, 4)
print(sdf4.rdd.getNumPartitions())
sc.setJobDescription("Part Exp1")
sdf4.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sdf8 = sdf_generator2(20000000, 8)
print(sdf8.rdd.getNumPartitions())
sc.setJobDescription("Part Exp2")
sdf8.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sdf3 = sdf_generator2(20000000, 3)
print(sdf3.rdd.getNumPartitions())
sc.setJobDescription("Part Exp3")
sdf3.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sdf6 = sdf_generator2(20000000, 6)
print(sdf6.rdd.getNumPartitions())
sc.setJobDescription("Part Exp4")
sdf6.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sdf200 = sdf_generator2(20000000, 200)
print(sdf200.rdd.getNumPartitions())
sc.setJobDescription("Part Exp5")
sdf200.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sdf20000 = sdf_generator2(20000000, 20000)
print(sdf20000.rdd.getNumPartitions())
sc.setJobDescription("Part Exp6")
sdf20000.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")
```
* `sdf4`: the 4 cores work on the 4 partitions in parallel.
* `sdf8`: the 4 cores work on 4 partitions in parallel; once this step is executed the remaining 4 partitions are being executed in parallel again:
	![](Apache%20Spark/attachments/Pasted%20image%2020240812163220.png)
* `sdf3`: only three cores are working and the remaining one is set in IDLE, so we're wasting our resources, hence the performance is not optimized:
	![](Apache%20Spark/attachments/Pasted%20image%2020240812163428.png)
* `sdf6`: the 4 cores work on 4 partitions in parallel; after that only two cores will work on the remaining two partitions while the other two cores are set in IDLE. Again we're wasting our resources, hence the performance is not optimized:
	![](Apache%20Spark/attachments/Pasted%20image%2020240812163715.png)
* `sdf200` and `sdf20000`: the same consideration of `sdf6`.

---
# 2. Coalesce
How **Coalesce** works:
* it's a narrow transformation.
* can only reduce and not increase the number of partitions. it does not return any errors, but it just ignores a value higher than the initial available partitions.
* Coalesce can skew the data within each partition which leads to lower performance and some tasks running way longer.
* Coalesce can help with efficiently **reducing high number of small partitions** and improve performance. Remember a too high number of partitions leads to a lot of scheduling overhead.
* A too small number of partitions (bigger partitions) can result to OOM or other issues. A factor of 2-4 of the number of cores is recommended. But really depends on the memory available. If you can't increase the number of cores the only option of a stable execution not reaching the limits of your memory is increasing the number of partitions. Recommendations in the internet say anything between 100-1000 MB. Spark sets his max partition bytes parameter to 128 MB.

Suppose you have a DataFrame with 4 partitions and we use `.coalesce()` function to reduce the number of partitions from 4 to 3:
```python
sdf2 = sdf1.coalesce(3)
sdf2.rdd.getNumPartitions()
```

Let's see the data repartition across these 3 new partitions:
```python
row_count2 = sdf2.count()
sdf_part2 = sdf2.withColumn("partition_id", f.spark_partition_id())
sdf_part_count2 = sdf_part2.groupBy("partition_id").count()
sdf_part_count2 = sdf_part_count2.withColumn("count_perc", 100*f.col("count")/row_count2)
sdf_part_count2.show()
```
Output:
```
+------------+----------+----------+
|partition_id|     count|count_perc|
+------------+----------+----------+
|           0| 500000000|      25.0|
|           1| 500000000|      25.0|
|           2|1000000000|      50.0|
+------------+----------+----------+
```
Basically with coalesce two partitions have been merged into one large partition of 1 million rows.
## 2.1. Comparisons
Let's run:
```python
sc.setJobDescription("Baseline 4 partitions")
sdf1.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")

sc.setJobDescription("Coalesce from 4 to 3")
sdf2.write.format("noop").mode("overwrite").save()
sc.setJobDescription("None")
```

In the "*Baseline 4 partitions*" scenario we have:
* each core processes 500.000.000 rows
* the execution time is uniform
![](Apache%20Spark/attachments/Pasted%20image%2020240812184724.png)

In the "*Coalesce from 4 to 3*" scenario we have:
* 1 core executes  500.000.000 rows
![](Apache%20Spark/attachments/Pasted%20image%2020240812184954.png)