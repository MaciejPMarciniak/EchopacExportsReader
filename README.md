# Building inductive data set from individual patient data for analysis and visualization
The project consists of methods to build a data set from patient-specific samples, providing the user with a tidy,
organized table to explore and hypothesize. In explicit, from a given set of .xml files exported from the 
**EchoPAC** software, a single table is generated, consisting of all relevant fields accounted for during clinical image 
analysis. With cases as rows and features as columns, the data set is designed for quick exploration and statistical
research.

### Extracted features
From the **EchoPAC** exports, the following parameters are extracted:
 * heart rate,
 * valve opening times,
 * blood pressure,
 * ejection fraction
 * global and segmental work indices:
    * myocardial work efficiency,
    * constructive work,
    * wasted work,
    * positive work,
    * negative work,
    * Sys(?) constructive work,
    * Sys(?) wasted work,
 * post-systolic strain PSS(?),
 * average segmental strain,
 * systolic and diastolic pressure,
 * global and segmental strain measurements,
 * myocardial work indices.
   
In addition to the raw indices, new features were derived, to provide the user with information relevant for 
results publication, such as:
 * frame rate for each of the views (4C, 3C, 2C),
 * segmental post-systolic boolean classification, which indicates whether the minimum strain took place after the 
 aortic valve closure (AVC),
 * segmental post-systolic index - ratio between the strain at AVC and the minimum strain,
 * segmental minimum strain value,
 * segmental strain value at AVC,
 * segmental time-to-peak - time from th beginning of the cycle to minimum strain,
 * segmental time-to-peak ratio - ratio between time-to-peak and cycle duration,
 * minimum global strain before AVC,
 * minimum global strain,
 * time of minimum global strain.
 
### Complementary tools

A few additional functions are implemented to ease the visualization and comparative studies. In explicit, the values 
necessary for createing 17 and 18 AHA polar plots of the left ventricle are provided. The functions build a data frame
consisting of mean and median values of the parameters of interest, one for each of the 17 or 18 segments. These values
can be obtained for multiple categorized patient groups. Moreover, the representatives of each group (closest to the
mean or median with regards to segmental values) can be found

# Motivation
Statistical models rely on the sets of samples to infer the behaviour of similar samples, classifiy them and build
predictions based on them. In general, the more samples are gathered, the more robust and reliable the model is and more
features of a sample can be explored. Population studies on the relatively new indices of function such as strain
and myocardial work are becoming increasingly popular, however it is difficult to gather the data necessary for analysis
and inductive reasoning.

EchoPAC software enables an export of individual patient data on the structure and function of the left ventricle. The
data is saved in the .xml or .txt files, which are not designed for research. Obtaining comparable data is hindered by
the structure of these exports, making it difficult to perform comparative studies for clinicians. With this tool, the 
data is transformed into easily applicable structure at a minimal cost.

# Screenshots (anonymized data)
1. xml in the firefox format
2. xml in the excel format - single patient data, across multiple sheets
3. txt in notepad - segments named with segments
4. result - single table 

# How2use

### class Cohort (bsh.py)

**Call**
```python
class Cohort(source_path='path_to_data', view='4C', output_path='path_to_store_results', 
output='name_of_output_file.csv')
```

**Input**

*source_path*: path to the .csv files containing the myocardial trace obtained with speckle tracing in EchoPAC. 
 

*view*: the view in which the image was taken; 4-chamber ('4C'), 3-chamber ('3C'), or 2-chamber ('2C') 

 
*output_path*: path to a folder where the results of computation and plots will be stored 

 
**Output** 


---
**Methods**


# Credits


# License