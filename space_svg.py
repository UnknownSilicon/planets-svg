import requests
import re
import math
import svgwrite
import numpy

AU = 1.495978707E11

YEAR = "2020"
DAY = "049"
MULT_FACTOR = 24  # This is used to scale the entire thing. Should be changed to match the material
SIZE = 1000
CENTER = (SIZE/2, SIZE/2)


request_data = {"activity": "ftp",
                "object": "01",
                "coordinate": "1",
                "start_year": YEAR,
                "start_day": DAY,
                "stop_year": YEAR,
                "stop_day": DAY,
                "resolution": "001",
                "equinox": "2",
                "object2": ""}

objects_search = ["29", "15", "04", "42", "30", "31", "44", "45", "38"]

'''
# Perihelions and Aphelions are in 1E6 KM and inclinations are in degrees
perihelions = [46, 107.5, 147.1, 206.6, 740.5, 1352.6, 2741.3, 4444.5, 4436.8]
aphelions = [69.8, 108.9, 152.1, 249.2, 816.6, 1514.5, 3003.6, 4545.7, 7375.9]
inclinations = [7, 3.4, 0, 1.9, 1.3, 2.5, 0.8, 1.8, 17.2]

# Convert perihelions and aphelions to AU. Don't run this every time!
for i in range(0, len(perihelions)):
    perihelions[i] = perihelions[i] * 1E9 / AU
    aphelions[i] = aphelions[i] * 1E9 / AU

print(*perihelions, sep=", ")
print(*aphelions, sep=", ")
'''


# Perihelions and Apehelions in AU
perihelions = [0.3074910076243485, 0.7185931156438579, 0.9833027656856883, 1.3810356994606607, 4.9499367640397836,
               9.0415725415803, 18.32445867827449, 29.709647464922107, 29.658176144080638]
aphelions = [0.4665841811343375, 0.7279515376150337, 1.0167257012970305, 1.6657991108692967, 5.458633844044413,
             10.12380719667556, 20.077825880445502, 30.386127681695672, 30.0]
inclinations = [7, 3.4, 0, 5.1, 1.9, 1.3, 2.5, 0.8, 17.2]
peri_longs = [77.45645, 131.53298, 102.94719, 336.04084, 14.75385, 92.43194, 170.96424, 44.97135, 224.06676]
scales = [1.25, 2, 2.7, 2.45, 1.1, .7, .4, .3, .36]

# DISTANCE, LAT, LONG
objects_data = []

# perihelions = list(map(lambda peri, theta: peri*math.cos(theta), perihelions, inclinations))
# aphelions = list(map(lambda aphe, theta: aphe*math.cos(theta), aphelions, inclinations))

print("Started...")

for x in objects_search:
    request_data["object"] = x
    r = requests.post("https://omniweb.gsfc.nasa.gov/cgi/models/helios1.cgi", data=request_data)
    data_page = r.text
    reg = re.search('http.+.lst"', data_page)
    data_url = reg.group(0)[0:-1]
    data_url = data_url.replace(":/", "://")

    d = requests.get(data_url)

    data = d.text
    data = data.split("\n")

    split_data = []

    for d in data[1:]:
        split_data.append(re.split("\\s+", d)[2:])

    # print(split_data)
    objects_data.append(split_data)

print("\n")

print(objects_data)

# Convert to x, y, z
converted_data = []

index = 0

for p in objects_data:
    planet = []
    for d in p[:-1]:
        r = float(d[0])
        b = float(d[1])
        l = float(d[2])

        # Convert, scale, and align points

        x = r * math.cos(b) * math.cos(l) * MULT_FACTOR * scales[index]
        y = r * math.cos(b) * math.sin(l) * MULT_FACTOR * scales[index]
        z = r * math.sin(b) * MULT_FACTOR * scales[index]

        day = [x, y, z]
        print(day)
        planet.append(day)
    print("\n")
    converted_data.append(planet)
    index += 1
print(converted_data)

# Now, get the closest points on the ellipses to each planet from the NASA data
# https://www.desmos.com/calculator/gw99rlkvlm
# ~~The hard part is scaling it right so the planets are actually roughly near their respective orbits,
# otherwise funky things happen~~. Looks like this is actually fine

iters = numpy.linspace(0, numpy.pi, 800)  # Change 314 to something higher to increase accuracy

aligned_planets = []

for pi in range(0, len(converted_data)):
    p = converted_data[pi][0]
    k = p[0]
    j = p[1]

    b = perihelions[pi]*MULT_FACTOR*scales[pi]
    a = aphelions[pi]*MULT_FACTOR*scales[pi]

    min_dist = math.inf
    x = 0
    y = 0

    for i in iters:
        q = a*b/(math.sqrt(math.pow(b, 2) + math.pow(a, 2) * math.pow(math.tan(i), 2)))
        w = -q
        t = q * math.tan(i)
        u = w * math.tan(i)

        d1 = math.sqrt(math.pow(q-j, 2) + math.pow(t-k, 2))
        d2 = math.sqrt(math.pow(w-j, 2) + math.pow(u-k, 2))

        if d1 < min_dist:
            min_dist = d1
            x = q
            y = t

        if d2 < min_dist:
            min_dist = d2
            x = w
            y = u
    aligned_planets.append((x + CENTER[0], y + CENTER[1]))


dwg = svgwrite.Drawing('test.svg', profile="full")

dwg.add(dwg.circle(center=CENTER, r=4.498, stroke=svgwrite.rgb(255, 0, 0, 'RGB'), fill_opacity="1", stroke_width=1))

for i in range(0, len(aphelions)):
    dwg.add(dwg.ellipse(center=CENTER, r=(aphelions[i]*MULT_FACTOR*scales[i],
                                          perihelions[i]*MULT_FACTOR*scales[i]),
                        transform="rotate("+str(peri_longs[i])+"," + str(CENTER[0]) + "," + str(CENTER[1]) + ")",
                        fill_opacity="0", stroke=svgwrite.rgb(0, 0, 0, 'RGB'), stroke_width=2))
    dwg.add(dwg.circle(center=aligned_planets[i], r=2.75, stroke=svgwrite.rgb(255, 0, 0, 'RGB'),
                       transform="rotate("+str(peri_longs[i])+"," + str(CENTER[0]) + "," + str(CENTER[1]) + ")",
                       fill_opacity="1", stroke_width=1))

dwg.add(dwg.circle(center=CENTER, r=(aphelions[-1]*MULT_FACTOR*scales[-1]*1.2), fill_opacity="0",
                   stroke=svgwrite.rgb(255, 0, 0, 'RGB'), stroke_width=1))

dwg.save()
