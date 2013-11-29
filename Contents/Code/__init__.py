DEBUG = False
VIDEOS_URL = "http://www.nbcsports.com/ajax-pane/get-pane/3373/61644?/video"
PLAYER_URL = "http://vplayer.nbcsports.com/p/BxmELC/nbcsportssite/select/"
THUMB_URL = "http://www.nbcsports.com/files/nbcsports/styles/video_thumbnail/public/media-theplatform/%s.jpg"
SMIL_URL = "http://link.theplatform.com/s/BxmELC/%s"
SMIL_NAMESPACE = {'a': 'http://www.w3.org/2005/SMIL21/Language'}

RE_VIDEO_HASH = Regex("media-theplatform/(.+?)\.jpg")

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'

LOGOS = {'boxing': True, 'college-football': True, 'f1': True, 'golf': True, 'mlb': True, 'mls': True,
         'nba': True, 'nhl': True, 'nfl': True, 'outdoors': True, 'premier-league': True, 'tennis': True}


####################################################################################################
def Start():

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)
    VideoClipObject.thumb = R(ICON)

    # Set the default cache time
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36"


####################################################################################################
@handler('/video/nbcsports', L('VideoTitle'))
def MainMenu():

    oc = ObjectContainer()

    # Iterate over all of the available categories and display them to the user.
    page = HTML.ElementFromURL(VIDEOS_URL)
    categories = page.xpath('//div[@class = "video-categories"]//li/a')
    log("Categories: %d" % len(categories))

    for category in categories:
        cat_id = category.get('href').replace('/video/', '')
        if cat_id.isdigit():
            name = category.text
            title = CleanName(name)
            logo = name.lower().replace(' ', '-')
            logo = R(logo + '.jpg')
            # this doesn't work and 2 hours of slinging crap leaves me no closer to knowing what does
            if not logo:
                logo = R(ICON)

            log("Category: %s, Name: %s, Logo: %s" % (cat_id, name, logo))

            oc.add(DirectoryObject(
                key=Callback(ChannelVideoCategory,
                id=cat_id,
                name=title),
                title=title,
                thumb=logo))

    return oc


####################################################################################################
@route('/video/nbcsports/{id}')
def ChannelVideoCategory(id, name):

    oc = ObjectContainer(view_group="InfoList")

    page = HTML.ElementFromURL(VIDEOS_URL)

    thumbs = page.xpath('//div[@id = "channel-' + id + '"]//img/@src')
    titles = page.xpath('//div[@id = "channel-' + id + '"]//div[contains(@class, "views-field-title")]//a/text()')

    num_thumbs = len(thumbs)
    num_titles = len(titles)
    log("Thumbs: %d, Titles: %d" % (num_thumbs, num_titles))

    if num_thumbs < 1 or num_titles < 1 or num_thumbs != num_titles:
        return ObjectContainer(header=name, message="D'oh! Me Fail Videos? Unpossible!.")

    for index in range(num_thumbs):
        name = titles[index]
        thumb = thumbs[index]
        video_hash = RE_VIDEO_HASH.search(thumb).group(1)
        if not video_hash:
            continue

        log("Hash: %s, Title: %s" % (video_hash, name))

        oc.add(CreateVideoObject(video_hash=video_hash))

    if len(oc) < 1:
        return ObjectContainer(header=name, message="There are no titles available for the requested item.")

    return oc


####################################################################################################
# https://forums.plexapp.com/index.php/topic/78852-can-i-directly-play-an-url-without-having-a-service-file/
####################################################################################################
def CreateVideoObject(video_hash, include_container=False):

    video_details = GetVideoDetails(video_hash)

    video_object = VideoClipObject(
        key=Callback(CreateVideoObject,
                        video_hash=video_hash,
                        include_container=True),
        rating_key=video_details['url'],
        title=video_details['title'],
        summary=video_details['summary'],
        tags=video_details['tags'],
        duration=video_details['duration'],
        thumb=video_details['thumb'],
        items=[
                MediaObject(
                        parts = [
                                PartObject(key=video_details['src'], duration=video_details['duration'])
                        ],
                        container=Container.MP4,
                        audio_codec=AudioCodec.AAC,
                        audio_channels=2
                )
        ]
    )

    if include_container:
            return ObjectContainer(objects=[video_object])
    else:
            return video_object


####################################################################################################
def GetVideoDetails(video_hash):

    log("GetVideoDetails(" + video_hash + ")")

    if Data.Exists(video_hash):
        log("Details for %s from cache" % video_hash)
        details = Data.LoadObject(video_hash)
    else:
        smil = XML.ElementFromURL(SMIL_URL % video_hash)

        video_details = smil.xpath('//a:video', namespaces=SMIL_NAMESPACE)[0]
        summary = video_details.get('abstract')
        duration = int(video_details.get('dur').strip('ms'))
        src = video_details.get('src')
        title = video_details.get('title')
        try:
            tags = [tag.strip() for tag in video_details.get('keywords').split(',')]
        except:
            tags = []

        thumb = THUMB_URL % video_hash
        url = PLAYER_URL + video_hash

        details = {'duration': duration, 'src': src, 'summary': summary, 'tags': tags, 'thumb': thumb, 'title': title,
                   'url': url}

        Data.SaveObject(video_hash, details)

    log(str(details))

    return details


####################################################################################################
def CleanName(name):
    # Function cleans up HTML ascii stuff
    remove = [('&amp;', '&'), ('&quot;', '"'), ('&#233;', 'e'), ('&#8212;', ' - '), ('&#39;', '\''), ('&#46;', '.'),
              ('&#58;', ':'), ('&#8482;', '')]
    for trash, crap in remove:
        name = name.replace(trash, crap)

    return name.strip()

def log(str):
    if DEBUG:
        Log(str)