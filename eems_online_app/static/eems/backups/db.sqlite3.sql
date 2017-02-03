BEGIN TRANSACTION;
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
CREATE TABLE "EEMS_ONLINE_MODELS" (
	`ID`	TEXT NOT NULL UNIQUE,
	`NAME`	TEXT,
	`EXTENT`	TEXT,
	`OWNER`	TEXT,
	`SHORT_DESCRIPTION`	TEXT,
	`LONG_DESCRIPTION`	TEXT,
	`AUTHOR`	TEXT,
	`CREATION_DATE`	TEXT,
	PRIMARY KEY(`ID`)
);
INSERT INTO `EEMS_ONLINE_MODELS` (ID,NAME,EXTENT,OWNER,SHORT_DESCRIPTION,LONG_DESCRIPTION,AUTHOR,CREATION_DATE) VALUES ('1','Site Sensitivity','[[32.534715526793306, -124.40416822955052], [42.01249803975221, -114.12309789053886]]','CBI','The Site Sensitivity Model evaluates the study area for factors that make the landscape sensitive to climate change. These factors fall into two main branches: soil sensitivity and water retention potential. As a final step, we defined barren areas as having the lowest possible sensitivity since many of these areas will not be further degraded by climate change.','                The Site Sensitivity Model evaluates the study area for factors that make the landscape sensitive to climate change. These factors fall into two main branches of the model: soil sensitivity and water retention potential. As a final step in the model, we defined barren areas as having the lowest possible sensitivity since many of these areas will not be further degraded by climate change.
                <p>
                <a href="https://databasin.org/maps/new#datasets=d1aba81719dc465594ed9a8d64e6b2a7&visibleLayers=6" target="_blank">View or Download this dataset on Data Basin</a>
                <p>
                <b>Soil Data for Soil Sensitivity Calculation</b>
                <p>
                    Soil data for this analysis were obtained from the conterminous United States Multi-Layer Soil Characteristics data (Miller & White 1998) and the STATSGO soil database (Soil Survey Staff 2015). All variables used are listed in Table 3.
		<p>


                <div class="tableDescriptions">Table 3 Soil variables used in the EEMS model, their acronym, the database, and URL where the data reside.</div>

                <p>
                <table class="modelDescriptionTable">
                 <tr><th class="tinyHeader">Variable</th class="tinyHeader"><th class="tinyHeader">Acronym</th class="tinyHeader"><th class="tinyHeader">Database</th class="tinyHeader"><th class="tinyHeader">URL</th class="tinyHeader"></tr>
                 <tr><td class="tg-yw4l">Available Water Capacity</td class="tg-yw4l"><td class="tg-yw4l">AWC</td class="tg-yw4l"><td class="tg-yw4l">CONUS-SOIL</td class="tg-yw4l"><td class="tg-yw4l">http://www.soilinfo.psu.edu/index.cgi?soil_data&conus&data_cov</td class="tg-yw4l"></tr>
                 <tr><td class="tg-yw4l">K-Factor</td class="tg-yw4l"><td class="tg-yw4l">Kffact</td class="tg-yw4l"><td class="tg-yw4l">CONUS-SOIL</td class="tg-yw4l"><td class="tg-yw4l">http://www.soilinfo.psu.edu/index.cgi?soil_data&conus&data_cov</td class="tg-yw4l"></tr>
                 <tr><td class="tg-yw4l">pH</td class="tg-yw4l"><td class="tg-yw4l">pH</td class="tg-yw4l"><td class="tg-yw4l">CONUS-SOIL</td class="tg-yw4l"><td class="tg-yw4l">http://www.soilinfo.psu.edu/index.cgi?soil_data&conus&data_cov</td class="tg-yw4l"></tr>
                 <tr><td class="tg-yw4l">Depth to Bedrock</td class="tg-yw4l"><td class="tg-yw4l">RD</td class="tg-yw4l"><td class="tg-yw4l">CONUS-SOIL</td class="tg-yw4l"><td class="tg-yw4l">http://www.soilinfo.psu.edu/index.cgi?soil_data&conus&data_cov</td class="tg-yw4l"></tr>
                 <tr><td class="tg-yw4l">Salinity</td class="tg-yw4l"><td class="tg-yw4l">SAL</td class="tg-yw4l"><td class="tg-yw4l">STATSGO</td class="tg-yw4l"><td class="tg-yw4l">https://gdg.sc.egov.usda.gov/</td class="tg-yw4l"></tr>
                 <tr><td class="tg-yw4l">Wind Erodibility Index</td class="tg-yw4l"><td class="tg-yw4l">WEG</td class="tg-yw4l"><td class="tg-yw4l">STATSGO</td class="tg-yw4l"><td class="tg-yw4l">https://gdg.sc.egov.usda.gov/</td class="tg-yw4l"></tr>
                </table>
                <p>
                    <b>Processing of Soil Data</b>
                <p>
                    All soil variables were downloaded for the conterminous United States and processed in ESRI ArcInfo workstation (ESRI 2014). Polygon data were converted to a raster dataset with a cell size of 0.0083333333 decimal degrees. The data were then clipped to the state of California boundaries and exported in NetCDF format.
                <p>
                    <b>Calculation of Water Erodibility Index</b>
                <p>
                    The index of susceptibility to water erosion (LSKf) was calculated from the Universal Soil Loss Equation (Wischmeier & Smith 1978) which is given as:
                <p>
                    A = R * K * L * S * C * P &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp (3)
                <p>
                    where A is predicted average annual soil loss, R is measured rainfall erosivity, K is soil erodibility, L is slope length factor, S is steepness of the slope, and C and P represent the respective erosion reduction effects of management (C) and erosion control practices (P).
                <p>
                    Combining L and S represents the impact of topography on erosion and is calculated as (Hickey 2000):

                <p>
                   LS= (As/22.13)^0.4∙ (sinθ/0.09)^1.4∙1.4 
                <p>
where As is the unit of contributing area (m), θ is the slope in radians. We then combined the K factor with LS to estimate the potential susceptibility of a soil to water erosion. 
                <p>
','Tim Sheehan','01/20/2016');
INSERT INTO `EEMS_ONLINE_MODELS` (ID,NAME,EXTENT,OWNER,SHORT_DESCRIPTION,LONG_DESCRIPTION,AUTHOR,CREATION_DATE) VALUES ('2','Climate Exposure (2016-2045)','[[32.534715526793306, -124.40416822955052], [42.01249803975221, -114.12309789053886]]','CBI','Climate exposure is based on the difference between the projected future climate (2016-2045) compared to the variability in climate over a reference historical period of 1971-2000. The higher the climate exposure, the greater the difference the projected climate is from what the area experienced in the past. ','                The Climate Exposure Model is based on aridity and climate. Climate factors include maximum temperature, minimum temperature, and precipitation on a seasonal basis and an annual basis. Change was calculated for two future time periods, 2016-2045 and 2046-2075, compared to the historical period, 1971-2000. Projections for three climate futures were used along with the ensemble mean values from those models. Temperature and precipitation differences were normalized using the standard deviation over the historical period via the following formula:
                <br>
                <div style="width:100%; text-align:center; margin-left:auto; margin-right:auto"> <img style="width:150px;" src="/static/img/ce_equation.png"></div>
                <br>
                <br>

                where d is the difference, x<sub>f</sub> is the mean of the variable in the future period, x<sub>h</sub> is the mean of the variable in the historical period, and Ïƒ<sub>x<sub>h</sub></sub> is standard deviation of the variable in the historical period. Change in aridity was calculated as the percent change from the historical period. Projected future change is very high for temperatures and aridity. In order to capture both the differences across the region as well as the severity of change, nonlinear conversions were used to convert input data into fuzzy space:

                <img src="/static/img/climate_chart1.png"><img src="/static/img/climate_chart2.png">

                <div class="footnote" style="margin-left:40px">Original value to fuzzy value conversion curves for a) climate variables and b) aridity.</div>
                <br>
                <p>
                <a href="https://databasin.org/maps/new#datasets=15e8a1a8ad604c2681590dc68d4ec1cf&visibleLayers=1" target="_blank">View or Download this dataset on Data Basin (2016-2045)</a> <br>
                <a href="https://databasin.org/maps/new#datasets=15e8a1a8ad604c2681590dc68d4ec1cf&visibleLayers=1" target="_blank">View or Download this dataset on Data Basin (2046-2075)</a>
