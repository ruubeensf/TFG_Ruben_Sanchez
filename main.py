import json
from datetime import datetime

import requests
from flask import Flask, render_template, request, redirect, session, make_response, url_for, jsonify
import base64

app = Flask(__name__)

API_KEY = ''

app.secret_key = API_KEY

# Caché para almacenar los resultados de las llamadas a la API
project_cache = {}


@app.route('/')
def home():
    # Establece el idioma predeterminado en español
    if 'language' not in session:
        session['language'] = 'es'

    # Si el usuario no ha iniciado sesión, le manda a la pagina de inicio de sesion
    if 'logged_in' not in session:
        return render_template('login.html', language=session['language'])
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si el usuario ya ha iniciado sesión, le manda a la pagina de inicio
    if 'logged_in' in session:
        return redirect('/dashboard')
    # Si el usuario no ha iniciado sesión, le manda a la pagina de inicio de sesion
    else:
        email = request.form['email']
        password = request.form['password']

        message = email + ':' + password
        message_bytes = message.encode('utf-8')
        base64_bytes = base64.b64encode(message_bytes)
        base64_str = base64_bytes.decode('utf-8')

        session['credentials'] = base64_str

        headers = {
            'Authorization': 'Basic ' + session['credentials']
        }

        # Enviar solicitud GET a la API de Teamwork para obtener un token de acceso
        response = requests.get('https://beedata.teamwork.com/authenticate.json', headers=headers)

        if response.status_code == 200:
            json_response = response.json()
            session['logged_in'] = 'Si'
            session['firstname'] = json_response['account']['firstname']
            session['lastname'] = json_response['account']['lastname']
            session['userid'] = json_response['account']['userId']
            session['language'] = 'es'
            # Si la solicitud fue exitosa, redirige al usuario a otra página
            return redirect(url_for('dashboard'))
        else:
            # Si la solicitud falló, muestra un mensaje de error al usuario
            error_message = 'Error de inicio de sesión. Por favor, inténtalo de nuevo.'
            return render_template('login.html', error_message=error_message, language=session['language'])


@app.route('/logout')
def logout():
    # Elimina las variables de sesión
    session.clear()
    project_cache.clear()
    response = make_response(redirect('/'))
    response.set_cookie('session', '', expires=0)
    return response


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'logged_in' not in session:
        return render_template('login.html')

    if 'language' not in session:
        session['language'] = 'es'

    headers = {
        'Authorization': 'Basic ' + session['credentials']
    }

    if 'projects' in project_cache:
        projects = project_cache['projects']
    else:
        response = requests.get('https://beedata.teamwork.com/projects.json', headers=headers)
        json_response = response.json()
        projects = json_response['projects']
        project_cache['projects'] = projects

    project_list = []

    for project in projects:
        if 'tasklists' in project:
            tasklistJSON = project['tasklists']
        else:
            project_id = project['id']
            response = requests.get(f'https://beedata.teamwork.com/projects/{project_id}/tasklists.json',
                                    headers=headers)
            tasklist_response = response.json()
            tasklistJSON = tasklist_response['tasklists']
            project['tasklists'] = tasklistJSON

        tasklist_list = []

        for tasklist in tasklistJSON:
            if 'tareas' in tasklist:
                tasks = tasklist['tareas']
            else:
                id_tasklist = tasklist['id']
                response = requests.get(
                    f'https://beedata.teamwork.com/tasklists/{id_tasklist}/tasks.json?responsible-party-ids=0,{session["userid"]}',
                    headers=headers)
                tasks_response = response.json()
                tasks = tasks_response['todo-items']
                tasklist['tareas'] = tasks

            task_list = []
            subtask_list = []

            for task in tasks:
                if task['parentTaskId'] == "":
                    task_list.append({
                        'id': task['id'],
                        'nombre': task['content'],
                        'subtareas': []
                    })
                else:
                    subtask_list.append({
                        'id': task['id'],
                        'nombre': task['content'],
                        'parentTaskId': int(task['parentTaskId'])
                    })

            for task in task_list:
                for subtask in subtask_list:
                    if subtask['parentTaskId'] == task['id']:
                        task['subtareas'].append(subtask)

            tasklist_list.append({
                'id': tasklist['id'],
                'nombre': tasklist['name'],
                'tareas': task_list
            })

        project_list.append({
            'id': project['id'],
            'nombre': project['name'],
            'tasklists': tasklist_list
        })

    error_message = request.args.get('error_message')

    if error_message is None:
        return render_template('dashboard2.html', logged_in=session['logged_in'], firstname=session['firstname'],
                               lastname=session['lastname'], projects=project_list, userid=session['userid'],
                               language=session['language'])
    else:
        return render_template('dashboard2.html', logged_in=session['logged_in'], firstname=session['firstname'],
                               lastname=session['lastname'], projects=project_list, userid=session['userid'],
                               language=session['language'], error_message=error_message)


