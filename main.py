from flask import Flask, flash
from flask import render_template, url_for, redirect, request, session, send_from_directory
from scraping import generateURL, findVideos
from pytube import YouTube
from datetime import datetime
import time
import os
import shutil
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import moviepy.editor as mp
import re

SECRET_KEY = os.urandom(32)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY


def sensor():
    try:
        shutil.rmtree('/static/cache',ignore_errors=True)
    except:
        pass

sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor,'interval',hours=24)
sched.start()

@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
def home():
    
    if request.method=="POST":
        if "search" in request.form:
            

            sortby = request.form["sortby"]
            search = request.form['search']
            
            results_dict=findVideos(generateURL(search,sortby),8)
            count = 0;
            while len(results_dict) == 0:
                count+=1;
                if count > 5:
                    return redirect(url_for("home"))
                results_dict=findVideos(generateURL(search))
            session['dict']=results_dict

            return render_template("home.html", title='Home', results_dict=results_dict, search=search)


        if "url" in request.form:
            url = request.form["url"]
            video = YouTube(url)
           
            video.streams.filter(progressive=True).first().download("static/cache/video")
            video.streams.filter(only_audio=True).first().download("static/cache/audio")
            tgt_folder = "static/cache/audio"
            
           

            for file in [n for n in os.listdir(tgt_folder) if re.search('mp4',n)]:
                full_path = os.path.join(tgt_folder, file)
                output_path = os.path.join(tgt_folder, os.path.splitext(file)[0] + '.mp3')
                clip = mp.AudioFileClip(full_path) # disable if do not want any clipping
                clip.write_audiofile(output_path)
            
            
            
            video_title = video.title
            os.remove("static/cache/audio/"+video_title.replace("\"","").replace(".","").replace("\'","")+".mp4")
            results_dict=session['dict']
            
            return render_template("home.html", title="Home",results_dict=results_dict ,video_title=video_title)

        


    return render_template('home.html', title='Home')

atexit.register(lambda: sched.shutdown())

if __name__ == '__main__':
    app.run()
