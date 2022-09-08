import collections
import random
import requests

class RedditUtil:
    MEMES_STR = "memes"
    COMICS_STR = "comics"

    DATA_JSON_KEY = "data"
    CHILDREN_JSON_KEY = "children"
    DOMAIN_JSON_KEY = "domain"
    URL_JSON_KEY = "url"
    IMAGES_DOMAIN_JSON_VALUE = "i.redd.it"

    def __init__(self):
        self.POSTS = {}
        self.ALREADY_POSTED = collections.deque()

    def _get_api_request_meta(self):
        metadata = {
            "subreddit": "memes",  # fallback subreddit
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

        return request.json()[RedditUtil.DATA_JSON_KEY][RedditUtil.CHILDREN_JSON_KEY]

    def get_reddit_post(self, subreddit):
        if subreddit in self.POSTS:
            posts = self.POSTS[subreddit]
        else:
            # print(f"New Subreddit {subreddit}")
            posts = []

        if not posts:
            posts_raw = self._request_reddit_api(subreddit)
            if not posts_raw:
                print("RedditAPI query failed!")
                return None

            for rawpost in posts_raw:
                post_url = rawpost[RedditUtil.DATA_JSON_KEY][RedditUtil.URL_JSON_KEY]
                if self._is_Posted(post_url):
                    continue
                # Filter adult content and videos
                if (rawpost[RedditUtil.DATA_JSON_KEY]["over_18"] != True and
                    rawpost[RedditUtil.DATA_JSON_KEY]["is_video"] != True and
                    rawpost[RedditUtil.DATA_JSON_KEY][RedditUtil.DOMAIN_JSON_KEY] == RedditUtil.IMAGES_DOMAIN_JSON_VALUE):
                        posts.append(post_url)
            self.POSTS[subreddit] = posts

        # print(json.dumps(posts))
        post_url = random.choice(posts)
        self._set_already_Posted(post_url, subreddit)
        return post_url

    def _set_already_Posted(self, post_url, subreddit):
        if post_url in self.POSTS[subreddit]:
          self.POSTS[subreddit].remove(post_url)
        self.ALREADY_POSTED.append(post_url)

        limit = self._get_api_request_meta()["limit"]
        if len(self.ALREADY_POSTED) > limit * 3:
          while self.ALREADY_POSTED and len(self.ALREADY_POSTED) >= limit:
              self.ALREADY_POSTED.popleft()

    def _is_Posted(self, post_url) -> bool:
        # post_url = raw_post[RedditUtil.DATA_JSON_KEY][RedditUtil.URL_JSON_KEY]
        return post_url in self.ALREADY_POSTED

## Reddit Tests
# redditUtil = RedditUtil()
# for i in range(1,500):
#     post = redditUtil.get_reddit_post(RedditUtil.MEMES_STR)
#     # post = redditUtil.get_reddit_post(RedditUtil.COMICS_STR)
#     # print(post)