@app.route('/add_time_entry', methods=['POST'])
def add_time_entry():
    # Si el usuario no ha iniciado sesión, le manda a la pagina de inicio de sesion
    if 'logged_in' not in session:
        return render_template('login.html')

    task_id = request.form['taskId']
    description = request.form['description']
    date_str = request.form['date']
    time = request.form['time']
    hours = request.form['hours']
    minutes = request.form['minutes']
    tags = request.form['tags']

    if tags == '':
        tags = None

    # Convertir la fecha a formato YYYYMMDD
    date_object = datetime.strptime(date_str, '%Y-%m-%d')
    date = date_object.strftime('%Y%m%d')

    payload = {
        'time-entry': {
            'description': description,
            'person-id': session['userid'],
            'date': date,
            'time': time,
            'hours': hours,
            'minutes': minutes,
            'isbillable': 0,
        }
    }

    if tags is not None:
        payload['time-entry']['tags'] = tags

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.post('https://beedata.teamwork.com/tasks/' + task_id + '/time_entries.json', headers=headers,
                             json=payload)

    if response.status_code == 201:
        project_cache.clear()
        return redirect('/dashboard')
    else:
        error_message = 'Error al agregar la entrada de tiempo. Por favor, inténtalo de nuevo.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/task_details/<task_id>', methods=['GET'])
def task_details(task_id):
    # Si el usuario no ha iniciado sesión, le manda a la pagina de inicio de sesion
    if 'logged_in' not in session:
        return render_template('login.html', language='es')

    headers = {
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.get('https://beedata.teamwork.com/tasks/' + task_id + '.json', headers=headers)
    json_response = response.json()
    if response.status_code == 200:
        task = json_response['todo-item']

        start_date = task['start-date']
        due_date = task['due-date']

        if start_date != "":
            start_date = datetime.strptime(start_date, "%Y%m%d")
            start_date = start_date.strftime("%d/%m/%Y")

        if due_date != "":
            due_date = datetime.strptime(due_date, "%Y%m%d")
            due_date = due_date.strftime("%d/%m/%Y")

        response = requests.get('https://beedata.teamwork.com/tasks/' + task_id + '/time_entries.json', headers=headers)
        json_response = response.json()
        time_entries = json_response['time-entries']

        return render_template('task_details.html', task=task, start_date=start_date, due_date=due_date,
                               time_entries=time_entries, language=session['language'])
    else:
        error_message = 'Error al acceder a los detalles de la tarea.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query', '')

    return redirect(url_for('showResults', query=query))


