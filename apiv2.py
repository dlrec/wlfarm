# TODO
# - loop for search results (for now it's limited to the last 100 search results)
# - filter giveaways for only a selected projects list
# - Remove tweets with mention to Discord?!?!

import os
import tweepy
import json
import time
from dotenv import load_dotenv
import csv
import random
import pandas as pd

# load twitter keys from .env field
load_dotenv(".env")

# get your userId in https://tweeterid.com/
userId = os.getenv("USER_ID")

# Replace with your own search query
query = '(WL OR Whitelist OR whitelist) (RT OR retweet) like tag giveaway -is:retweet'

# quantity of tweets to retrieve from search
# max returned by twitter API is 100
MAX_RESULTS = 100

# filter for low followers accounts
follower_count_min = 10000

# delay between actions
WAIT_TIME = 2

# load data from previous giveaways
past_giveaways = pd.read_csv("giveaways.csv")

# load users to mention in response
with open("friends.txt", "r") as f:
    friends = f.read().splitlines()

# load words to add to response
with open("words.txt", "r") as f:
    words = f.read().splitlines()

client = tweepy.Client(consumer_key=os.getenv('API_KEY'),
                       consumer_secret=os.getenv('API_KEY_SECRET'),
                       access_token=os.getenv('ACCESS_TOKEN'),
                       access_token_secret=os.getenv('ACCESS_TOKEN_SECRET'),
                       bearer_token=os.getenv("BEARER_TOKEN"))

tweets = client.search_recent_tweets(
    query=query,
    # TODO - check if 'public_metrics are needed here
    tweet_fields=['author_id', 'created_at', 'entities', 'public_metrics'],
    expansions=['author_id'],
    #user_fields=['id', 'name', 'username', 'created_at', 'description', 'public_metrics', 'verified'],
    user_fields=['id', 'name', 'username','public_metrics'],
    max_results=MAX_RESULTS
    )

# create dict with author_ids and followers count
author_list = dict()
for author in tweets.includes['users']:
    author_dict = dict()
    author_dict['id'] = author['id']
    author_dict['username'] = author['username']
    author_dict['followers_count'] = author.data['public_metrics']['followers_count']
    author_list[author['id']]=author_dict

for i,tweet in enumerate(tweets.data):
    print("---------------------------------------------------")
    if tweet.id in past_giveaways.tweet_id.values:
        print(f"Already entered giveaway in tweet id: {tweet.id}")
        continue

    # empty list to store author and mentions ids
    mentioned_ids = []
    mentioned_ids.append(tweet.author_id)

    # check number of followers
    if(author_list[tweet.author_id]['followers_count'] > follower_count_min):
        try:
            for mention in tweet.entities['mentions']:
                mentioned_ids.append(int(mention['id']))

            # script auto adds author_id and all mentions
            # remove duplicates to avoid double following requests
            mentioned_ids = list(set(mentioned_ids))

            print(f"Entering giveaway posted by: {author_list[tweet.author_id]['username']} with tweet_id: {tweet.id} ")
            giveaway_details = [
                int(time.time()),
                tweet.id,
                tweet.author_id,
                author_list[tweet.author_id]['username']
            ]

            try:
                # retweet
                print("retweeting giveaway...")
                client.retweet(tweet_id=tweet.id)
                time.sleep(WAIT_TIME)

                # like tweet
                print("liking giveaway...")
                client.like(tweet_id=tweet.id)
                time.sleep(WAIT_TIME)

                # follow author and mentioned users
                print("following tweet author and mentioned users...")
                for userId in mentioned_ids:
                    print(f"Following {userId}")
                    client.follow_user(target_user_id=userId)
                    time.sleep(WAIT_TIME)
                
                # reply with text
                reply_text = f"{random.choice(words)} \n {' '.join(friends)}"
                print(f"Replying with text: {reply_text}")
                client.create_tweet(text=reply_text, in_reply_to_tweet_id=tweet.id)
                
                # save giveaway data to db
                with open('giveaways.csv', 'a') as file:
                    writer = csv.writer(file)
                    writer.writerow(giveaway_details)
            except:
                print(f"Error when trying to enter giveaway with tweet_id: {tweet.id}")
        except:
            print(f"TODO. Error was raised because no mentions detected in tweet id: {tweet.id}")
    #else:
        # print(f"not enough followers for giveaway {tweet.id}")

    #print("---------------------------------------------------")

print("finished")
