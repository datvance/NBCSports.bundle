DEBUG = True
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
    log("Categoreies: %d" % len(categories))

    for category in categories:
        cat_id = category.get('href').replace('/video/', '')
        if cat_id.isdigit():
            name = category.text
            logo = name.lower().replace(' ', '-')

            logo = R(logo + '.jpg')

            if logo is None:
                logo = R(ICON)

            log("Category: %s, Name: %s, Logo: %s" % (cat_id, name, logo))

            oc.add(DirectoryObject(
                key=Callback(ChannelVideoCategory,
                id=cat_id,
                name=CleanName(name)),
                title=name,
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

        url = PLAYER_URL + video_hash

        # Depending on parameters to SMIL_URL, could be different format, but we'll go with this
        smil = XML.ElementFromURL(SMIL_URL % video_hash)

        video_details = smil.xpath('//a:video', namespaces=SMIL_NAMESPACE)[0]
        #mp4_url = video_details.get('src')
        summary = video_details.get('abstract')
        duration = int(video_details.get('dur').strip('ms'))

        try:
            tags = [tag.strip() for tag in video_details.get('keywords').split(',')]
        except:
            tags = []

        oc.add(CreateVideoObject(
            url=url,
            title=CleanName(name),
            summary=summary,
            thumb=thumb,
            duration=duration,
            tags=tags))

    # It's possible that there is actually no vidoes are available for the ipad. Unfortunately, they
    # still provide us with empty containers...
    if len(oc) < 1:
        return ObjectContainer(header=name, message="There are no titles available for the requested item.")

    return oc


def CreateVideoObject(url, title, summary, thumb, duration, tags, include_container=False):

    video_hash = url.split('/')[-1]
    smil = XML.ElementFromURL(SMIL_URL % video_hash)

    video_details = smil.xpath('//a:video', namespaces=SMIL_NAMESPACE)[0]
    mp4 = video_details.get('src')
    log("mp4: " + mp4)

    video_object = VideoClipObject(
        key=Callback(CreateVideoObject,
                        url=url,
                        title=title,
                        summary=summary,
                        thumb=thumb,
                        duration=duration,
                        tags=tags,
                        include_container=True),
        rating_key=url,
        title=title,
        summary=summary,
        tags=tags,
        duration=duration,
        thumb=thumb,
        items=[
                MediaObject(
                        parts = [
                                PartObject(key=mp4, duration=duration)
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