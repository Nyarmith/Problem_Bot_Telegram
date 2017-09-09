#!/usr/bin/env python
#sends either txt or png in email to listed users

import smtplib
import telepot
import os
import yaml
import random
import re

CONFIGFILE   = '/home/reader/Projects/Problem_Notifier_Telegram/config.yml';
PROBLEM_DAT  = '/home/reader/Projects/Problem_Notifier_Telegram/prob_tracking.yml';

#--good sorting--
def tryint(s):
    try:
        return int(s)
    except:
        return s

def alphanum_key(s):
    """ Turn a string into a list of string and number chunks.
        "z23a" -> ["z", 23, "a"]
    """
    return [ tryint(c) for c in re.split('([0-9]+)', s) ]

def sort_nicely(l):
    """ Sort the given list in the way that humans expect.
    """
    l.sort(key=alphanum_key)


def get_immediate_subdirectories(a_dir):
    os.chdir('/home/reader/Projects/Problem_Notifier');
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]

def removekey(d, key):
    r = dict(d)
    del r[key]
    return r

#--Problem Manager Definition
#   1 problemManager = 1 chat
class ProblemManager(object):
    def __init__(self):
        #dict of "source1" : {"problems_done" : {"Chapter_1" : [] , ..}, "problems_not_done": {"Chapter_1" : [], ..}}, source2: ...
        self.cur_source = None
        self.problems   = {}  
        self.joined_usrs= {}  #user1 : 'ready', user2 : 'ready', user3 : 'not-ready', etc... (but with True and False)
        #populate problems

    #select pool to draw problems from
    def selectSource(src):
        if src in self.problems.keys():
            self.cur_source = src
            return True
        else:
            return False

    def sendRandomProblem():

    #def sendChapterProblem(source, chapter): # TODO: as part of mode

    def addUser(uname):
        if uname.id not in self.joined_usrs.keys():
            self.joined_usrs[uname.id] = False
            return True
        else:
            return False

    def rmUser(uname):
        removeKey(self.joined_usrs, uname.id)

    #this means the user has understood and is able to move on
    def flagUser(uname):
        flag = self.joined_usrs[uname]
        self.joined_usrs[uname]

    #dispenses the next problem (TODO: based on the dispense-mode)
    def dispense():
        #first fresh problem from random chapter
        if not this.all_ready():
            return -1;


    def listSources():  #lists current sources, also looks for new ones
        #check if we haven't seen this source somewhere, so we can avoid overwriting in that scenario(but add the difference)
        mockobj = {}
        for dir in get_immediate_subdirectories(CONFIG_SPEC['problem_directory']):
            if not dir.startswith('.'):
                for subdir in get_immediate_subdirectories(dir):
                    chapters = {}
                    chapters[subdir] = set()
                    for curfile in os.listdir(dir + '/' + subdir):
                        chapters[subdir].add(dir+'/'+subdir+'/'+curfile)
                #compare the chapters object with the current running and completed chapters for the source
                if dir not in self.problems.keys():
                    self.problems[dir] = chapters
                else:
                    for chap in chapters.keys():
                        if chap not in self.problems[dir].keys():
                            self.problems[dir][chap] = chapters[chap] #this is wrong because it doesn't take into account problems_done and problems_not_done
                            self.problems[dir][chap] = chapters[chap]
                        else:


        #now that reading of the sources is done, let's return the actual sources
        return self.problems.keys()



    #def setDispenseMode(uname):


    def all_ready():
        for i in self.joined_usrs.keys():
            if self.joined_usrs[i] is False:
                return False

        return True



def load(filename):
   f = open(filename)
   state = yaml.load(f.read())
   f.close()
   return state

def save(obj, filename):
    f = open(filename, 'w')
    f.write(yaml.dump(obj))
    f.close()


#Bot Definition
class ProblemBot(object):
    def __init__(self):
        self.save_file='chats/ProblemBot'
        if os.path.isfile(self.save):
            self.chats = load(self.save)
        else:
            self.chats = {}

    def save(self):
        save(self.chats, self.save_file)

    #load file state to object
    def load(self, self):
        self.chats = load(self.save_file)

#these map to new commands
    def join(self, chat_id, args):
        if self.chats[chat_id].addUser(args[0]):
            bot.sendMessage(chat_id, "User %s Readied"   % args[0].first_name)
        else:
            bot.sendMessage(chat_id, "User %s already joined" % args[0].first_name)


    def leave(self, chat_id, args):
        return self.chats[chat_id].rmUser(args[0])

    def ready(self, chat_id, args):
        state = self.chats[chat_id].flagUser(args[0])
        if state == True:
            bot.sendMessage(chat_id, "User %s Readied"   % args[0].first_name)
        else:
            bot.sendMessage(chat_id, "User %s Unreadied" % args[0].first_name)

    #the name for this command is really up for grabs
    def give_problem(self, chat_id, args):
        newProb = self.chats[chat_id].dispense()  #returns filepath
        if newProb is None:
            bot.sendMessage(chat_id, "All problems in %s complete!" % self.chats[chat_id].cur_source)
        else if newProb == -1:
            bot.sendMessage(chat_id, "Users aren't readied!" % self.chats[chat_id].cur_source)
        
        bot.sendPhoto(newProb, open(newProb, 'rb'))

    def unready(self, chat_id, args):
        self.chats[chat_id]

    def select_source(self, chat_id, args):
        if self.chats[chat_id].selectSource(args[1]):
            bot.sendMessage(chat_id, "Source Selected!")
        else:
            bot.sendMessage(chat_id, "No Such Source!")


    def list_sources(self, chat_id, args):
        src_list = self.chats[chat_id].listSources()
        bot.sendMessage(chat_id, str(src_list))


    def start(self, chat_id, args):
        self.chats[chat_id] = ProblemManager()
        
    def help(self, chat_id, args):
        helpstr = "I have no idea, I'm so tired"
        return helpstr



PB = ProblemBot()

def handle(msg):
    chat_id = msg['chat']['id']
    command = msg['text']
    fromusr = msg['from']  #is a dict of 'first_name' : <users first name>, 'id' : <users id>

    print("got command: {}".format(command))

    split_msg = command.split()
    method    = split_msg[0][1:]
    args      = split_msg[1:]
    args.insert(0,fromusr)

    try:
        getattr(PB, method)(chat_id, args)
    except:
        bot.sendMessage(chat_id, "Invalid Command")




f = open('config.yml')
cfgstr = f.read()
mykey = yaml.load(cfgstr)['key']
f.close()
#initialize the bot as a global that everything relies on
bot = telepot.Bot(mykey)

print("i'm listening yo")
bot.message_loop(handle, run_forever=True)
