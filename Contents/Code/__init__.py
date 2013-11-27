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

DEFAULT_LOGO = 'simpsons.jpg'
LOGOS = {'college-football': True, 'f1': True, 'mlb': True, 'mls': True, 'nba': True, 'nhl': True, 'nfl': True, 'premier-league': True}


####################################################################################################
def Start():

    Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    # Set the default ObjectContainer attributes
    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(DEFAULT_LOGO)
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
            if logo in LOGOS:
                logo = R(logo + '.jpg')
            else:
                logo = R(DEFAULT_LOGO)

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

        oc.add(VideoClipObject(
            url=url,
            title=CleanName(name),
            thumb=thumb,
            summary=summary,
            duration=duration,
            tags=tags
        ))

    # It's possible that there is actually no vidoes are available for the ipad. Unfortunately, they
    # still provide us with empty containers...
    if len(oc) < 1:
        return ObjectContainer(header=name, message="There are no titles available for the requested item.")

    return oc


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