','Tim Sheehan','01/20/2016');
INSERT INTO `EEMS_ONLINE_MODELS` (ID,NAME,EXTENT,OWNER,SHORT_DESCRIPTION,LONG_DESCRIPTION,AUTHOR,CREATION_DATE) VALUES ('4','Potential Impact (2016-2045)','[[32.534715526793306, -124.40416822955052], [42.01249803975221, -114.12309789053886]]','CBI','EEMS model of potential climate impacts (2016-2045) generated using data from STATSGO soils data and climate model results. Results from the Site Sensitivity and Climate Exposure models contribute equally to the results of the Potential Climate Impact model. As with the Climate Exposure Model, the Climate Impacts Model was run for each climate future.','                 EEMS model of potential climate impacts generated using data from STATSGO soils data and climate model results. Results from the Site Sensitivity and Climate Exposure models contribute equally to the results of the Potential Climate Impact model. As with the Climate Exposure Model, the Climate Impacts Model was run for each climate future (full results available on Data Basin). The results from the run with ensemble climate data are used in the Climate Console.
                <p>
                <a href="https://databasin.org/maps/new#datasets=5f66253161de4550b720da7b16bbd46b&visibleLayers=0" target="_blank">View or Download this dataset on Data Basin (2016-2045)</a> <br>
                <a href="https://databasin.org/maps/new#datasets=6be381850f2f427ea54ffd8c642def7e&visibleLayers=0" target="_blank">View or Download this dataset on Data Basin (2046-2075)</a>
                <p>

','Tim Sheehan','01/20/2016');
INSERT INTO `EEMS_ONLINE_MODELS` (ID,NAME,EXTENT,OWNER,SHORT_DESCRIPTION,LONG_DESCRIPTION,AUTHOR,CREATION_DATE) VALUES ('3','Climate Exposure (2046-2075)','[[32.534715526793306, -124.40416822955052], [42.01249803975221, -114.12309789053886]]','CBI','Climate exposure is based on the difference between the projected future climate (2016-2045) compared to the variability in climate over a reference historical period of 1971-2000. The higher the climate exposure, the greater the difference the projected climate is from what the area experienced in the past. ','                The Climate Exposure Model is based on aridity and climate. Climate factors include maximum temperature, minimum temperature, and precipitation on a seasonal basis and an annual basis. Change was calculated for two future time periods, 2016-2045 and 2046-2075, compared to the historical period, 1971-2000. Projections for three climate futures were used along with the ensemble mean values from those models. Temperature and precipitation differences were normalized using the standard deviation over the historical period via the following formula:
                <br>
                <div style="width:100%; text-align:center; margin-left:auto; margin-right:auto"> <img style="width:150px;" src="/static/img/ce_equation.png"></div>
                <br>
                <br>

                where d is the difference, x<sub>f</sub> is the mean of the variable in the future period, x<sub>h</sub> is the mean of the variable in the historical period, and Ïƒ<sub>x<sub>h</sub></sub> is standard deviation of the variable in the historical period. Change in aridity was calculated as the percent change from the historical period. Projected future change is very high for temperatures and aridity. In order to capture both the differences across the region as well as the severity of change, nonlinear conversions were used to convert input data into fuzzy space:

                <img src="/static/img/climate_chart1.png"><img src="/static/img/climate_chart2.png">

                <div class="footnote" style="margin-left:40px">Original value to fuzzy value conversion curves for a) climate variables and b) aridity.</div>
                <br>
                <p>
                <a href="https://databasin.org/maps/new#datasets=15e8a1a8ad604c2681590dc68d4ec1cf&visibleLayers=1" target="_blank">View or Download this dataset on Data Basin (2016-2045)</a> <br>
                <a href="https://databasin.org/maps/new#datasets=15e8a1a8ad604c2681590dc68d4ec1cf&visibleLayers=1" target="_blank">View or Download this dataset on Data Basin (2046-2075)</a>
