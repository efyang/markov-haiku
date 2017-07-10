import praw
import string
import os


def get_secrets():
    client_id = os.environ['REDDIT_CLIENT_ID']
    client_secret = os.environ['REDDIT_CLIENT_SECRET']
    return (client_id, client_secret)


def get_comments_texts(subreddit, num_comments):
    (c_id, c_secret) = get_secrets()
    r = praw.Reddit(user_agent="Comment Extraction (by /u/HonorabruTroll)",
                    client_id=c_id,
                    client_secret=c_secret)
    for comment in r.subreddit(subreddit).comments(limit=num_comments):
        if "bot" not in comment.author.name.lower() \
                and comment.author.name != "AutoModerator" \
                and comment.author.name != "TIP_ME_COINS":
            yield comment.body


# returns the word chains
def get_raw_chains(subreddit, num_comments, allowed_words):
    allowed_chars = string.ascii_lowercase + string.digits + " .\'"
    all_sentences = list()
    for comment in get_comments_texts(subreddit, num_comments):
        sentences = ''.join([c for c in comment.lower() if c in allowed_chars])\
            .split('.')
        all_sentences.extend(sentences)
    chains = list()
    for sentence in all_sentences:
        words = [word for word in sentence.split(' ') if word in allowed_words]
        if words != []:
            chains.append(words)
    return chains
