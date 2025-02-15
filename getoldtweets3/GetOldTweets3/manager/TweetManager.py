# -*- coding: utf-8 -*-

import json, re, datetime, sys, random, http.cookiejar
import urllib.request, urllib.parse, urllib.error
from pyquery import PyQuery
from .. import models
import time
class TweetManager:
    """A class for accessing the Twitter's search engine"""
    def __init__(self):
        pass

    user_agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:61.0) Gecko/20100101 Firefox/61.0',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:63.0) Gecko/20100101 Firefox/63.0',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Safari/605.1.15',
    ]

    @staticmethod
    def getTweets(tweetCriteria, receiveBuffer=None, bufferLength=100, proxy=None, debug=False):
        """Get tweets that match the tweetCriteria parameter
        A static method.

        Parameters
        ----------
        tweetCriteria : tweetCriteria, an object that specifies a match criteria
        receiveBuffer : callable, a function that will be called upon a getting next `bufferLength' tweets
        bufferLength: int, the number of tweets to pass to `receiveBuffer' function
        proxy: str, a proxy server to use
        debug: bool, output debug information
        """
        results = []
        resultsAux = []
        cookieJar = http.cookiejar.CookieJar()
        user_agent = random.choice(TweetManager.user_agents)

        all_usernames = []
        usernames_per_batch = 20
        if hasattr(tweetCriteria, 'username'):
            if type(tweetCriteria.username) == str or not hasattr(tweetCriteria.username, '__iter__'):
                tweetCriteria.username = [tweetCriteria.username]

            usernames_ = [u.lstrip('@') for u in tweetCriteria.username if u]
            all_usernames = sorted({u.lower() for u in usernames_ if u})
            n_usernames = len(all_usernames)
            n_batches = n_usernames // usernames_per_batch + (n_usernames % usernames_per_batch > 0)
        else:
            n_batches = 1
        print("Batches:", n_batches)
        print("Range Batches:", range(n_batches))
        for batch in range(n_batches):  # process all_usernames by batches
            refreshCursor = ''
            batch_cnt_results = 0

            if all_usernames:  # a username in the criteria?
                tweetCriteria.username = all_usernames[batch*usernames_per_batch:batch*usernames_per_batch+usernames_per_batch]

            active = True
            while active:
                json = TweetManager.getJsonResponse(tweetCriteria, refreshCursor, cookieJar, proxy, user_agent, debug=debug)
                if len(json['items_html'].strip()) == 0:
                    break

                refreshCursor = json['min_position']
                scrapedTweets = PyQuery(json['items_html'])
                #Remove incomplete tweets withheld by Twitter Guidelines
                scrapedTweets.remove('div.withheld-tweet')
                tweets = scrapedTweets('div.js-stream-tweet')

                if len(tweets) == 0:
                    break

                for tweetHTML in tweets:
                    tweetPQ = PyQuery(tweetHTML)
                    tweet = models.Tweet()
                    #######     NEW ATTRIBUTES MATCHING THE OUTPUT OF T-HOARDER_KIT     ######
                    # INITIALIZE attr
                    tweet.idTweet = ''
                    tweet.date = ''
                    tweet.author = ''
                    tweet.text = ''
                    tweet.app = ''
                    tweet.authorId = ''
                    tweet.authorFollowers = ''
                    tweet.authorFollowing = ''
                    tweet.authorNTweets = ''
                    tweet.authorLocation = ''
                    tweet.tweetUrls = ''
                    tweet.tweetGeo = ''
                    tweet.authorScreenName = ''
                    tweet.authorBio = ''
                    tweet.tweetURLMedia = ''
                    tweet.tweetTypeMedia = ''
                    tweet.quote = ''
                    tweet.tweeetsRelation = ''
                    tweet.repliedTweetId = ''
                    tweet.userRepliedTo = ''
                    tweet.retweetedTweetId = ''
                    tweet.userRetweeted = ''
                    tweet.quotedTweetId = ''
                    tweet.userQuoted = ''
                    tweet.firstHT = ''
                    tweet.lang = ''
                    tweet.authorCreationDate = ''
                    tweet.isVerified = False
                    tweet.authorAvatar = ''
                    tweet.permalink = ''

                    usernames = tweetPQ("span.username.u-dir b").text().split()
                    if not len(usernames):  # fix for issue #13
                        continue

                    tweet.author = '@' + usernames[0]
                    tweet.authorId = int(tweetPQ("a.js-user-profile-link").attr("data-user-id"))
                    rawtext = TweetManager.textify(tweetPQ("p.js-tweet-text").html(), tweetCriteria.emoji)
                    tweet.text = re.sub(r"\s+", " ", rawtext)\
                        .replace('# ', '#').replace('@ ', '@').replace('$ ', '$')
                    tweet.lang = tweetPQ("p.js-tweet-text").attr("lang")
                    tweet.idTweet = tweetPQ.attr("data-tweet-id")
                    tweet.permalink = 'https://twitter.com' + tweetPQ.attr("data-permalink-path")
                    tweet.authorScreenName = tweetPQ.attr("data-name")

                    # CHECKS IF THE TWEET IS A RETWEET BY THE ELEMENT SPAN WITH CLASS JS-RETWEEET-TEXT
                    # IF IT IS, FILL OUT THE ATTRIBUTES
                    isRetweet = tweetPQ("span.js-retweet-text").size() > 0
                    if isRetweet:
                        tweet.userRetweeted = '@' + usernames[0]
                        tweet.author = '@' + tweetPQ("div").attr("data-retweeter")
                        tweet.text = 'RT ' + tweet.userRetweeted + ': ' + tweet.text
                        tweet.retweetedTweetId = tweetPQ("div").attr("data-tweet-id")
                        tweet.idTweet = tweetPQ("div").attr("data-retweet-id")
                        tweet.permalink = 'https://twitter.com/' + tweetPQ("div").attr("data-retweeter") + '/status/' +  tweet.idTweet
                        tweet.authorScreenName = tweetPQ("span.js-retweet-text a").text()
                        tweet.authorId = int(tweetPQ("span.js-retweet-text a").attr("data-user-id"))

                    dateSec = int(tweetPQ("small.time span.js-short-timestamp").attr("data-time"))
                    tweet.date = datetime.datetime.fromtimestamp(dateSec, tz=datetime.timezone.utc)
                    tweet.formatted_date = datetime.datetime.fromtimestamp(dateSec, tz=datetime.timezone.utc)\
                                                            .strftime("%a %b %d %X +0000 %Y")
                    tweet.hashtags, tweet.mentions, tweet.firstHT = TweetManager.getHashtagsAndMentions(tweetPQ)

                    geoSpan = tweetPQ('span.Tweet-geo')
                    if len(geoSpan) > 0:
                        tweet.geo = geoSpan.attr('title')
                    else:
                        tweet.geo = ''

                    urls = []
                    for link in tweetPQ("a"):
                        try:
                            urls.append((link.attrib["data-expanded-url"]))
                        except KeyError:
                            pass

                    tweet.tweetUrls = ",".join(urls)
                    tweet.quote = ''
                    # CHECKS IF THE TWEET IS A REPLY
                    isReply = tweetPQ.attr("data-is-reply-to") #Contains true or nothing
                    # CHECKS IF THE TWEET IS A QUOTE
                    isQuoted = tweetPQ("div.QuoteTweet-container").size() > 0
                    if isQuoted:
                        tweet.tweeetsRelation = 'Quote'
                        rawQuote = TweetManager.textify(tweetPQ("div.QuoteTweet-text").text(),tweetCriteria.emoji)
                        tweet.quote = re.sub(r"\s+", " ", rawQuote)\
                            .replace('# ', '#').replace('@ ', '@').replace('$ ', '$')
                        tweet.quotedTweetId = tweetPQ("div.QuoteTweet-container div.QuoteTweet-innerContainer").attr("data-item-id")
                        tweet.userQuoted  = '@' + tweetPQ("div.QuoteTweet-container div").attr("data-screen-name")

                    # THE TWEET RELATION HIERARCHY IS RT > REPLY > QUOTE, IF IT IS A RT BUT ALSO A QUOTE, IT IS A RT, AND THE SAME APPLIES TO THE REST
                    if isReply:
                        tweet.tweeetsRelation = 'Reply'
                    if isRetweet:
                        tweet.tweeetsRelation = 'RT'
                    results.append(tweet)
                    resultsAux.append(tweet)

                    if receiveBuffer and len(resultsAux) >= bufferLength:
                        receiveBuffer(resultsAux)
                        resultsAux = []

                    batch_cnt_results += 1
                    if tweetCriteria.maxTweets > 0 and batch_cnt_results >= tweetCriteria.maxTweets:
                        active = False
                        break

            if receiveBuffer and len(resultsAux) > 0:
                receiveBuffer(resultsAux)
                resultsAux = []

        return results

    @staticmethod
    def getHashtagsAndMentions(tweetPQ):
        """Given a PyQuery instance of a tweet (tweetPQ) getHashtagsAndMentions
        gets the hashtags and mentions from a tweet using the tweet's
        anchor tags rather than parsing a tweet's text for words begining
        with '#'s and '@'s. All hashtags are wrapped in anchor tags with an href
        attribute of the form '/hashtag/{hashtag name}?...' and all mentions are
        wrapped in anchor tags with an href attribute of the form '/{mentioned username}'.
        """
        anchorTags = tweetPQ("p.js-tweet-text")("a")
        hashtags = []
        mentions = []
        isFirstHT = True
        firstHT = ''
        for tag in anchorTags:
            tagPQ = PyQuery(tag)
            url = tagPQ.attr("href")
            if url is None or len(url) == 0 or url[0] != "/":
                continue

            # Mention anchor tags have a data-mentioned-user-id
            # attribute.
            if not tagPQ.attr("data-mentioned-user-id") is None:
                mentions.append("@" + url[1:])
                continue

            hashtagMatch = re.match('/hashtag/\w+', url)
            if hashtagMatch is None:
                continue

            hashtag = hashtagMatch.group().replace("/hashtag/", "#")
            if isFirstHT:
                firstHT = hashtag
                isFirstHT = False
            hashtags.append(hashtag)

        return (" ".join(hashtags), " ".join(mentions), firstHT)

    @staticmethod
    def textify(html, emoji):
        """Given a chunk of text with embedded Twitter HTML markup, replace
        emoji images with appropriate emoji markup, replace links with the original
        URIs, and discard all other markup.
        """
        # Step 0, compile some convenient regular expressions
        imgre = re.compile("^(.*?)(<img.*?/>)(.*)$")
        charre = re.compile("^&#x([^;]+);(.*)$")
        htmlre = re.compile("^(.*?)(<.*?>)(.*)$")
        are = re.compile("^(.*?)(<a href=[^>]+>(.*?)</a>)(.*)$")

        # Step 1, prepare a single-line string for re convenience
        puc = chr(0xE001)
        if html == '' or html == None:
            return ''
        html = html.replace("\n", puc)

        # Step 2, find images that represent emoji, replace them with the
        # Unicode codepoint of the emoji.
        text = ""
        match = imgre.match(html)
        while match:
            text += match.group(1)
            img = match.group(2)
            html = match.group(3)

            attr = TweetManager.parse_attributes(img)
            if emoji == "unicode":
                chars = attr["alt"]
                match = charre.match(chars)
                while match:
                    text += chr(int(match.group(1),16))
                    chars = match.group(2)
                    match = charre.match(chars)
            elif emoji == "named":
                text += "Emoji[" + attr['title'] + "]"
            else:
                text += " "

            match = imgre.match(html)
        text = text + html

        # Step 3, find links and replace them with the actual URL
        html = text
        text = ""
        match = are.match(html)
        while match:
            text += match.group(1)
            link = match.group(2)
            linktext = match.group(3)
            html = match.group(4)

            attr = TweetManager.parse_attributes(link)
            try:
                if "u-hidden" in attr["class"]:
                    pass
                elif "data-expanded-url" in attr \
                and "twitter-timeline-link" in attr["class"]:
                    text += attr['data-expanded-url']
                else:
                    text += link
            except:
                pass

            match = are.match(html)
        text = text + html

        # Step 4, discard any other markup that happens to be in the tweet.
        # This makes textify() behave like tweetPQ.text()
        html = text
        text = ""
        match = htmlre.match(html)
        while match:
            text += match.group(1)
            html = match.group(3)
            match = htmlre.match(html)
        text = text + html

        # Step 5, make the string multi-line again.
        text = text.replace(puc, "\n")
        return text

    @staticmethod
    def parse_attributes(markup):
        """Given markup that begins with a start tag, parse out the tag name
        and the attributes. Return them in a dictionary.
        """
        gire = re.compile("^<([^\s]+?)(.*?)>.*")
        attre = re.compile("^.*?([^\s]+?)=\"(.*?)\"(.*)$")
        attr = {}

        match = gire.match(markup)
        if match:
            attr['*tag'] = match.group(1)
            markup = match.group(2)

            match = attre.match(markup)
            while match:
                attr[match.group(1)] = match.group(2)
                markup = match.group(3)
                match = attre.match(markup)

        return attr

    @staticmethod
    def getJsonResponse(tweetCriteria, refreshCursor, cookieJar, proxy, useragent=None, debug=False):
        """Invoke an HTTP query to Twitter.
        Should not be used as an API function. A static method.
        """
        url = "https://twitter.com/i/search/timeline?"

        if not tweetCriteria.topTweets:
            url += "f=tweets&"

        url += ("vertical=news&q=%s&src=typd&%s"
                "&include_available_features=1&include_entities=1&max_position=%s"
                "&reset_error_state=false")

        urlGetData = ''

        if hasattr(tweetCriteria, 'querySearch'):
            urlGetData += tweetCriteria.querySearch

        if hasattr(tweetCriteria, 'excludeWords'):
            urlGetData += ' -'.join([''] + tweetCriteria.excludeWords)

        if hasattr(tweetCriteria, 'username'):
            if not hasattr(tweetCriteria.username, '__iter__'):
                tweetCriteria.username = [tweetCriteria.username]

            usernames_ = [u.lstrip('@') for u in tweetCriteria.username if u]
            tweetCriteria.username = {u.lower() for u in usernames_ if u}

            usernames = [' from:'+u for u in sorted(tweetCriteria.username)]
            if usernames:
                urlGetData += ' OR'.join(usernames)

        if hasattr(tweetCriteria, 'within'):
            if hasattr(tweetCriteria, 'near'):
                urlGetData += ' near:"%s" within:%s' % (tweetCriteria.near, tweetCriteria.within)
            elif hasattr(tweetCriteria, 'lat') and hasattr(tweetCriteria, 'lon'):
                urlGetData += ' geocode:%f,%f,%s' % (tweetCriteria.lat, tweetCriteria.lon, tweetCriteria.within)

        if hasattr(tweetCriteria, 'since'):
            urlGetData += ' since:' + tweetCriteria.since

        if hasattr(tweetCriteria, 'until'):
            urlGetData += ' until:' + tweetCriteria.until

        if hasattr(tweetCriteria, 'minReplies'):
            urlGetData += ' min_replies:' + tweetCriteria.minReplies

        if hasattr(tweetCriteria, 'minFaves'):
            urlGetData += ' min_faves:' + tweetCriteria.minFaves

        if hasattr(tweetCriteria, 'minRetweets'):
            urlGetData += ' min_retweets:' + tweetCriteria.minRetweets

        if hasattr(tweetCriteria, 'lang'):
            urlLang = 'l=' + tweetCriteria.lang + '&'
        else:
            urlLang = ''
        url = url % (urllib.parse.quote(urlGetData.strip()), urlLang, urllib.parse.quote(refreshCursor))
        useragent = useragent or TweetManager.user_agents[0]

        headers = [
            ('Host', "twitter.com"),
            ('User-Agent', useragent),
            ('Accept', "application/json, text/javascript, */*; q=0.01"),
            ('Accept-Language', "en-US,en;q=0.5"),
            ('X-Requested-With', "XMLHttpRequest"),
            ('Referer', url),
            ('Connection', "keep-alive")
        ]

        if proxy:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}), urllib.request.HTTPCookieProcessor(cookieJar))
        else:
            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookieJar))
        opener.addheaders = headers

        if debug:
            print(url)
            print('\n'.join(h[0]+': '+h[1] for h in headers))

        try:
            time.sleep(1)
            response = opener.open(url)
            jsonResponse = response.read()
        except Exception as e:
            print("An error occured during an HTTP request:", str(e))
            print("Try to open in browser: https://twitter.com/search?q=%s&src=typd" % urllib.parse.quote(urlGetData))
            sys.exit()

        try:
            s_json = jsonResponse.decode()
        except:
            print("Invalid response from Twitter")
            sys.exit()

        try:
            dataJson = json.loads(s_json)
        except:
            print("Error parsing JSON: %s" % s_json)
            sys.exit()

        if debug:
            print(s_json)
            print("---\n")

        return dataJson
