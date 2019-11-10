from flask import Flask, render_template, request, jsonify, abort, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sys

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost:5432/todoApp'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)

class TodoList(db.Model):
    __tablename__ = 'todolists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    todos = db.relationship('Todo', backref='list', cascade='all, delete-orphan', lazy=True)

class Todo(db.Model):
    __tablename__ = 'todos'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False, default=1)

    def __repr__(self):
        return f'<Todo {self.id} {self.description}>'


# Todo routes
@app.route('/todos/create', methods=['POST'])
def create_todo():
    body = {}
    error = False
    try:
        description = request.get_json()['description']
        todo = Todo(description = description)
        db.session.add(todo)
        db.session.commit()
        body['description'] = todo.description
        body['id'] = todo.id
        body['list_id'] = todo.list_id
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify(body)

@app.route('/todos/<todo_id>/set-completed', methods=['POST'])
def set_completed_todo(todo_id):
    try:
        completed = request.get_json()['completed']
        todo = Todo.query.get(todo_id)
        todo.completed = completed
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    # return redirect(url_for('get_list_todos'))
    return jsonify({'success': True})

@app.route('/todos/<todo_id>/delete', methods=['DELETE'])
def delete_todo(todo_id):
    try:
        Todo.query.filter_by(id=todo_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    # return redirect(url_for('get_list_todos'))
    return jsonify({'success': True})


@app.route('/lists/<list_id>')
def get_list_todos(list_id):
    return render_template('index.html',
    lists = TodoList.query.order_by('id').all(),
    active_list = TodoList.query.get(list_id),
    todos = Todo.query.filter_by(list_id = list_id).order_by('id').all())

@app.route('/')
def index():
    return redirect(url_for('get_list_todos', list_id=1))


# Todo List routes
@app.route('/lists', methods=['POST'])
def create_list():
    body = {}
    try:
        name = request.get_json()['name']
        todo_list = TodoList(name = name)
        db.session.add(todo_list)
        db.session.commit()
        body['name'] = todo_list.name
        body['id'] = todo_list.id
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify(body)

@app.route('/lists/<list_id>/complete', methods=['POST'])
def complete_list(list_id):
    body = { 'completed': False }
    try:
        completed = request.get_json()['completed']
        todolist = TodoList.query.get(list_id)
        todos = todolist.todos
        for todo in todos:
            todo.completed = completed
        if completed:
            todos.completed = True
            body.update({'completed': completed})
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return jsonify(body)

@app.route('/lists/<list_id>/delete', methods=['DELETE'])
def delete_list(list_id):
    try:
        todolist = TodoList.query.filter_by(id=list_id).first()
        db.session.delete(todolist)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return jsonify({ 'success': True })

if '__main__':
    app.run()
