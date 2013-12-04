DEBUG = False
VIDEOS_URL = "http://www.nbcsports.com/ajax-pane/get-pane/3373/61644?/video"
ALL_URL = "http://www.nbcsports.com/search/site/video%%3A?f[0]=bundle%%3Avideo_content_type&page=%s"

NAME = L('Title')
ART = 'art-default.jpg'
ICON = 'icon-default.png'
PREFIX = '/video/nbcsports'

SHOWS = ['Dan Patrick Show', 'ProFootballTalk', 'SportsDash']

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
                key=Callback(ListVideos,
                id=cat_id,
                name=title),
                title=title,
                thumb=logo))

    for show in SHOWS:
        thumb = R(show.lower().replace(' ', '-') + '.jpg')
        oc.add(DirectoryObject(key=Callback(ListShow, show=show), title=L(show), thumb=thumb))

    oc.add(DirectoryObject(key=Callback(AllVideos), title=L('All Videos'), thumb=R('icon-dark.jpg')))
    oc.add(SearchDirectoryObject(identifier="com.plexapp.plugins.nbcsports", title=L("Search NBCSports.com Videos"), prompt=L("Search for Videos")))

    return oc


####################################################################################################
@route(PREFIX + '/listvideos')
def ListVideos(id, name):

    oc = ObjectContainer(view_group="InfoList", title1=name)

    page = HTML.ElementFromURL(VIDEOS_URL)

    thumbs = page.xpath('//div[@id = "channel-' + id + '"]//img/@src')
    links = page.xpath('//div[@id = "channel-' + id + '"]//div[contains(@class, "views-field-title")]//a')

    num_thumbs = len(thumbs)
    num_links = len(links)
    log("Thumbs: %d, Links: %d" % (num_thumbs, num_links))

    if num_thumbs < 1 or num_links < 1 or num_thumbs != num_links:
        return ObjectContainer(header=name, message="D'oh! Me Fail Videos? Unpossible!.")

    for index in range(num_thumbs):
        url = 'http://www.nbcsports.com' + links[index].get('href')
        title = CleanName(links[index].text)
        thumb = thumbs[index]

        oc.add(VideoClipObject(url=url, title=title, thumb=thumb))

    return oc


####################################################################################################
@route(PREFIX + '/listshow')
def ListShow(show):

    log("ListShow("+show+")")

    if show == 'ProFootballTalk':
        search = 'ProFootballTalk'
    elif show == 'Dan Patrick Show':
        search = 'DPS:'
    elif show == 'SportsDash':
        search = show

    oc = ObjectContainer(view_group="InfoList", title1=show)

    page = HTML.ElementFromURL(VIDEOS_URL)

    rows = page.xpath('//li[contains(@class, "views-row")]')
    log("Found %d rows" % len(rows))
    for row in rows:
        link = row.xpath('.//a[contains(text(), "' + search + '")]')
        log("Found %d link" % len(link))
        if len(link) == 1:
            title = link[0].text
            url = 'http://www.nbcsports.com' + link[0].get('href')
            thumb = row.xpath('.//img/@src')[0]

            oc.add(VideoClipObject(url=url, title=title, thumb=thumb))

    return oc


####################################################################################################
def AllVideos(page=0):

    oc = ObjectContainer(title2='Page '+str(page+1))

    url = ALL_URL % page
    data = HTML.ElementFromURL(url)

    for video in data.xpath('//li[@class="search-result"]/h3/a'):
        title = video.text
        link = video.get('href')
        Log("%s | %s" % (title, link))
        oc.add(VideoClipObject(url=link, title=title))

    if len(data.xpath('//li[contains(@class,"pager-next")]/a')) > 0:
        oc.add(NextPageObject(key=Callback(AllVideos, page=page+1), title="More Videos..."))

    if len(oc) < 1:
        Log ('nbcsports.com search query returned no results')
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


def log(str):
    if DEBUG:
        Log.Debug(str)