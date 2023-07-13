import time
#import subprocess
import json
from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from zapv2 import ZAPv2
from webflask.models import Note
from webflask import db

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
def home_page():
    show_div = True # Set the value of show_div
    return render_template("base.html", show_div=show_div, user=current_user)

@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added successfully!', category='success')

    show_search = True # show_search bar
    return render_template("home.html", user=current_user, show_search=show_search, username=current_user.username)

@views.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    results = []  # Initialize results with an empty list
    search_query = ''  # Assign an initial value to search_query
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        results = Note.query.filter(
            Note.data.ilike(f'%{search_query}%'),
            Note.user_id==current_user.id).all()
    
    show_search = True # show_search bar
    return render_template('search.html', results=results, query=search_query, show_search=show_search, user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
    
    return jsonify({})

@views.route('/scan_url', methods=['GET', 'POST'])
#@login_required
def scan_url():
    if request.method == 'POST':
        scan_url = request.form.get('scan_url')
        try:
            # Start OWASP ZAP as a subprocess
            #zap_process = subprocess.Popen(['owasp-zap', '-daemon', '-host', '0.0.0.0', '-port', '8080'])

            # Wait for ZAP to initialize
            #time.sleep(20)
            time.sleep(5)

            # Initialize the ZAP API client
            zap_api_key = 'fullstack'  # Replace with your ZAP API key
            zap_base_url = 'http://localhost:8080'  # Replace with the base URL of your ZAP instance
            zap = ZAPv2(apikey=zap_api_key, proxies={'http': zap_base_url, 'https': zap_base_url})

            # Start a new ZAP session
            zap.core.new_session()

            # Open the target URL in ZAP
            zap.spider.scan(scan_url)

            # Wait for ZAP to complete its scanning actions
            while zap.spider.status() != '100':
                time.sleep(5)

            # Retrieve the ZAP alerts
            alerts = zap.core.alerts()

            # Store the alerts in a list
            unique_alerts = {}  # To keep track of unique alerts
            
            # Iterate over the alerts and add unique alerts to the dictionary
            for alert in alerts:
                alert_string = alert.get('alert')
                risk = alert.get('risk')
                solution = alert.get('solution')
                if alert_string not in unique_alerts:
                    unique_alerts[alert_string] = {'risk': risk, 'solution': solution}

            # Stop the OWASP ZAP subprocess
            #zap_process.terminate()
            #zap_process.wait()

            return render_template('scan_url.html', user=current_user, scan_url=scan_url, alerts=unique_alerts)
        except Exception as e:
            error_message = str(e)

            # Stop the OWASP ZAP subprocess
            #zap_process.terminate()
            #zap_process.wait()
            return render_template('scan_url.html', user=current_user, error_message=error_message)
    return render_template('scan_url.html', user=current_user)