@app.route('/show_results/<query>', methods=['GET'])
def showResults(query):
    # Si el usuario no ha iniciado sesión, le manda a la pagina de inicio de sesion
    if 'logged_in' not in session:
        return render_template('login.html', language=session['language'])

    headers = {
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.get('https://beedata.teamwork.com/tasks.json?search=' + query, headers=headers)
    json_response = response.json()
    tasks = json_response['todo-items']

    # Buscar los elementos que en content contengan el query
    searchedTasks = []

    for task in tasks:
        if query.lower() in task['content'].lower():
            searchedTasks.append(task)

    return render_template('search_results.html', tasks=searchedTasks, query=query, language=session['language'])


@app.route('/change_language', methods=['POST'])
def change_language():
    language_code = request.json.get('language')
    session['language'] = language_code
    return jsonify({'success': True})


@app.route('/create_project', methods=['POST'])
def create_project():
    if 'logged_in' not in session:
        return render_template('login.html')

    project_name = request.form['project_name']
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']

    # Convertir la fecha a formato YYYYMMDD
    start_date_object = datetime.strptime(start_date_str, '%Y-%m-%d')
    start_date = start_date_object.strftime('%Y%m%d')

    end_date_object = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date_object.strftime('%Y%m%d')

    payload = {
        'project': {
            'name': project_name,
            'start-date': start_date,
            'end-date': end_date,
            'use-tasks': "true"
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.post('https://beedata.teamwork.com/projects.json', headers=headers, json=payload)

    if response.status_code == 201:
        project_cache.clear()
        return redirect('/dashboard')
    else:
        error_message = 'Error al crear el proyecto. Por favor, inténtalo de nuevo.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/create_tasklist', methods=['POST'])
def create_tasklist():
    if 'logged_in' not in session:
        return render_template('login.html')

    tasklist_name = request.form['tasklist_name']
    project_id = request.form['project_id']

    payload = {
        'tasklist': {
            'name': tasklist_name
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.post('https://beedata.teamwork.com/projects/' + project_id + '/tasklists.json', headers=headers,
                             json=payload)

    if response.status_code == 201:
        project_cache.clear()
        return redirect('/dashboard')
    else:
        error_message = 'Error al crear la tasklist. Por favor, inténtalo de nuevo.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/create_task', methods=['POST'])
def create_task():
    if 'logged_in' not in session:
        return render_template('login.html')

    task_name = request.form['task_name']
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']
    task_description = request.form['task_description']
    tasklist_id = request.form['tasklist_id']

    # Convertir la fecha a formato YYYYMMDD
    start_date_object = datetime.strptime(start_date_str, '%Y-%m-%d')
    start_date = start_date_object.strftime('%Y%m%d')

    end_date_object = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date_object.strftime('%Y%m%d')

    payload = {
        'todo-item': {
            'use-defaults': 0,
            'completed': 0,
            'content': task_name,
            'responsible-party-id': session['userid'],
            'tasklistId': tasklist_id,
            'start-date': start_date,
            'due-date': end_date,
            'description': task_description
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.post('https://beedata.teamwork.com/tasklists/' + tasklist_id + '/tasks.json', headers=headers,
                             json=payload)

    if response.status_code == 201:
        project_cache.clear()
        return redirect('/dashboard')
    else:
        error_message = 'Error al crear la task. Por favor, inténtalo de nuevo.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/create_subtask', methods=['POST'])
def create_subtask():
    if 'logged_in' not in session:
        return render_template('login.html')

    subtask_name = request.form['subtask_name']
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']
    subtask_description = request.form['subtask_description']
    tags = request.form['tags']
    task_id = request.form['task_id']

    # Convertir la fecha a formato YYYYMMDD
    start_date_object = datetime.strptime(start_date_str, '%Y-%m-%d')
    start_date = start_date_object.strftime('%Y%m%d')

    end_date_object = datetime.strptime(end_date_str, '%Y-%m-%d')
    end_date = end_date_object.strftime('%Y%m%d')

    if tags == '':
        tags = None

    payload = {
        'todo-item': {
            'content': subtask_name,
            'responsible-party-id': session['userid'],
            'start-date': start_date,
            'due-date': end_date,
            'description': subtask_description,
        }
    }

    if tags is not None:
        payload['todo-item']['tags'] = tags

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.post('https://beedata.teamwork.com/tasks/' + task_id + '.json', headers=headers,
                             json=payload)

    if response.status_code == 201:
        project_cache.clear()
        return redirect('/dashboard')
    else:
        error_message = 'Error al crear la subtask. Por favor, inténtalo de nuevo.'
        return redirect('/dashboard?error_message=' + error_message)


@app.route('/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    if 'logged_in' not in session:
        return render_template('login.html')

    headers = {
        'Authorization': 'Basic ' + session['credentials']
    }

    response = requests.delete('https://beedata.teamwork.com/tasks/' + task_id + '.json', headers=headers)

    if response.status_code == 200:
        project_cache.clear()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
