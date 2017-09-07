#!/usr/bin/env python
#sends either txt or png in email to listed users

import smtplib
import telepot
import os
import yaml
import random
import re

CONFIGFILE   = '/home/reader/Projects/Problem_Notifier/config.yml';
PROBLEM_DAT  = '/home/reader/Projects/Problem_Notifier/prob_tracking.yml';

#loaded config file
CONFIG_SPEC     = None
prob_tracking   = None

#good sorting

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

#emails a random problem, then updates our metadata lib
def sendRandomProblems(n):
    global CONFIG_SPEC
    problem_list = {}
    #get existing config
    # params
    f = open(CONFIGFILE)
    CONFIG_SPEC = yaml.load(f.read())
    f.close()
    # problems to ignore
    f = open(PROBLEM_DAT)
    prob_tracking = yaml.load(f.read())
    f.close()

    #get list of problems in your directories
    for dir in get_immediate_subdirectories(CONFIG_SPEC['problem_directory']):
        if not dir.startswith('.'):
            for subdir in get_immediate_subdirectories(dir):
                problem_list[dir + '/' + subdir] = set()
                for file in os.listdir(dir + '/' + subdir):
                    problem_list[dir + '/' + subdir].add(dir+'/'+subdir+'/'+file)
    
    completed_list = set(prob_tracking['sent_problems'])
    for key in problem_list.keys():
        problem_list[key] = problem_list[key] - completed_list
        #remove empty sets
        if len(problem_list[key]) == 0:
            problem_list = removekey(problem_list, key)

    to_send = []
    
    #pick n random chapters, and pick the first problem from whichever you choose
    for i in range(n):
        chapter = random.sample(problem_list.keys(),1)[0]
        problems = list(problem_list[chapter])
        sort_nicely(problems)
        to_send.append(problems[0])
        problems.pop(0)
        if len(problems) != 0:
            problem_list[chapter] = set(problems)
        else:
            problem_list = removekey(problem_list[chapter])
    
    
    for i in to_send:
        sendProblem(i)
        prob_tracking['sent_problems'].append(i)
    
    prob_tracking['sent_problems']
    f = open(PROBLEM_DAT,'w')
    f.write(yaml.dump(prob_tracking))
    f.close()

#formats given problem and sends it to the user
def sendProblem( prob ):
    global CONFIG_SPEC
    #get extension
    ext = prob.split('.')[-1]
    message=None
    f = open(prob,'rb')
    if ext == 'txt':
        message = MIMEText(f.read())
    elif ext == 'png':
        message = MIMEImage(f.read())
        message.add_header('Content-ID', '<image1>')
    f.close()
    
    prob_name = prob.split('/')[-1].split('.')[0]
    sendemail(CONFIG_SPEC['email'], CONFIG_SPEC['recipients'],# [],
        CONFIG_SPEC['subject'] + ' ' + prob_name, message,
	CONFIG_SPEC['email'], CONFIG_SPEC['pass'])
 
def sendemail(from_addr, to_addr_list,# cc_addr_list,
              subject, message,
              login, password,
              smtpserver='smtp.gmail.com:587'):
    global CONFIG_SPEC
    msg = MIMEMultipart()
    msg['From']      = from_addr
    msg['To']        = ','.join(to_addr_list)
    msg['Subject']   = '%s' % subject
    msg.preamble = 'This is a multi-part message in MIME format.'

    msg.attach(MIMEText('%s <br> <img src="cid:image1"> <br> Enyoy!' % CONFIG_SPEC['msg_header'], 'html'))
    msg.attach(message)

    server = smtplib.SMTP(smtpserver)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, msg.as_string())
    server.quit()


#1 problemManager = 1 chat
class ProblemManager(object):
    def __init__(self, prev_state={}):
        self.problems = prev_state  #I may just be able to serialize this with json

    #select pool to draw problems from
    def selectSource(src):

    def sendRandomProblem():

    def sendChapterProblem(source, chapter):

    def addUser(uname):

    def rmUser(uname):

    #this means the user has understood and is able to move on
    def flagUser(uname):

    #dispenses the next problem based on the dispense-mode
    def dispense():

    def setDispenseMode(uname):

class ProblemBot:
    def __init__(self):
        if os.path.isfile('chats/listo'):
            self.load()
        else:
            self.chats = {}
    #save current state to file
    def save(self):
        f = open('chats/listo', 'w')
        f.write(yaml.dump(self.listos))
        f.close()

    #load file state to object
    def load(self):
        f = open('chats/listo')
        self.chats = yaml.load(f.read())
        f.close()

#these map to new commands
    def new_chat(self, chat_id):
        self.chats[chat_id] = ProblemManager()

    def join(uname):
        self.chats[chat_id].join(uname)


