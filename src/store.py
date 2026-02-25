import threading
from models import User, Recording 

class Store: 
    def __init__(self):
        self._users: dict[str, User] = {}
        self._recordings: dict[str, Recording] = {}
        self._user_locks: dict[str, threading.Lock] = {}
        self._recording_lock = threading.Lock()
        self._meta_lock = threading.Lock()

    def get_or_create_user(self, user_id: str) -> User:
        with self._meta_lock:
            if user_id not in self._users:
                self._users[user_id] = User(id=user_id)
            return self._users[user_id]

    def get_user(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_recording(self, recording_id: str) -> Recording | None:
        return self._recordings.get(recording_id)

    def set_recording(self, recording: Recording) -> None:
        self._recordings[recording.id] = recording

    def get_user_lock(self, user_id: str) -> threading.Lock:
        with self._meta_lock:
            if user_id not in self._user_locks:
                self._user_locks[user_id] = threading.Lock()
            return self._user_locks[user_id]

    def get_recording_lock(self, recording_id: str) -> threading.Lock:
        with self._meta_lock:
            if recording_id not in self._recording_locks:
                self._recording_locks[recording_id] = threading.Lock()
            return self._recording_locks[recording_id]

    def reset(self):
        with self._meta_lock:
            self._users.clear()
            self._recordings.clear()
            self._user_locks.clear()
            self._recording_locks.clear()

store = Store()