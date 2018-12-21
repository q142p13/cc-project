import org.apache.spark.SparkContext
import org.apache.spark.SparkConf
import scala.collection.mutable.Set

object Recommend {
  def main(args: Array[String]) {
    val searchStr = args(0)
    val inputFile = args(1)
    val outputFile = args(2)
    val conf = new SparkConf().setAppName("Recommend")
    val sc = new SparkContext(conf)
    val textFile = sc.textFile(inputFile)
    textFile.map( line => {
      // Id, ProductId, HelpfulnessNumerator, HelpfulnessDenominator, Score, Summary, Text
      val elems = line.split('\t')
      val score = elems(4)
      (score*getSimilarity(searchStr, elems(6)), elems(1), elems(5), elems(6))
    }).sortBy(_._1, false).top(10).saveAsTextFile(ouputFile)
  }

  def getSimilarity(str1 : String, str2 : String): Double = {
    val set1: Set[String] = Set()
    val set2: Set[String] = Set()
    for (a <- str1.toLowerCase().split(" "))
      set1.add(a)
    for (a <- str2.split(" "))
      set2.add(a)
    return set1.&(set2).size * 1.0 / set1.size
  }

}

