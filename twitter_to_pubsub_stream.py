# twitter_to_pubsub_stream.py
import argparse
import json
import os

from google.cloud import pubsub_v1
import tweepy


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--stream_rule', type=str, required=True)
    parser.add_argument('--project_id', type=str, required=True)
    parser.add_argument('--topic_id', type=str, required=True)

    return parser.parse_args()


def write_to_pubsub(data, stream_rule):
    """
    Writes tweets to pubsub topic

    :param data: dict
    :param stream_rule: str
    :return: None
    """
    data["stream_rule"] = stream_rule
    data_formatted = json.dumps(data).encode("utf-8")
    id = data["id"].encode("utf-8")
    author_id = data["author_id"].encode("utf-8")

    future = publisher.publish(
        topic_path, data_formatted, id=id, author_id=author_id
    )
    print(future.result())


class Client(tweepy.StreamingClient):
    def __init__(self, bearer_token, stream_rule):
        super().__init__(bearer_token)

        self.stream_rule = stream_rule

    def on_response(self, response):
        """
        Formats response received
        :param response: twitterPipeline.twitter_to_pubsub_stream.Client.response
        :return:
        """
        tweet_data = response.data.data
        del tweet_data["edit_history_tweet_ids"]
        user_data = response.includes['users'][0].data
        result = tweet_data
        result["user"] = user_data
        print(result)
        print(self.stream_rule)
        write_to_pubsub(result, self.stream_rule)


if __name__ == "__main__":
    tweet_fields = ['id','text','author_id','created_at','lang']
    user_fields = ['description','created_at','location']
    expansions = ['author_id']
    bearer_token = os.environ["BEARER_TOKEN"]
    args = parse_args()
    streaming_client = Client(bearer_token, args.stream_rule)
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(args.project_id, args.topic_id)

    # remove existing rules
    rules = streaming_client.get_rules().data
    if rules is not None:
        existing_rules = [rule.id for rule in streaming_client.get_rules().data]
        streaming_client.delete_rules(ids=existing_rules)

    # add new rules and run stream
    streaming_client.add_rules(tweepy.StreamRule(args.stream_rule))
    streaming_client.filter(expansions=expansions, tweet_fields=tweet_fields, user_fields=user_fields)



