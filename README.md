# Astronomy Picture of the Day (APOD) microservice

A microservice written in Python with the [Flask micro framework](http://flask.pocoo.org).

# Table of contents
1. [Getting Started](#getting_started)
    1. [Standard environment](#standard_env)
    2. [`virtualenv` environment](#virtualenv)
    3. [`conda` environment](#conda)
2. [Docs](#docs)
3. [Feedback](#feedback)
4. [Author](#author)

&nbsp;
## Getting started <a name="getting_started"></a>

### Standard environment <a name="standard_env"></a>

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Install dependencies into the project's `lib`
```bash
pip install -r requirements.txt -t lib
```
4. Add `lib` to your PYTHONPATH and run the server
```bash
PYTHONPATH=./lib python apod/service.py
```
&nbsp;
### `virtualenv` environment <a name="virtualenv"></a>

1. Clone the rep
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Create a new virtual environment `env` in the directory
```bash
python -m virtualenv env
```
4. Activate the new environment
```bash
source env/bin/activate
```
5. Install dependencies in new environment
```bash
pip install -r requirements.txt
```
6. Run the server locally
```bash
python apod/service.py
```
&nbsp;
### `conda` environment <a name="conda"></a>

1. Clone the repo
```bash
git clone https://github.com/nasa/apod-api
```
2. `cd` into the new directory
```bash
cd apod-api
```
3. Create a new virtual environment `env` in the directory
```bash
conda create --prefix ./env python=2.7
```
4. Activate the new environment
```bash
conda activate ./env
```
5. Install dependencies in new environment
```bash
pip install -r requirements.txt
```
6. Run the server locally
```bash
python apod/service.py
```
&nbsp;
## Docs <a name="docs"></a>

### Endpoint: `/<version>/apod`

There is only one endpoint in this service which takes 2 optional fields
as parameters to a http GET request. A JSON dictionary is returned nominally. 

**Fields**

- `date` A string in YYYY-MM-DD format indicating the date of the APOD image (example: 2014-11-03).  Defaults to today's date.  Must be after 1995-06-16, the first day an APOD picture was posted.  There are no images for tomorrow available through this API.
- `start_date` A string in YYYY-MM-DD format indicating the start of a date range. All images in the range from `start_date` to `end_date` will be returned in a JSON array. Cannot be used with `date`.
- `end_date` A string in YYYY-MM-DD format indicating that end of a date range. If `start_date` is specified without an `end_date` then `end_date` defaults to the current date.

**Returned fields**

- `resource` A dictionary describing the `image_set` or `planet` that the response illustrates, completely determined by the structured endpoint.
- `title` The title of the image.
- `date` Date of image. Included in response because of default values.
- `url` The URL of the APOD image or video of the day.
- `hdurl` The URL for any high-resolution image for that day (if available).
- `media_type` The type of media (data) returned. May either be 'image' or 'video' depending on content.
- `explanation` The supplied text explanation of the image.
- `thumbnail_url` The URL of thumbnail of the video. 

**Example**

```bash
localhost:5000/v1/apod?date=2014-10-01
```
<details><summary>See Return Object</summary>
<p>

```jsoniq
{
    resource: {
        image_set: "apod"
    },
    date: "2013-10-01", 
    title: "Filaments of the Vela Supernova Remnant",
    url: "http://apod.nasa.gov/apod/image/1310/velafilaments_jadescope_960.jpg",
    explanation: "The explosion is over but the consequences continue. About eleven
    thousand years ago a star in the constellation of Vela could be seen to explode,
    creating a strange point of light briefly visible to humans living near the 
    beginning of recorded history. The outer layers of the star crashed into the 
    interstellar medium, driving a shock wave that is still visible today. A roughly 
    spherical, expanding shock wave is visible in X-rays. The above image captures some
    of that filamentary and gigantic shock in visible light. As gas flies away from the
    detonated star, it decays and reacts with the interstellar medium, producing light
    in many different colors and energy bands. Remaining at the center of the Vela
    Supernova Remnant is a pulsar, a star as dense as nuclear matter that rotates
    completely around more than ten times in a single second."
}
```

</p>
</details>


```bash
https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY&start_date=2017-07-08&end_date=2017-07-10 
```

<details><summary>See Return Object</summary>
<p>

```jsoniq
[
  {
    "copyright": "T. Rector", 
    "date": "2017-07-08", 
    "explanation": "Similar in size to large, bright spiral galaxies in our neighborhood, IC 342 is a mere 10 million light-years distant in the long-necked, northern constellation Camelopardalis. A sprawling island universe, IC 342 would otherwise be a prominent galaxy in our night sky, but it is hidden from clear view and only glimpsed through the veil of stars, gas and dust clouds along the plane of our own Milky Way galaxy. Even though IC 342's light is dimmed by intervening cosmic clouds, this sharp telescopic image traces the galaxy's own obscuring dust, blue star clusters, and glowing pink star forming regions along spiral arms that wind far from the galaxy's core. IC 342 may have undergone a recent burst of star formation activity and is close enough to have gravitationally influenced the evolution of the local group of galaxies and the Milky Way.", 
    "hdurl": "https://apod.nasa.gov/apod/image/1707/ic342_rector2048.jpg", 
    "media_type": "image", 
    "service_version": "v1", 
    "title": "Hidden Galaxy IC 342", 
    "url": "https://apod.nasa.gov/apod/image/1707/ic342_rector1024s.jpg"
  }, 
  {
    "date": "2017-07-09", 
    "explanation": "Can you find your favorite country or city?  Surprisingly, on this world-wide nightscape, city lights make this task quite possible.  Human-made lights highlight particularly developed or populated areas of the Earth's surface, including the seaboards of Europe, the eastern United States, and Japan.  Many large cities are located near rivers or oceans so that they can exchange goods cheaply by boat.  Particularly dark areas include the central parts of South America, Africa, Asia, and Australia.  The featured composite was created from images that were collected during cloud-free periods in April and October 2012 by the Suomi-NPP satellite, from a polar orbit about 824 kilometers above the surface, using its Visible Infrared Imaging Radiometer Suite (VIIRS).", 
    "hdurl": "https://apod.nasa.gov/apod/image/1707/EarthAtNight_SuomiNPP_3600.jpg", 
    "media_type": "image", 
    "service_version": "v1", 
    "title": "Earth at Night", 
    "url": "https://apod.nasa.gov/apod/image/1707/EarthAtNight_SuomiNPP_1080.jpg"
  }, 
  {
    "date": "2017-07-10", 
    "explanation": "What's happening around the center of this spiral galaxy? Seen in total, NGC 1512 appears to be a barred spiral galaxy -- a type of spiral that has a straight bar of stars across its center.  This bar crosses an outer ring, though, a ring not seen as it surrounds the pictured region. Featured in this Hubble Space Telescope image is an inner ring -- one that itself surrounds the nucleus of the spiral.  The two rings are connected not only by a bar of bright stars but by dark lanes of dust. Inside of this inner ring, dust continues to spiral right into the very center -- possibly the location of a large black hole. The rings are bright with newly formed stars which may have been triggered by the collision of NGC 1512 with its galactic neighbor, NGC 1510.", 
    "hdurl": "https://apod.nasa.gov/apod/image/1707/NGC1512_Schmidt_1342.jpg", 
    "media_type": "image", 
    "service_version": "v1", 
    "title": "Spiral Galaxy NGC 1512: The Nuclear Ring", 
    "url": "https://apod.nasa.gov/apod/image/1707/NGC1512_Schmidt_960.jpg"
  }
]
```


</p>
</details>


## Feedback <a name="feedback"></a>
Star this repo if you found it useful. Use the github issue tracker to give
feedback on this repo.

## Author <a name="author"></a>
Brian Thomas (based on code by Dan Hammer) 

