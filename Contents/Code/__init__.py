import datetime
common = SharedCodeService.common

NBC_URL = "http://www.nbcsports.com"
VIDEOS_URL = NBC_URL + "/video"
ALL_URL = NBC_URL + "/search/site/video%%3A?f[0]=bundle%%3Avideo_content_type&page=%s"
LATEST_URL = NBC_URL + "/api/v1/video_queues"

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'
PREFIX = '/video/nbcsports'

DATE_RE = Regex('\/public\/(\d{4})\/(\d{1,2})\/(\d{1,2})/')


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
@handler(PREFIX, L('VideoTitle'))
def MainMenu():

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(LatestVideos), title="Latest Videos", thumb=R('latest-videos.jpg')))

    # Iterate over all of the available categories and display them to the user.
    page = HTML.ElementFromURL(VIDEOS_URL)
    categories = page.xpath('//select[@title = "Browse channels"]/option')
    if len(categories) > 0:
        categories.pop(0)
    common.log("Categories: %d" % len(categories))

    for category in categories:
        cat_uri = category.get('value').replace('/video/', '')
        name = category.text
        title = CleanName(name)
        logo = name.lower().replace(' ', '-')
        logo = R(logo + '.jpg')
        # this doesn't work and 2 hours of slinging crap leaves me no closer to knowing what does
        if logo is None or logo == "":
            logo = R(ICON)

        common.log("Category: %s, Name: %s, Logo: %s" % (cat_uri, name, logo))

        oc.add(DirectoryObject(
            key=Callback(ListVideos,
            uri=cat_uri,
            name=title),
            title=title,
            thumb=logo))

    #oc.add(DirectoryObject(key=Callback(AllVideos), title=L('All Videos'), thumb=R('icon-dark.jpg')))
    #oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.nbcsports", title=L("Search NBCSports.com Videos"), prompt=L("Search for Videos")))

    return oc


####################################################################################################
@route(PREFIX + '/listvideos')
def ListVideos(uri, name, page=0):

    page = int(page)

    common.log("ListVideos(%s, %s, %d)" % (uri, name, page))

    oc = ObjectContainer(view_group="InfoList", title1=name)

    url = VIDEOS_URL + '/' + uri
    if page > 0:
        url += '?page=%d' % page

    html = HTML.ElementFromURL(url)

    thumbs = html.xpath('//div[@class = "video-event-thumb__image"]//img/@src')
    links = html.xpath('//div[@class = "video-event-thumb__image"]/a/@href')
    titles = html.xpath('//span[@class = "video-event-thumb__event-name"]/text()')

    num_thumbs = len(thumbs)
    num_links = len(links)
    num_titles = len(titles)
    common.log("Thumbs: %d, Links: %d, Titles: %d" % (num_thumbs, num_links, num_titles))

    if num_thumbs < 1 or num_links < 1 or num_titles < 1 or num_thumbs != num_links:
        return ObjectContainer(header=name, message="D'oh! Me Fail Videos? Unpossible!.")

    for index in range(num_thumbs):
        url = NBC_URL + links[index]
        title = titles[index]
        thumb = thumbs[index]

        originally_available_at = None

        result = DATE_RE.search(thumb)
        if result is not None:
            thumb_dates = result.groups()
            if len(thumb_dates) == 3:
                year = int(thumb_dates[0])
                month = int(thumb_dates[1])
                day = int(thumb_dates[2])
                common.log("Date found: %s" % str(thumb_dates))
                originally_available_at = datetime.date(year, month, day)

        oc.add(VideoClipObject(url=url, title=title, thumb=thumb, originally_available_at=originally_available_at))

    oc.add(NextPageObject(key=Callback(ListVideos, uri=uri, name=name, page=page + 1), title="More Videos..."))

    return oc


####################################################################################################
def LatestVideos():

    oc = ObjectContainer(view_group="InfoList", title1="Latest Videos")

    data = JSON.ObjectFromURL(LATEST_URL)

    for tray_index in range(len(data['trays'])):

        tray = data['trays'][tray_index]
        oc.add(DirectoryObject(key=Callback(ListLatest, title=tray['trayTitle']),
                               title=tray['trayTitle'],
                               thumb=R("latest-videos.jpg")))

    return oc


####################################################################################################
def ListLatest(title):

    oc = ObjectContainer(title1=title)

    data = JSON.ObjectFromURL(LATEST_URL)

    for tray_index in range(len(data['trays'])):
        tray = data['trays'][tray_index]
        if tray['trayTitle'] == title:
            for entry in tray['entries']:
                url = NBC_URL + entry['nodeUrl']
                oc.add(VideoClipObject(url=url, title=entry['title'], thumb=entry['plmedia$defaultThumbnailUrl']))

    return oc


####################################################################################################
def AllVideos(page=0):

    oc = ObjectContainer(title2='Page ' + str(page + 1))

    url = ALL_URL % page
    data = HTML.ElementFromURL(url)

    for video in data.xpath('//li[@class="search-result"]/h3/a'):
        title = video.text
        link = video.get('href')
        commong.log("%s | %s" % (title, link))
        oc.add(VideoClipObject(url=link, title=title))

    if len(data.xpath('//li[contains(@class,"pager-next")]/a')) > 0:
        oc.add(NextPageObject(key=Callback(AllVideos, page=page+1), title="More Videos..."))

    if len(oc) < 1:
        commong.log ('nbcsports.com search query returned no results')
        return ObjectContainer(header="Empty", message="There are no videos results to list right now.")
    else:
        return oc


####################################################################################################
def CleanName(name):
    # Function cleans up HTML entities
    remove = [('&amp;', '&'), ('&quot;', '"'), ('&#233;', 'e'), ('&#8212;', ' - '), ('&#39;', '\''), ('&#46;', '.'),
              ('&#58;', ':'), ('&#8482;', '')]
    for trash, crap in remove:
        name = name.replace(trash, crap)

    return name.strip()
