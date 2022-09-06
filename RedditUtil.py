import random
import requests
import time 

class RedditUtil:
    MEMES_STR = "memes"
    COMICS_STR = "comics"

    DATA_JSON_KEY = "data"
    CHILDREN_JSON_KEY = "children"
    DOMAIN_JSON_KEY = "domain"
    URL_JSON_KEY = "url"
    IMAGES_DOMAIN_JSON_VALUE = "i.redd.it"

    def __init__(self):
        self.ALREADY_POSTED = []

    def _get_api_request_meta(self):
        metadata = {
            "subreddit": "memes",  # fallback
            "limit": 100,
            "timeframe": "hour",  #hour, day, week, month, year, all
            "listing":"hot"  # controversial, best, hot, new, random, rising, top
        }
        return metadata

    def _request_reddit_api(self, subreddit):
        try:
            metadata = self._get_api_request_meta()
            listing, limit, timeframe = metadata["listing"], metadata["limit"], metadata["timeframe"]
            base_url = f'https://www.reddit.com/r/{subreddit}/{listing}.json?limit={limit}&t={timeframe}'
            request = requests.get(base_url, headers={'User-agent': 'bot'})
        except:
            base_url = f'https://www.reddit.com/r/{metadata["subreddit"]}/{listing}.json?limit={limit}&t={timeframe}'
            request = requests.get(base_url, headers={'User-agent': 'bot'})

            if not request:
                return None
        return request.json()[RedditUtil.DATA_JSON_KEY][
            RedditUtil.CHILDREN_JSON_KEY]

    def get_reddit_post(self, subreddit):
        posts_raw = self._request_reddit_api(subreddit)
        if not posts_raw:
            return None

        posts = []
        for rawp in posts_raw:
            if self._is_Posted(rawp):
                continue
            if (rawp[RedditUtil.DATA_JSON_KEY]["over_18"] != True and
                  rawp[RedditUtil.DATA_JSON_KEY]["is_video"] != True and
                  rawp[RedditUtil.DATA_JSON_KEY][RedditUtil.DOMAIN_JSON_KEY] in RedditUtil.IMAGES_DOMAIN_JSON_VALUE):
                posts.append(rawp)

        # print(json.dumps(posts))
        post = random.choice(posts)
        self._set_already_Posted(post)
        post = post[RedditUtil.DATA_JSON_KEY]
        return post

    def _set_already_Posted(self, raw_post):
        post_url = raw_post[RedditUtil.DATA_JSON_KEY][RedditUtil.URL_JSON_KEY]
        self.ALREADY_POSTED.append(post_url)

    def _is_Posted(self, raw_post) -> bool:
        post_url = raw_post[RedditUtil.DATA_JSON_KEY][RedditUtil.URL_JSON_KEY]
        return post_url in self.ALREADY_POSTED
    def prune_posts(self):
      # epoch_time = int(time.time())
      pass
## Reddit Tests
# redditUtil = RedditUtil()
# post = redditUtil.get_reddit_post(RedditUtil.MEMES_STR)
# print(post["url"])