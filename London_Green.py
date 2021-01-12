import arcgis
from arcgis.gis import GIS
from arcgis.raster.functions import apply, clip, remap, colormap
from arcgis.geocoding import geocode
from datetime import datetime
import pandas as pd
from IPython.display import display
from IPython.display import Image
from IPython.display import HTML
import matplotlib.pyplot as plt
%matplotlib inline


gis = GIS(url='https://pythonapi.playground.esri.com/portal', username='arcgis_python', password='amazing_arcgis_123')

search_item = gis.content.search('title:Multispectral Landsat', 'Imagery Layer', outside_org=True)[0]
landsat = search_item.layers[0]


UK_items = gis.content.search('United Kingdom', item_type="Feature Layer", outside_org=True)[0]
UK_items
UK_boundaries = UK_items.layers[1]
UK_boundaries
london_area = geocode("London, GB", out_sr=landsat.properties.spatialReference)[0]
landsat.extent = london_area['extent']
london_area
london = UK_boundaries.query(where='OBJECTID=7')
london_geom = london.features[0].geometry
london_geom
london_geom['spatialReference'] = {'wkid':4326}
london.features[0].extent = london_area['extent']



selected = landsat.filter_by(where="(Category = 1) AND (cloudcover <=0.2)",
                             time=[datetime(2015, 1, 1), datetime(2019, 12, 31)],
                             geometry=arcgis.geometry.filters.intersects(london_area['extent']))
selected
df = selected.query(out_fields="AcquisitionDate, GroupName, CloudCover, DayOfYear",order_by_fields="AcquisitionDate").sdf
df['AcquisitionDate'] = pd.to_datetime(df['AcquisitionDate'], unit='ms')
df

london_image = landsat.filter_by('OBJECTID=2918532') # 2017-10-15
apply(london_image, 'Natural Color with DRA')


ndvi_colorized = apply(london_image, 'NDVI Raw')
ndvi_colorized


london_clip = clip(ndvi_colorized, london_geom)
london_clip.extent = london_area['extent']
london_clip

threshold_value = 0.45
london_masked = colormap(remap(london_clip,
                        input_ranges=[0.4,threshold_value,threshold_value, 1],output_values=[1, 2]),colormap=[[1, 124, 252, 0], [2, 0, 102, 0]], astype='u8')

Image(london_masked.export_image(bbox=london_area['extent'], size=[1500,600], f='image'))



pixx = (london_clip.extent['xmax'] - london_clip.extent['xmin']) / 1500
pixy = (london_clip.extent['ymax'] - london_clip.extent['ymin']) / 600

res = london_masked.compute_histograms(london_clip.extent,
                               pixel_size={'x':pixx, 'y':pixy})
numpix = 0
res
histogram = res['histograms'][0]['counts'][0:]
for i in histogram[1:]:
    numpix += i

sqmlondon_area = numpix * pixx * pixy # in sq. m
acres = 0.00024711 * sqmlondon_area   # in acres
HTML('<h3>Total Green cover in london is ~ <i>{}%</i> of the total \
     geographical london_area of london.</h3>'.format(int((acres/429444.442717)*100)))
london_area = ['Non Forest', 'Forest', 'Agriculture']

data = [60, 19, 20]

# Creating plot
fig = plt.figure(figsize =(10, 7))
plt.pie(data, labels = london_area)

# show plot
plt.show()
