#!/usr/bin/python3
# File name: assignment3.py
# Authors: Lakeman, G (s3383180) and Algra, N (s3133125)
# Date: 05-04-20

import tweepy
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import messagebox
import time
import queue
import json
import threading
from geopy import Nominatim
from nltk.sentiment.vader import SentimentIntensityAnalyzer


class CustomStream(tweepy.StreamListener):
    ''' Subclass of tweepy StreamListener with custom on_status to send tweets to tweet queue '''
    def __init__(self, q):
        tweepy.StreamListener.__init__(self)
        self.myQueue = q
    
    def on_status(self, status):
        # Add stuff here to what to do when a tweet appears
        if status.in_reply_to_status_id:
            #print(status.text)
            self.myQueue.sendItem(status)

    def on_error(self, status_code):
        print(status_code)
        if status_code == 401:
            # To prevent logging in in a loop and getting blocked
            quit()


class MyQueue():
    ''' Queue class to transfer new submission data between threads '''
    def __init__(self, maxsize, sendBlock, getBlock):
        self.myqueue=queue.Queue(maxsize)
        self.sendBlock = sendBlock
        self.getBlock = getBlock

    def sendItem(self,item):
        ''' Add item to queue '''
        self.myqueue.put(item, block=self.sendBlock)

    def getNextItem(self):
        ''' Get item from queue '''
        message=self.myqueue.get(block=self.getBlock)
        return message


