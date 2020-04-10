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
import threading
from geopy import Nominatim


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
                    print("Starting stream...")
                    self.stream.filter(languages = self.lang, track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example. The program will continue to use the old variables')
            else:
                try:
                    self.lang = False
                    self.keywords = key_rad.split(', ')
                    print("Starting stream...")
                    self.stream.filter(track = self.keywords, is_async = True)
                    print("Started stream?!")
                except:
                    messagebox.showerror('Error: Input error', 'The given input does not meet the right format, please enter according to the given example. The program will continue to use the old variables')
                    
        elif (streamtype == 2 and lang_loc and key_rad):
            try:
                self.location = self.geolocator.geocode(location_string)
                rad = convert_to_degrees(int(keyrad))
                self.loc = [self.location.longitude-rad, self.location.latitude-rad, self.location.longitude+rad, self.location.latitude+rad]
                print("Starting stream...")
                self.stream.filter(locations = self.loc, is_async = True)
                print("Starting stream...")
            except:
                messagebox.showerror('Error: Location not found', 'The given location has not been found. The program will continue to use the old variables')
        else:
            if streamtype == 1:
                messagebox.showerror('Error: No input', 'Twitter requires us to give a search term, please enter one. The program will continue to use the old variables')
            else:
                if not(key_Rad):
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a location, please enter one. The program will continue to use the old variables')
                else:
                    messagebox.showerror('Error: No input', 'Twitter requires us to give a radius, please enter one. The program will continue to use the old variables')

class IncomingTweets(tk.Frame):
    ''' Main interface class for the Twitter stream '''
    def __init__(self, parent, api, tweetQueue, treeQueue):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.api = api
        self.tweetQueue = tweetQueue
        self.treeQueue = treeQueue
        self.dict = {'leaves': dict(), 'tweets': dict()}
        self.last_branch_id = 0
        threading.Thread(target=self.check_tweet_queue, daemon=True).start()
        self.after(10, self.check_tree_queue)

        # Make menubar
        self.menubar = tk.Menu(self)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load conversation", command=exit)
        self.filemenu.add_command(label="Save conversation", command=exit)
        self.filemenu.add_command(label="Exit", command=exit)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.accountmenu = tk.Menu(self.menubar, tearoff=0)
        self.accountmenu.add_command(label="Load credentials", command=lambda:self.api.set_new_cred())
        self.menubar.add_cascade(label="Account", menu=self.accountmenu)
        self.parent.config(menu=self.menubar)
        
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
        
        self.var_button = tk.Button(self, text = "Start stream", command = lambda: self.set_variables())
        self.var_button.grid(column=1, row=5, rowspan =2, sticky = 'nse', padx=15, pady=15)
        
        # Treeview with conversations
        self.tree = ttk.Treeview(self)
        self.yscrollbarTree = ttk.Scrollbar(self, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.yscrollbarTree.set)
        self.yscrollbarTree.grid(row=0, column=0, sticky='nse')
        self.tree.grid(column=0, row=0, columnspan=3, sticky= 'nsew')

    def set_lan_key(self):
        self.old_loc = self.langloc_string.get()
        self.langloc_string.set(self.old_lang)
        self.langloc_label['text'] = 'Languages'
        self.old_rad = self.keyrad_string.get()
        self.keyrad_string.set(self.old_key)
        self.keyrad_label['text'] = 'Keywords'
        print(self.option_value.get())
        
    def set_loc_rad(self):
        self.old_lang = self.langloc_string.get()
        self.langloc_string.set(self.old_loc)
        self.langloc_label['text'] = 'Location'
        self.old_key = self.keyrad_string.get()
        self.keyrad_string.set(self.old_rad)
        self.keyrad_label['text'] = 'Radius'
        print(self.option_value.get())
        
    def check_tree_queue(self):
        ''' Gets items from tree queue and adds them to treeview, runs on main loop ''' 
        try:
            # Try getting an item from tree queue
            parent, id, text = self.treeQueue.getNextItem()
            try:
                # Try to insert item into tree
                self.tree.insert(parent, 'end', id, text=text)
            except:
                # Sometimes the text isn't compatible with treeview, eg. some emojis
                self.tree.insert(parent, 'end', id, text="TWEET CANNOT BE DISPLAYED")
        except: pass
        self.after(10, self.check_tree_queue)
        
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
                total_author_set = total_author_set.union(self.dict['tweets'][parent_id][author_set])
                total_author_set.add(status.author.name)
                authors = len(total_author_set)
                total_turns = total_turns + self.dict['tweets'][parent_id][turns] + 1
                if (authors > 1 and authors <= 10 and total_turns > 2 and total_turns <= 10):
                    # Check if convo meets author and turn requirements
                    author_set = self.dict['tweets'][parent_id][author_set]
                    author_set.add(status.author.name)
                    turns = self.dict['tweets'][parent_id][turns] + 1
                    # Add tweet to dictionary
                    self.dict['tweets'][status.id] = {
                        'author': status.author.name, 
                        'text': status.text, 
                        'parent': parent_id, 
                        'author_set': author_set, 
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
                    self.treeQueue.sendItem([str(branch_id)+'-'+str(turns-1), str(branch_id)+'-'+str(turns), status.text])
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
                        turns = result['turns'] + 1
                        # Add tweet to dictionary
                        self.dict['tweets'][status.id] = {
                            'author': status.author.name, 
                            'text': status.text, 
                            'parent': parent_id, 
                            'author_set': author_set, 
                            'turns': turns
                        }
                        branch_id = result['branch_id']
                        # Send the tweet to the tree queue, from where it will be added to the treeview
                        self.treeQueue.sendItem([str(branch_id)+'-'+str(turns-1), str(branch_id)+'-'+str(turns), status.text])
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
                    'author_set': {status.author.name}, 
                    'turns': 1
                }
                # Create new id for converstation and add it to leaves in dict
                self.last_branch_id += 1
                branch_id = self.last_branch_id
                self.dict['leaves'][leaf_id] = branch_id
                # Send the tweet to the tree queue, from where it will be added to the treeview
                self.treeQueue.sendItem(['', str(branch_id)+'-'+str(1), status.text])
                return {'author_set': {status.author.name}, 'turns': 1, 'branch_id': branch_id}
            else:
                # If convo doesn't meet requirements, return False
                return False
        
    def set_variables(self):
        self.api.set_var(self.langloc_string.get(), self.keyrad_string.get(), self.option_value.get())
        self.var_button['text'] = 'Set variables'

def convert_to_degrees(dist):
    return (dist*(1/111))


def main():
    tweetQueue = MyQueue(100, False, False)
    treeQueue = MyQueue(100, True, False)
    api = Credentials(tweetQueue)
    api.setup_stream()
    root = tk.Tk()
    root.geometry('1280x720')
    inc_tweets = IncomingTweets(root, api, tweetQueue, treeQueue)
    inc_tweets.pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
    root.mainloop()

if __name__ == "__main__":
    main()
