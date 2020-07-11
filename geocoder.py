#   This Script gets a CSV file as input with the next format:
#       |   Location    |   GeoLocation         |
#       |   Name        |   longitude, latitude   |
#   It returns a CSV file with the GeoLocation field filled out, when possible
import herepy
import json
import csv

geocoderApi = herepy.GeocoderApi('YOUR_API_KEY')

r = csv.reader(open('locationsFile.csv', 'r', encoding='utf-8',newline=''), delimiter='\t')
lines = list(r)

#Location   ->  Column 0
#Geolocation    ->  Column 1
count = 0
for i in range(lines - 1):
    if i == 0:
        continue
    location = lines[i][0]
    geoLocation = lines[i][1]
    #print("Location", location)
    #print("GeoLocation", geoLocation)
    if i%5000 == 0:
        print(i)
    #If there is already geolocation, get to next entry
    if geoLocation != 'None' and geoLocation != '':
        print("coordenadas", geoLocation)
        continue
    #If there is no location to translate into coordinates, get to next entry
    elif location == 'None' or location == '':
        continue
    # At this point we need to translate the location to coordinates
    response = geocoderApi.free_form(location)
    jsonObject = json.loads(str(response))
    # If the location can't be recognized, the returned element is empty, get to next entry
    if len(jsonObject["items"]) == 0:
        continue
    else:
        # Get the longitude and latitude and write it to the original
        longitud =  jsonObject["items"][0]["position"]["lng"]
        latitud = jsonObject["items"][0]["position"]["lat"]
        geoLocation = '' + str(longitud) + ', ' + str(latitud)
        lines[i][1] = geoLocation
        count = count + 1
        #print("GeoLocation", geoLocation)
print("Translated", count)

writer = csv.writer(open('outputFile.csv', 'w', encoding="utf-8"), delimiter='\t')
writer.writerows(lines)
