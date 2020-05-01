"""
Split off some library functions for easier testing and code management.

Created on Mar 24, 2017

@author=bathomas @email=brian.a.thomas@nasa.gov
"""

from bs4 import BeautifulSoup, Comment
from datetime import timedelta
import requests
import logging
import json
import os
import re

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

# location of backing APOD service
BASE = 'https://apod.nasa.gov/apod/'


CACHE_FOLDER_HTML = "cache/html"
CACHE_FOLDER_JSON = "cache/json"

if not os.path.exists(CACHE_FOLDER_JSON):
    os.makedirs(CACHE_FOLDER_JSON)

if not os.path.exists(CACHE_FOLDER_HTML):
    os.makedirs(CACHE_FOLDER_HTML)

# JSON Caching

def cache_json(data, date):
    with open(f"{CACHE_FOLDER_JSON}/{date}.json", "w") as file:
        json.dump(data, file)

def cached_json_for(date):
    with open(f"{CACHE_FOLDER_JSON}/{date}.json") as file:
        data = json.load(file)
    return data

def cached_json_exists_for(date):
    return os.path.exists(f"{CACHE_FOLDER_JSON}/{date}.json")


# HTML Caching (internal use only)

def _cached_html_for(date):
    with open(f"{CACHE_FOLDER_HTML}/{_html_filename_for(date)}") as file:
        content = file.read()
    return content

def _cache_html(content, date):
    with open(f"{CACHE_FOLDER_HTML}/{_html_filename_for(date)}", "w") as file:
        file.write(content)

def _html_filename_for(date):
    date_str = date.strftime('%y%m%d')
    return f"ap{date_str}.html"


# function for getting video thumbnails
def _get_thumbs(data):
    if _youtube_video_id_from(data):
        return "https://img.youtube.com/vi/" + _youtube_video_id_from(data) + "/0.jpg"

    elif "vimeo" in data:
        # get ID from Vimeo URL
        vimeo_id_regex = re.compile("(?:/video/)(\d+)")
        vimeo_id = vimeo_id_regex.findall(data)[0]
        # make an API call to get thumbnail URL
        response = requests.get(f"https://vimeo.com/api/v2/video/{vimeo_id}.json")
        return response.json()[0]['thumbnail_large']


def _youtube_video_id_from(url):
    if not url:
        return None
    regex = "(?:http:|https:)*?\/\/(?:www\.|)(?:youtube\.com|m\.youtube\.com|youtu\.|youtube-nocookie\.com).*(?:v=|v%3D|v\/|(?:a|p)\/(?:a|u)\/\d.*\/|watch\?|vi(?:=|\/)|\/embed\/|oembed\?|be\/|e\/)([^&?%#\/\n]*)"
    video_id = re.compile(regex).findall(url)  # returns an array
    return ''.join(video_id)  # get id or empty string


def _query(url):
    query = requests.utils.urlparse(url).query
    return "?" + query if query else ""


def _get_apod_chars(dt):
    try:
        html_content = _cached_html_for(dt)
    except:
        apod_url = os.path.join(BASE, _html_filename_for(dt))
        LOG.debug('OPENING URL:' + apod_url)
        response = requests.get(apod_url)
        response.raise_for_status()
        html_content = response.text
        _cache_html(html_content, dt)

    soup = BeautifulSoup(html_content, 'html.parser')
    LOG.debug('getting the data url')
    data = None
    hd_data = None

    if soup.img:
        media_type = 'image'
        data = BASE + soup.img['src']

        LOG.debug('getting the link for hd_data')
        for link in soup.find_all('a', href=True):
            if link['href'] and link['href'].startswith('image'):
                hd_data = BASE + link['href']
                break
    else:
        media_type = 'video'
        if soup.iframe:
            data = soup.iframe['src']
        elif soup.object and _youtube_video_id_from(soup.object.embed["src"]):
            # old way of embedding videos
            url = soup.object.embed["src"]
            # generating new URL because the old url structure is not recognized by youtube anymore
            # and query params could contain start position
            data = "https://youtu.be/" + _youtube_video_id_from(url) + _query(url)

    if not data:
        # Ignore the entry if we can't get neither an image nor a video url (flash/unsupported video)
        raise ValueError("Neither image nor video is available for this date")

    props = {}

    props['explanation'] = _explanation(soup)
    props['title'] = _title(soup)
    props['media_type'] = media_type
    props['date'] = dt.isoformat()
    
    copyright_text = _copyright(soup)
    if copyright_text:
        props['copyright'] = copyright_text

    keywords = _keywords(soup)
    if keywords:
        props['keywords'] = keywords
    
    props['url'] = data

    if hd_data and hd_data != data:
        props['hdurl'] = hd_data

    if media_type == "video":
        props['thumbnail_url'] = _get_thumbs(data)

    return props


