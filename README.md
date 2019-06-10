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

# Screenshots 
All presented screenshot come form randomly created, probable data representing the original exports from the 
**EchoPAC** software.

### Input - .xml export file with functional data of a single patient
The data is provided in a specific XML structure, which is illegible. It is also possible to open the file with
applications such us MS Excel, as a table. However, population studies on these files would be time-consuming and 
laborious.
![smooth plots](images/xml_example_gedit.png  "Segmental Strain - Echopac version")

### Input - .txt export file with functional data of a single patient
Less data is available in the case of a single view export. However, it is still possible to extract the data on
segmental strain (color-coded).
![smooth plots](images/txt_example.png  "Segmental Strain - Echopac version")

### Output - myocardial function population data
ID | HR | MVC (ms) | ... | GWE (%) | GWI (mmHg%) |... |  SBP (mmHg) | DBP (mmHg) | MW_Basal Inferior (mmHg%) | MW_Basal Posterior (mmHg%)| ...
 :---:|:---:|:---:| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---:  
ABC001 | 63	| 24    | ... | 0.97	| 2054  | ... | 136	| 83	| 1524	| 2234	| ... 
ACD002 | 77	| 45	| ... | 0.99	| 1725	| ... | 121	| 73	| 1281	| 1875 | ... 
ADE003 | 79	| 38	| ... | 0.97	| 2262	| ... | 152	| 92	| 1362	| 2893 | ... 
AEF004	| 65 | 32	| ... | 0.95	| 1254	| ... | 115	| 77	| 1123	| 1490 | ... 
AFG005	| 67 | 13	| ... | 0.96	| 2032	| ... | 134	| 85	| 1552	| 1750 | ... 
AGH006	| 84 | 37	| ... | 0.98	| 2472	| ... | 126	| 72	| 2762	| 3312 | ... 



### Output - mean and median values of strain and myocardial work in the population


### Output - printed represetnatives of the given patient groups


# How2use

### class Cohort (bsh.py)

**Call**
```python
from echo_data_set import EchoDataSet
path_to_data = 'data/exports'
path_to_output = 'data/output'
eds = EchoDataSet(input_path=path_to_data, output_path=path_to_output, output='all_cases.csv', export_file_type='xml')
   
```

**Input**

*input_path*: path to the .xml/.txt files containing the exports from **EchoPAC**,

 
*output_path*: path to a folder where the resulting table, the 17 and/or 18 AHA values and group representatives
will be stored,

*output*: name of the file to which the table is saved,

*export_file_type*: xml or txt, the type of exports from which the data set is created.
 
**Output** 


---
**Methods**


# Credits


# License