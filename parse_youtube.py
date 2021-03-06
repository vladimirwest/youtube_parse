import sys
import os

import time




import subprocess

from utils import stats_util
from utils import queue_utils

from threading import Thread


import traceback

import youtube_video_searcher
from vad_first_parser import process_video

import const
import shutil

from glob import glob



reload(sys)
sys.setdefaultencoding('utf8')


def check_dependencies_installed():
    try:
        subprocess.check_output(['soxi'], stderr=subprocess.STDOUT)
        subprocess.check_output(['youtube-dl', '--help'], stderr=subprocess.STDOUT)
        subprocess.check_output(['ffmpeg', '--help'], stderr=subprocess.STDOUT)
    except Exception as ex:
        print 'ERROR: some of dependencies are not installed: youtube-dl, ffmpeg or sox: '+str(ex)
        return False

    return True

def setup():
    print 'main setup - start'
    queue_utils.setup()

    curr_dir_path = os.path.dirname(os.path.realpath(__file__))
    videos_data_dir = os.path.join(curr_dir_path, "data/")

    if not os.path.exists(videos_data_dir):
        os.makedirs(videos_data_dir)

    print 'main setup - end'


displayed_no_videos_to_process = False

def video_parser_thread_loop():
    global displayed_no_videos_to_process

    while True:
        #try_remove_to_delete_dir()

        #print 'video parser loop'

        if youtube_video_searcher.is_searching:
            # dont interefere
            print 'dont interefere with searching'
            time.sleep(3)
            continue

        #print "getting video id to parse..."
        video_id = queue_utils.get_video_to_process()

        #print 'got video id %s' % video_id

        if queue_utils.is_video_processed_or_failed(video_id):
            print("VIDEO %s is already processed" % video_id)

        if not video_id:
            if not displayed_no_videos_to_process:
                print 'no videos to parse - wait 5 seconds...'
                displayed_no_videos_to_process = True
            time.sleep(5)
            continue

        displayed_no_videos_to_process = False

        # start video processing
        queue_utils.put_video_to_processing(video_id)

        try:
            process_video(video_id)

            queue_utils.put_video_to_processed(video_id)
            subprocess.call("rm -rf data/"+ str(video_id) + "/audio*", shell=True)
        except Exception as e:
            print('failed to process video ' + video_id + ': ' + str(e))
            error_type = str(e)
            queue_utils.put_video_to_failed(video_id)
            subprocess.call("rm -rf data/" + str(video_id), shell=True)

        # sleep to allow other threads acces to csvs
        time.sleep(0.2)

        

def start_parsing(threads_num):
    
    try:        

        setup()

        # start searching thread
        youtube_video_searcher.start_searcher_thread()

        video_parser_threads = []
        # start parsing threads

        for i in range(0, threads_num):
            #print 'start parsing thread ' + str(i)
            thr = Thread(target=video_parser_thread_loop)
            thr.daemon = True
            thr.start()
            video_parser_threads.append(thr)

        # wait for threads
        while True: time.sleep(100)

    except (KeyboardInterrupt, SystemExit):
        print '\n! Received keyboard interrupt, quitting threads.\n'

    stats_util.show_global_stats()

if __name__ == "__main__":


    _threads_number = 20
    try:    
        _threads_number = int(sys.argv[sys.argv.index("--threads-num")+1])
    except:
        pass

    if check_dependencies_installed():
        print("Start parsing with %i threads" % _threads_number)
        start_parsing(threads_num=_threads_number)
