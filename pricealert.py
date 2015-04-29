#!/usr/bin/env python

import sys
import praw
import twilio
from twilio.rest import TwilioRestClient
import json

SETTINGS = "settings.json"
INFO = "queue.json"

def get_saved_submissions(input_file):
    """ Function returns a dict of the latest submissions already
        processed by the script """
    with open(input_file, "r+") as submissions:
        try:
            new_map = json.load(submissions)
            return new_map
        except (ValueError, IOError):
            # No information in file
            return {}

def main():
    with open(SETTINGS, "r") as settings_file:
        try:
            settings_map = json.load(settings_file)
        except (ValueError, IOError):
            print("Could not parse settings file {}".format(SETTINGS))
            raise

    new_data = False
    reddit_instance = praw.Reddit("PriceAlert price notifer - /u/Charly")
    fmf_new_queue = list(reddit_instance.get_subreddit("frugalmalefashion").get_new(limit=10))
    to_notify = []
    feed_map = get_saved_submissions(INFO)

    for item in fmf_new_queue:
        if item.fullname not in feed_map:
            new_data = True
            feed_map[item.fullname] = [item.title, item.url, item.permalink, item.created_utc, item.short_link]
            to_notify.append(item.fullname)

    if new_data:
        try:
            account_sid = settings_map["account_sid"]
            auth_token = settings_map["auth_token"]
            twilio_client = TwilioRestClient(account_sid, auth_token)
            for post in to_notify:
                metadata = feed_map[post]
                message_body = "\nFMF: {}\n".format(metadata[0].encode('ascii', 'ignore'))
                if metadata[1] == metadata[2]:
                    message_body = message_body + "\nReddit (self): {}\n".format(metadata[-1])
                else:
                    message_body = message_body + "\nURL: {}\nReddit: {}\n".format(metadata[1], metadata[-1])
                message = twilio_client.messages.create(body=message_body,
                                                        to=settings_map["personal_number"],
                                                        from_=settings_map["service_number"])
                print(message.sid + " At time: " + str(metadata[3]))
        except twilio.TwilioRestException as e:
            print(e)


    with open(INFO, "w") as data_dumper:
        json.dump(feed_map, data_dumper, ensure_ascii=True)

if __name__ == "__main__":
    main()
