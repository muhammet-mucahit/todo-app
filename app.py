from flask import Flask, request, render_template, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import sys
from flask_migrate import Migrate

app = Flask(__name__)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = "<dialect>://<username>@<host>:<port>/<database>"
db = SQLAlchemy(app)

migrate = Migrate(app, db)


class TodoList(db.Model):
    __tablename__ = "todolists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    todos = db.relationship(
        "Todo",
        cascade="all, delete-orphan",
        backref=db.backref("list", single_parent=True, cascade="all,delete-orphan"),
        lazy=True,
    )

    def __repr__(self):
        return f"<Todo {self.id} {self.name}>"


class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(), nullable=False)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    list_id = db.Column(
        db.Integer, db.ForeignKey("todolists.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self):
        return f"<Todo {self.id} {self.description}>"


@app.route("/todos", methods=["POST"])
def create():
    error = False
    body = {}
    try:
        desc = request.get_json()["description"]
        list_id = request.get_json()["list_id"]
        todo = Todo(description=desc)
        active_list = TodoList.query.get(list_id)
        todo.list = active_list
        db.session.add(todo)
        db.session.commit()
        body["id"] = todo.id
        body["description"] = todo.description
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route("/lists", methods=["POST"])
def create_list():
    error = False
    body = {}
    try:
        name = request.get_json()["name"]
        todo_list = TodoList(name=name)
        db.session.add(todo_list)
        db.session.commit()
        body["id"] = todo_list.id
        body["name"] = todo_list.name
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    if error:
        abort(400)
    else:
        return jsonify(body)


@app.route("/lists/<list_id>", methods=["PUT", "DELETE"])
def update_list(list_id):
    if request.method == "PUT":
        try:
            completed = request.get_json()["completed"]
            todolist = TodoList.query.get(list_id)
            todolist.completed = completed

            todos = Todo.query.filter_by(list_id=list_id).all()
            for todo in todos:
                todo.completed = completed
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
    elif request.method == "DELETE":
        try:
            TodoList.query.filter_by(id=list_id).delete()
            db.session.commit()
        except:
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()
    return jsonify({"success": True})


@app.route("/todos/<todo_id>", methods=["PUT", "DELETE"])
def update(todo_id):
    if request.method == "PUT":
        try:
            completed = request.get_json()["completed"]
            todo = Todo.query.get(todo_id)
            todo.completed = completed
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
    elif request.method == "DELETE":
        try:
            Todo.query.filter_by(id=todo_id).delete()
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
    return jsonify({"success": True})


@app.route("/lists/<list_id>")
def get_todo_lists(list_id):
    return render_template(
        "index.html",
        todos=Todo.query.filter_by(list_id=list_id).order_by("id").all(),
        active_list=TodoList.query.get(list_id),
        lists=TodoList.query.order_by("id").all(),
    )


@app.route("/")
def index():
    return redirect(url_for("get_todo_lists", list_id=1))


if __name__ == "__main__":
    app.debug = True
    app.run()