','Tim Sheehan','01/20/2016');
INSERT INTO `EEMS_ONLINE_MODELS` (ID,NAME,EXTENT,OWNER,SHORT_DESCRIPTION,LONG_DESCRIPTION,AUTHOR,CREATION_DATE) VALUES ('5','Potential Impact (2046-2075)','[[32.534715526793306, -124.40416822955052], [42.01249803975221, -114.12309789053886]]','CBI','EEMS model of potential climate impacts (2016-2045) generated using data from STATSGO soils data and climate model results. Results from the Site Sensitivity and Climate Exposure models contribute equally to the results of the Potential Climate Impact model. As with the Climate Exposure Model, the Climate Impacts Model was run for each climate future.','                 EEMS model of potential climate impacts generated using data from STATSGO soils data and climate model results. Results from the Site Sensitivity and Climate Exposure models contribute equally to the results of the Potential Climate Impact model. As with the Climate Exposure Model, the Climate Impacts Model was run for each climate future (full results available on Data Basin). The results from the run with ensemble climate data are used in the Climate Console.
                <p>
                <a href="https://databasin.org/maps/new#datasets=5f66253161de4550b720da7b16bbd46b&visibleLayers=0" target="_blank">View or Download this dataset on Data Basin (2016-2045)</a> <br>
                <a href="https://databasin.org/maps/new#datasets=6be381850f2f427ea54ffd8c642def7e&visibleLayers=0" target="_blank">View or Download this dataset on Data Basin (2046-2075)</a>
                <p>

','Tim Sheehan','01/20/2016');
COMMIT;
