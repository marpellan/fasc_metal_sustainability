Title: Country-level metal and mineral production data (USGS & BGS sources, 1994–2022)

Description: This repository contains two harmonized datasets providing country-level production data for a wide range of metals and minerals, spanning the years 1994 to 2022. The datasets are based on data published by the United States Geological Survey (USGS) and the British Geological Survey (BGS).
These data (from both USGS and BGS sources) were used in the preliminary stages of a research article for constructing HHI metrics (Bucciarelli, P., Hache, E., & Mignon, V. (2025). Evaluating criticality of strategic metals: Are the Herfindahl–Hirschman Index and usual concentration thresholds still relevant? Energy Economics, 143, 108208 [https://doi.org/10.1016/j.eneco.2025.108208]). The HHI dataset derived from these data is available here: https://pladifes.institutlouisbachelier.org/critical-metals/.

Datasets Included: production_USGS_data.csv, production_BGS_data.csv

USGS Dataset (production_USGS_data.csv):
- Source: USGS Minerals Yearbook (annual publications from 1996 to 2024).In the publication for year i, the USGS provides production data for year i-2.
- Time span: 1994–2022
- Extraction method: A code was developed to extract data directly from the PDFs of the Yearbooks using automated parsing techniques. Despite verification efforts, some errors may persist due to parsing inconsistencies or OCR limitations.
- Limitations: Not all metadata from the original PDFs was extracted. In particular, values for the United States are sometimes marked as “Withheld to avoid disclosing company proprietary data” and may be excluded from the reported world total.
- Specific Changes in the USGS Dataset by material:
	- Gypsum : In the 2019 USGS Yearbook (covering year 2017), the reported production of gypsum in China shows a sharp decline. According to the USGS, "Prior year chapters of this commodity included gypsum production for China that totaled as much as 130 million tons. However, recently acquired information revealed that the vast majority of that amount was likely synthetic gypsum, which is not 'mine production.' Hence, the large decrease in reported gypsum in China reflects a recategorization of gypsum material and should not be interpreted as a large decrease in the overall total world production of gypsum nor the production of gypsum in China." China's gypsum production shows an abrupt increase between 2006 and 2007 in earlier publications. To retain only mine production, we applied a linear interpolation between the 2006 and 2017 values for China for the years 2007 to 2016. (The corresponding amount is reduced from the world total to maintain consistency)
	- Magnesium-compound : For magnesite, the reporting unit changes over time. Until the 2016 Yearbook (covering data through 2014), China’s production values are reported in terms of magnesium content (atomic mass: 24.304). Starting with the 2017 Yearbook (covering 2015 data), the values are reported as gross weight of magnesite (MgCO₃) (molar mass: 83.315). To ensure consistency and alignment with the World Mining Data classification, all values have been converted into magnesite equivalent. (The corresponding amount is reduced from the world total to maintain consistency)
	- Strontium : In the 2002 publication for strontium, the reported production value for China was estimated at 200,000 tonnes. Based on our assessment, this figure appears too high. We adjusted the value to 50,000 tonnes and reduced the corresponding amount from the world total to maintain consistency.
	- Sulfur : Starting with the 2018 USGS publication (reporting year 2016), the reported production of sulfur in China increases significantly. According to the USGS, this is due to a change in the accounting method: "China sulfur production includes byproduct elemental sulfur recovered from natural gas and petroleum, the estimated sulfur content of byproduct sulfuric acid from metallurgy, and the sulfur content of sulfuric acid from pyrite." To ensure consistency with other data sources —especially with the World Mining Data (WMD)—we replaced the Chinese sulfur production values from 2016 to 2021 with the corresponding figures from WMD. For 2022, we applied a proportional estimate based on the USGS year-over-year variation and the 2021 WMD value. (The corresponding amount is reduced from the world total to maintain consistency)
	- Tungsten : For tungsten, the 2009 USGS Yearbook states: "Production estimates for China were revised downward to represent tungsten content of concentrates." This revision causes China's reported production to drop from 79,000 to 41,000 tonnes. Earlier figures were likely overestimated. To correct this, we replaced China's production values and corresponding world totals for the years 1999 to 2006 using data from the British Geological Survey (BGS) (The corresponding amount is reduced from the world total to maintain consistency)

BGS Dataset (production``_BGS_data.csv):
- Source: World Mineral Statistics Dataset (British Geological Survey)
- Time span: 1994–2022
- Extraction method: A web scraping script was written to extract structured data from the BGS online database.

Column Descriptions (applies to both datasets):
- material: Name of the metal or mineral
- stage: Production stage in the material value chain such as 'mine', 'smelter', or 'refinery'. Some materials are listed with the type 'production' when no specific stage is indicated in the USGS or BGS documentation.
- country: Name of the producing country
- year: Calendar year of reported production (from 1994 to 2022)
- value: Reported production quantity (in tonnes)
- note: Optional field with clarifications

Units and Measurement:
- All values are expressed in metric tonnes.
- For minerals, the quantity refers to the gross weight of the mineral.
- For metals, the quantity reflects the metal content, unless otherwise specified in the note column.


Limitations: The raw production data from both the USGS and BGS sources are not the final results used in the article. Robustness and consistency checks were conducted exclusively at the level of the HHI indicators, not directly on the raw production data shared here.

Licensing & Reuse:
- The original data are publicly available from the USGS and BGS.
- This compilation is shared for reproducibility and academic transparency. Users are encouraged to validate figures with original sources for any critical applications.
- Please cite this dataset in any derivative work : Bucciarelli,P. (2025). Country-level metal and mineral production data (USGS & BGS sources, 1994–2022). Zenodo. [https://doi.org/10.5281/zenodo.15431056]
- A reference to our paper would also be appreciated: Bucciarelli, P., Hache, E., & Mignon, V. (2025). Evaluating criticality of strategic metals: Are the Herfindahl–Hirschman Index and usual concentration thresholds still relevant? Energy Economics, 143, 108208 [https://doi.org/10.1016/j.eneco.2025.108208]