def _title(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image title.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time.
    """
    LOG.debug('getting the title')
    try:
        # Handler for later APOD entries
        center_selection = soup.find_all('center')[1]
        bold_selection = center_selection.find_all('b')[0]
        title = bold_selection.text.strip(' ')
        try:
            title = title.encode('latin1').decode('cp1252')
        except Exception as ex:
            LOG.error(str(ex))
        
        return title
    except Exception:
        # Handler for early APOD entries
        text = soup.title.text.split(' - ')[-1]
        title = text.strip()
        try:
            title = title.encode('latin1').decode('cp1252')
        except Exception as ex:
            LOG.error(str(ex))

        return title


def _copyright(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image copyright.  Highly idiosyncratic with adaptations for different
    HTML structures that appear over time.
    """
    LOG.debug('getting the copyright')
    try:
        # Handler for later APOD entries
        # There's no uniform handling of copyright (sigh). Well, we just have to
        # try every stinking text block we find...

        copyright_text = None
        use_next = False
        for element in soup.findAll('a', text=True):
            # LOG.debug("TEXT: "+element.text)

            if use_next:
                copyright_text = element.text.strip(' ')
                break

            if 'Copyright' in element.text:
                LOG.debug('Found Copyright text:' + str(element.text))
                use_next = True

        if not copyright_text:

            for element in soup.findAll(['b', 'a'], text=True):
                # search text for explicit match
                if 'Copyright' in element.text:
                    LOG.debug('Found Copyright text:' + str(element.text))
                    # pull the copyright from the link text which follows
                    sibling = element.next_sibling
                    stuff = ""
                    while sibling:
                        try:
                            stuff = stuff + sibling.text
                        except Exception:
                            pass
                        sibling = sibling.next_sibling

                    if stuff:
                        copyright_text = stuff.strip(' ')
        try:
            copyright_text = copyright_text.encode('latin1').decode('cp1252')
        except Exception as ex:
            LOG.error(str(ex))

        return copyright_text

    except Exception as ex:
        LOG.error(str(ex))
        raise ValueError('Unsupported schema for given date.')


def _keywords(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    content of the `keywords` meta.
    """
    LOG.debug('getting the keywords')
    raw_keywords = None

    try:
        # Handle later APOD entries
        meta = soup.find("meta", attrs={"name": "keywords"})
        raw_keywords = meta["content"]
    except Exception:
        # Handler for early APOD entries
        comments = soup.findAll(text=lambda text:isinstance(text, Comment))
        for comment in comments:
            comment = comment.lower()
            if "keywords:" not in comment: continue
            raw_keywords = comment.split("keywords:")[1]
            break

    try:
        # e.g.: "abc, bcd, ng1 sd..."
        content = raw_keywords.split(",")
        # remove leading/trailing spaces and convert everything to lowercase
        keywords = [word.strip().lower() for word in content]
        keywords = [word for word in keywords if word]  # remove empty strings
        return keywords
    except:
        return None


def _explanation(soup):
    """
    Accepts a BeautifulSoup object for the APOD HTML page and returns the
    APOD image explanation.  Highly idiosyncratic.
    """
    # Handler for later APOD entries
    LOG.debug('getting the explanation')
    s = soup.find_all('p')[2]

    footer = s.find('p')
    if footer:
        if "Explanation:" in footer.text:
            # old structure
            s = footer
        else:
            footer.decompose()

    s = s.text
    s = s.replace('\n', ' ')
    s = s.replace('Explanation: ', '')
    s = s.split('Tomorrow\'s picture')[0]
    s = s.split('For more information')[0]
    s = s.strip()
    
    # recursively clean double spaces
    while '  ' in s:
        s = s.replace('  ', ' ')
    
    if s == '':
        # Handler for earlier APOD entries
        texts = [x.strip() for x in soup.text.split('\n')]
        try:
            begin_idx = texts.index('Explanation:') + 1
        except ValueError as e:
            # Rare case where "Explanation:" is not on its own line
            explanation_line = [x for x in texts if "Explanation:" in x]
            if len(explanation_line) == 1:
                begin_idx = texts.index(explanation_line[0])
                texts[begin_idx] = texts[begin_idx][12:].strip()
            else:
                raise e

        idx = texts[begin_idx:].index('')
        s = ' '.join(texts[begin_idx:begin_idx + idx])

    try:
        s = s.encode('latin1').decode('cp1252')
    except Exception as ex:
        LOG.error(str(ex))

    return s


def parse_apod(dt, use_default_today_date=False):
    """
    Accepts a date in '%Y-%m-%d' format. Returns the URL of the APOD image
    of that day, noting that
    """

    LOG.debug('apod chars called date:' + str(dt))

    try:
        return _get_apod_chars(dt)

    except Exception as ex:

        # handle edge case where the service local time
        # miss-matches with 'todays date' of the underlying APOD
        # service (can happen because they are deployed in different
        # timezones). Use the fallback of prior day's date

        if use_default_today_date:
            # try to get the day before
            dt = dt - timedelta(days=1)
            return _get_apod_chars(dt)
        else:
            # pass exception up the call stack
            LOG.error(str(ex))
            raise Exception(ex)