class Credentials():
    def __init__(self, queue):
        self.queue = queue
        self.geolocator = Nominatim(user_agent = 'Guus en Nick')

    def read_cred(self):
        f = open('credentials.txt', 'r')
        f_lines = f.readlines()
        self.consumer_key = f_lines[0].rstrip()
        self.consumer_secret = f_lines[1].rstrip()
        self.access_token = f_lines[2].rstrip()
        self.access_secret = f_lines[3].rstrip()
        
    def test_credentials(self):
        self.read_cred()
        try:
            self.test_auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            self.test_auth.set_access_token(self.access_token, self.access_secret)
            self.test_api = tweepy.API(self.test_auth)
            self.test_search = self.test_api.get_user('twitter')
            return True
        except:
            return False
    
    def set_new_cred(self):
        if self.test_credentials():
            self.setup_stream()
            print('New credentials will be used the next time the variables are set')
        
    def setup_stream(self):
        print("Setting up stream...")
        # Get credentials and create api
        self.read_cred()
        self.auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        self.auth.set_access_token(self.access_token, self.access_secret)
        self.api = tweepy.API(self.auth)
        
        # create stream
        self.stream_listener = CustomStream(self.queue)
        self.stream = tweepy.Stream(auth = self.api.auth, listener = self.stream_listener)
        
    def set_var(self, lang_loc, key_rad, stream_type):
        self.stream_type = stream_type
        if stream_type == 1 and key_rad:
            if (lang_loc and key_rad):
                try:
                    self.lang = lang_loc.split(', ')
                    self.keywords = key_rad.split(', ')
                    self.stream.disconnect()
                    print("Starting stream...")
                    self.stream.filter(languages = self.lang, track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example.')
            else:
                try:
                    self.lang = False
                    self.keywords = key_rad.split(', ')
                    self.stream.disconnect()
                    print("Starting stream...")
                    self.stream.filter(track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example. The program will continue to use the old variables')
                    
        elif (stream_type == 2 and lang_loc and key_rad):
            try:
                self.location = self.geolocator.geocode(lang_loc)
                rad = convert_to_degrees(int(key_rad))
                self.loc = [self.location.longitude-rad, self.location.latitude-rad, self.location.longitude+rad, self.location.latitude+rad]
                print(self.loc)
                self.stream.disconnect()
                print("Starting stream...")
                self.stream.filter(locations = self.loc, is_async = True)
                print("Starting stream...")
            except:
                messagebox.showerror('Error: Location not found', 'The given location has not been found. The program will continue to use the old variables')
        else:
            if stream_type == 1:
                messagebox.showerror('Error: No input', 'Twitter requires us to give a search term, please enter one. The program will continue to use the old variables')
            else:
                if not(key_Rad):
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a location, please enter one. The program will continue to use the old variables')
                else:
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a radius, please enter one. The program will continue to use the old variables')

class IncomingTweets(tk.Frame):
    ''' Main interface class for the Twitter stream '''
    def __init__(self, parent, api, tweetQueue, treeQueueOne, treeQueueTwo):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api
        self.tweetQueue = tweetQueue
        self.treeQueueOne = treeQueueOne
        self.treeQueueTwo = treeQueueTwo
        self.dict = {'leaves': dict(), 'tweets': dict()}
        self.loaded = dict()
        self.sentiment = dict()
        self.sid = SentimentIntensityAnalyzer()
        self.last_branch_id = 0
        threading.Thread(target=self.check_tweet_queue, daemon=True).start()
        self.after(10, self.check_tree_queues)
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=3)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=3)
        self.columnconfigure(4, weight=3)
        self.rowconfigure(0, weight=1)

        # Make menubar
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load conversation", command=lambda: self.load("en, nl-corona 1.json"))
        self.filemenu.add_command(label="Save conversation", command=self.save)
        self.filemenu.add_command(label="Exit", command=lambda: self.quit_program())
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.accountmenu = tk.Menu(self.menubar, tearoff=0)
        self.accountmenu.add_command(label="Load credentials", command=lambda:self.api.set_new_cred())
        self.menubar.add_cascade(label="Account", menu=self.accountmenu)
        self.parent.config(menu=self.menubar)
        
        ## First Frame
        
        # Treeview with conversations
        self.tree_one = ttk.Treeview(self)
        self.yscrollbarTreeOne = ttk.Scrollbar(self, orient='vertical', command=self.tree_one.yview)
        self.tree_one.configure(yscrollcommand=self.yscrollbarTreeOne.set)
        self.yscrollbarTreeOne.grid(row=0, column=1, sticky='nse')
        self.tree_one.grid(column=0, row=0, columnspan=2, sticky= 'nsew')
        
        # Input fields and buttons
        self.langloc_string = tk.StringVar()
        self.langloc_entry = tk.Entry(self, textvariable=self.langloc_string)
        self.langloc_string.set("en, nl")
        self.langloc_label = tk.Label(self, text='Languages')
        self.langloc_label.grid(column=0, row=1, sticky= 'nsw')
        self.langloc_entry.grid(column=0, row=2, columnspan = 2, sticky= 'nswe')
        
        self.keyrad_string = tk.StringVar()
        self.keyrad_entry = tk.Entry(self, textvariable=self.keyrad_string)
        self.keyrad_string.set("Example, #List, @Input")
        self.keyrad_label = tk.Label(self, text='Keywords')
        self.keyrad_label.grid(column=0, row=3, sticky= 'nsw')
        self.keyrad_entry.grid(column=0, row=4, columnspan = 2, sticky= 'nswe')
        self.old_loc = "Oude Kijk in Het Jatstraat 26 Groningen"
        self.old_rad = '50'
        
        self.option_value = tk.IntVar()
        self.option1 = tk.Radiobutton(self, text='Languages and Keywords', variable = self.option_value, value=1, command = lambda: self.set_lan_key())
        self.option1.select()
        self.option1.grid(column=0, row=5, sticky= 'nsw')
        self.option2 = tk.Radiobutton(self, text='Location and Radius', variable = self.option_value, value=2, command = lambda: self.set_loc_rad())
        self.option2.grid(column=0, row=6, sticky= 'nsw')
        
        # Buttons
        self.var_button = tk.Button(self, text = "Start stream", command = lambda: self.set_variables())
        self.var_button.grid(column=1, row=7, sticky = 'nsew', pady = 15, padx = 15)
        self.stop_button = tk.Button(self, text = "Stop stream", command = lambda: self.stop_stream())
        self.stop_button.grid(column=0, row=7, sticky = 'nsew', pady = 15, padx = 15)
        
        ## Second Frame
        
        # Second Treeview
        self.tree_two = ttk.Treeview(self)
        self.yscrollbarTreeTwo = ttk.Scrollbar(self, orient='vertical', command=self.tree_two.yview)
        self.tree_two.configure(yscrollcommand=self.yscrollbarTreeTwo.set)
        self.yscrollbarTreeTwo.grid(row=0, column=4, sticky='nse')
        self.tree_two.grid(column=3, row=0, columnspan = 2, sticky= 'nsew')
        
        # Input fields
        self.min_num_string = tk.StringVar()
        self.min_num_entry = tk.Entry(self, textvariable=self.min_num_string)
        self.min_num_string.set('2')
        self.min_num_label = tk.Label(self, text='Minimum number of participants')
        self.min_num_label.grid(column=3, row=1, sticky= 'nsw')
        self.min_num_entry.grid(column=3, row=2, sticky= 'nswe')
        
        self.max_num_string = tk.StringVar()
        self.max_num_entry = tk.Entry(self, textvariable=self.max_num_string)
        self.max_num_string.set('10')
        self.max_num_label = tk.Label(self, text='Maximum number of participants')
        self.max_num_label.grid(column=4, row=1, sticky= 'nsw')
        self.max_num_entry.grid(column=4, row=2, sticky= 'nswe')
        
        self.min_len_string = tk.StringVar()
        self.min_len_entry = tk.Entry(self, textvariable=self.min_len_string)
        self.min_len_string.set('3')
        self.min_len_label = tk.Label(self, text='Minimum length')
        self.min_len_label.grid(column=3, row=3, sticky= 'nsw')
        self.min_len_entry.grid(column=3, row=4, sticky= 'nswe')
        
        self.max_len_string = tk.StringVar()
        self.max_len_entry = tk.Entry(self, textvariable=self.max_len_string)
        self.max_len_string.set('10')
        self.max_len_label = tk.Label(self, text='Maximum length')
        self.max_len_label.grid(column=4, row=3, sticky= 'nsw')
        self.max_len_entry.grid(column=4, row=4, sticky= 'nswe')
        
        self.tres_pos_string = tk.StringVar()
        self.tres_pos_entry = tk.Entry(self, textvariable=self.tres_pos_string)
        self.tres_pos_string.set('0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001')
        self.tres_pos_label = tk.Label(self, text='List of positive tresholds')
        self.tres_pos_label.grid(column=3, row=5, sticky= 'nsw')
        self.tres_pos_entry.grid(column=3, row=6, sticky= 'nswe')
        
        self.tres_neg_string = tk.StringVar()
        self.tres_neg_entry = tk.Entry(self, textvariable=self.max_len_string)
        self.tres_neg_string.set('0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001')
        self.tres_neg_label = tk.Label(self, text='List of negative tresholds')
        self.tres_neg_label.grid(column=4, row=5, sticky= 'nsw')
        self.tres_neg_entry.grid(column=4, row=6, sticky= 'nswe')
    
        # Input buttons
        self.filter_button = tk.Button(self, text = "Set filter", command = lambda: self.set_variables())
        self.filter_button.grid(column=4, row=7, sticky = 'nsew', pady = 15, padx = 15)
    
    def save(self):
        ''' Saves current tweet dictionary to a .json file '''
        f = open(self.langloc_string.get()+"-"+self.keyrad_string.get()+" "+str(self.option_value.get())+".json", 'w')
        json_string = json.dumps(self.dict)
        f.write(json_string)
        f.close()
        
    def load(self, filename):
        ''' Loads a tweet dictionary from a .json file '''
        f = open(filename, 'r')
        self.loaded = json.load(f)
        f.close()
        for leaf in self.loaded['leaves']:
            # Get sentiment array for each conversation
            self.sentiment[leaf] = self.get_sentiment(leaf)
        print(self.sentiment)
        self.filter()
        
    def filter(self):
        min_num = int(self.min_num_string.get())
        max_num = int(self.max_num_string.get())
        min_len = int(self.min_len_string.get())
        max_len = int(self.max_len_string.get())
        tres_pos_str = self.tres_pos_string.get()
        tres_pos = [int(i) for i in tres_pos_str.split()]
        tres_neg_str = self.tres_neg_string.get()
        tres_neg = [int(i) for i in tres_neg_str.split()]
        for leaf in self.loaded['leaves']:
            num = len(self.loaded['tweets'][str(leaf)]['author_set'])
            len = self.loaded['tweets'][str(leaf)]['turns']
            pos = [i['pos'] for i in self.sentiment[leaf]]
            neg = [i['neg'] for i in self.sentiment[leaf]]
            if num >= min_num and num <= max_num and len >= min_len and len <= max_len:
                requirements_met = True
                for i in range(len):
                    if not (pos[i] >= tres_pos[i] and neg[i] >= tres_neg[i]):
                        requirements_met = False
                if requirements_met:
                    self.show_convo(leaf, self.loaded['leaves'][str(leaf)])
                    
    def show_convo(self, tweet_id, branch_id):
        parent_id = self.loaded['tweets'][str(tweet_id)]['parent']
        if parent_id:
            # Recursive case
            self.show_convo(parent_id, branch_id)
        turns = self.loaded['tweets'][str(tweet_id)]['turns']
        text = self.loaded['tweets'][str[(tweet_id)]['text']
        self.treeQueueTwo.sendItem([str(branch_id)+'-'+str(turns-1), str(branch_id)+'-'+str(turns), text])
            
    def get_sentiment(self, tweet_id):
        ''' Recursively get sentiment analysis of every tweet in conversation '''
        parent_id = self.loaded['tweets'][str(tweet_id)]['parent']
        if parent_id:
            # Recursive case
            sentiments = self.get_sentiment(parent_id)
        else:
            # Base case
            sentiments = list()
        ss = self.sid.polarity_scores(self.loaded['tweets'][str(tweet_id)]['text'])
        sentiments.append({'pos': ss['pos'], 'neg': ss['neg']})
        return sentiments

    def set_lan_key(self):
        self.old_loc = self.langloc_string.get()
        self.langloc_string.set(self.old_lang)
        self.langloc_label['text'] = 'Languages'
        self.old_rad = self.keyrad_string.get()
        self.keyrad_string.set(self.old_key)
        self.keyrad_label['text'] = 'Keywords'
        
    def set_loc_rad(self):
        self.old_lang = self.langloc_string.get()
        self.langloc_string.set(self.old_loc)
        self.langloc_label['text'] = 'Location'
        self.old_key = self.keyrad_string.get()
        self.keyrad_string.set(self.old_rad)
        self.keyrad_label['text'] = 'Radius'
        
    def check_tree_queues(self):
        ''' Gets items from tree queue and adds them to treeview, runs on main loop ''' 
        try:
            # Try getting an item from tree queue ONE
            parent, id, text = self.treeQueueOne.getNextItem()
            try:
                # Try to insert item into tree
                self.tree_one.insert(parent, 'end', id, text=text)
            except:
                # Sometimes the text isn't compatible with treeview, eg. some emojis
                self.tree_one.insert(parent, 'end', id, text="TWEET CANNOT BE DISPLAYED")
        except: pass
        
        try:
            # Try getting an item from tree queue TWO
            parent, id, text = self.treeQueueTwo.getNextItem()
            try:
                # Try to insert item into tree
                self.tree_one.insert(parent, 'end', id, text=text)
            except:
                # Sometimes the text isn't compatible with treeview, eg. some emojis
                self.tree_one.insert(parent, 'end', id, text="TWEET CANNOT BE DISPLAYED")
        except: pass
        self.after(10, self.check_tree_queues)
        
    def check_tweet_queue(self):
        ''' Threaded function which takes tweets from queue, has them processed and added to tree queue '''
        while True:
            try:
                # Try getting an item from tweet queue
                status = self.tweetQueue.getNextItem()
                # Recursively process the conversation
                self.process_convo(status.id, status, set(), 0)
            except: pass
            time.sleep(0.01)
    
    def process_convo(self, leaf_id, status, total_author_set, total_turns):
        ''' Recursively traces a converation to its root, checks turn and author count, and adds it if valid '''
        #print("doing something with id:")
        #print(status.id)
        parent_id = status.in_reply_to_status_id  
        if (parent_id):
            # If tweets has a parent, we haven't reached the root yet
            if parent_id in self.dict['tweets']:
                # If the parent is already in the dictionary we use the data from there
                author_set = set()
                for i in self.dict['tweets'][parent_id][author_set]:
                    author_set.add(i)
                author_set.add(status.author.name)
                total_author_set.union(author_set)
                authors = len(total_author_set)
                turns = self.dict['tweets'][parent_id][turns] + 1
                total_turns += turns
                if (authors > 1 and authors <= 10 and total_turns > 2 and total_turns <= 10):
                    # Check if convo meets author and turn requirements
                    author_list = list()
                    for i in author_set:
                        author_list.append(i)
                    # Add tweet to dictionary
                    self.dict['tweets'][status.id] = {
                        'author': status.author.name, 
                        'text': status.text, 
                        'parent': parent_id, 
                        'author_set': author_list, 
                        'turns': turns
                    }
                    # Conversations are identified by their leaf, which carries the id for the entire convo
                    if parent_id in self.dict['leaves']:
                        # If the parent was a preexisting leaf, it will be replaced by the new leaf
                        branch_id = self.dict['leaves'][parent_id]
                        self.dict['leaves'].pop(parent_id)
                    else:
                        # Else we make a new id
                        self.last_branch_id += 1
                        branch_id = self.last_branch_id
                    self.dict['leaves'][leaf_id] = branch_id
                    # Send the tweet to the tree queue, from where it will be added to the treeview
                    self.treeQueueOne.sendItem([str(branch_id)+'-'+str(turns-1), str(branch_id)+'-'+str(turns), status.text])
                    print("found one in dict")
                    return {'author_set': author_set, 'turns': turns, 'branch_id': branch_id}
                else:
                    # If requirements are not met, return False
                    return False
            else:
                # Recursive case, if parent tweet is not already in dict
                parent = self.api.api.get_status(parent_id)
                total_author_set.add(status.author.name)
                authors = len(total_author_set)
                total_turns = total_turns + 1
                if (authors <= 10 and total_turns <= 10):
                    # Check if maximum requirements haven't already been exceeded
                    result = self.process_convo(leaf_id, parent, total_author_set, total_turns)
                    if result:
                        # If the recursive function doesn't return False, the conversation is valid
                        author_set = result['author_set']
                        author_set.add(status.author.name)
                        author_list = list()
                        for i in author_set:
                            author_list.append(i)
                        turns = result['turns'] + 1
                        # Add tweet to dictionary
                        self.dict['tweets'][status.id] = {
                            'author': status.author.name, 
                            'text': status.text, 
                            'parent': parent_id, 
                            'author_set': author_list, 
                            'turns': turns
                        }
                        branch_id = result['branch_id']
                        # Send the tweet to the tree queue, from where it will be added to the treeview
                        self.treeQueueOne.sendItem([str(branch_id)+'-'+str(turns-1), str(branch_id)+'-'+str(turns), status.text])
                        return {'author_set': author_set, 'turns': turns, 'branch_id': branch_id}
                    else:
                        # If recursive fuction returns False, so conversation is invalid
                        return False
                else:
                    # If maximum requirements exceeded, there's no point in continuing
                    return False
        else:
            # If the tweet has no parent, we have reached the root of the conversation
            total_author_set.add(status.author.name)
            authors = len(total_author_set)
            total_turns = total_turns + 1
            if (authors > 1 and authors <= 10 and total_turns > 2 and total_turns <= 10):
                # Check if convo meets author and turn requirements
                # Add tweet to dictionary
                self.dict['tweets'][status.id] = {
                    'author': status.author.name, 
                    'text': status.text, 
                    'parent': parent_id, 
                    'author_set': [status.author.name], 
                    'turns': 1
                }
                # Create new id for converstation and add it to leaves in dict
                self.last_branch_id += 1
                branch_id = self.last_branch_id
                self.dict['leaves'][leaf_id] = branch_id
                # Send the tweet to the tree queue, from where it will be added to the treeview
                self.treeQueueOne.sendItem(['', str(branch_id)+'-'+str(1), status.text])
                return {'author_set': {status.author.name}, 'turns': 1, 'branch_id': branch_id}
            else:
                # If convo doesn't meet requirements, return False
                return False
        
    def set_variables(self):
        self.api.set_var(self.langloc_string.get(), self.keyrad_string.get(), self.option_value.get())
        self.var_button['text'] = 'Change variables'
        
    def stop_stream(self):
        self.api.stream.disconnect()
        self.var_button['text'] = 'Start stream'
    
    def quit_program(self):
        self.api.stream.disconnect()
        exit()

def convert_to_degrees(dist):
    return ((dist*(1/111))/2)


def main():
    tweetQueue = MyQueue(100, False, False)
    treeQueueOne = MyQueue(100, True, False)
    treeQueueTwo = MyQueue(100, True, False)
    api = Credentials(tweetQueue)
    api.setup_stream()
    root = tk.Tk()
    root.geometry('1280x720')
    inc_tweets = IncomingTweets(root, api, tweetQueue, treeQueueOne, treeQueueTwo)
    inc_tweets.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    root.mainloop()

if __name__ == "__main__":
    main()
