import os
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, join_room, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

rooms = {}  # имя_комнаты -> список sid участников

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@socketio.on("join")
def on_join(data):
    room = data["room"]
    join_room(room)
    members = rooms.setdefault(room, [])
    if len(members) >= 2:
        emit("full", {})
        return
    members.append(request.sid)
    if len(members) == 2:
        # второй вошедший инициирует звонок
        emit("ready", {"initiator": True}, to=request.sid)
        emit("ready", {"initiator": False}, to=members[0])
        print(f"[{room}] Звонок начался")

@socketio.on("signal")
def on_signal(data):
    # пересылаем SDP/ICE второму участнику
    emit("signal", data["payload"], to=data["room"], include_self=False)

@socketio.on("disconnect")
def on_disconnect():
    for room, members in list(rooms.items()):
        if request.sid in members:
            members.remove(request.sid)
            emit("peer-left", {}, to=room)
            print(f"[{room}] Участник вышел, осталось {len(members)}")
            if not members:
                del rooms[room]

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Сервер запущен на порту {port}")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True)