import os
import tweepy
import logging

from src.utils import save_to_df, save_df_to_csv, is_tweet_valid

BATCH_SIZE=int(os.environ.get('BATCH_SIZE', 100))
TOT_TWEET=int(os.environ.get('TOT_TWEET', 1000))

class myStreamListener(tweepy.StreamingClient):
    total_number_of_tweets = 0
    current_number_batched = 0
    batched_tweets = []
    batch_num=0
    closed_peacefully = False

    def __init__(self, bearer_token, BASIC_DATA_PATH) -> None:
        self.BASIC_DATA_PATH = BASIC_DATA_PATH + '/tweets'
        self.df = None
        super().__init__(bearer_token, wait_on_rate_limit=True, return_type = dict, daemon=True )

    def reset_batch(self):
        self.df = None
        self.batched_tweets = []
        self.current_number_batched = 0
        self.batch_num+=1

    def on_tweet(self, tweet):
        if is_tweet_valid(tweet)==False:
           return
        try:
            self.batched_tweets.append(tweet)
            self.total_number_of_tweets += 1
            self.current_number_batched += 1

            if self.current_number_batched > BATCH_SIZE:
                logging.info('{} tweets parsed'.format(self.total_number_of_tweets))
                self.df = save_to_df(self.batched_tweets, self.df)
                save_df_to_csv(self.df, self.BASIC_DATA_PATH+'-{}.csv'.format(self.batch_num))
                self.reset_batch()

            if self.total_number_of_tweets > TOT_TWEET:
                self.closed_peacefully=True
                self.disconnect() 
        
        except Exception as e:
            logging.error('Encountered Exception: {}'.format(e))
            pass

    def on_errors(self, errors) :
        save_df_to_csv(self.df, self.BASIC_DATA_PATH+'-{}.csv'.format('BACKUP_E'))
        logging.error('on_errors: Encountered errors: {}'.format(errors))


    def on_exception(self, e):
        logging.error('on_exception: Encountered Exception: {}'.format(e))

    def on_disconnect(self):
        logging.info('on_disconnect')
        if not self.closed_peacefully:
            save_df_to_csv(self.df, self.BASIC_DATA_PATH+'-{}.csv'.format('BACKUP_D'))
