import time


class SessionManager:
    def __init__(self):
        self.current_session = None
        self.current_session_id = None
        self.current_user_id = None
        self.frames_buffer = []
        self.accuracy = 0.6

    def start_session(self, user_id, session_id):
        self.current_user_id = user_id
        self.current_session_id = session_id
        self.current_session = {
            "user_id": user_id,
            "session_id": session_id,
            "start_time": time.time(),
            "frames": []
        }
        self.frames_buffer = []

    def add_frame_data(self, keypoints, angle=None, status=None, score=0):
        if self.current_session is None:
            return

        frame_data = {
            "timestamp": time.time(),
            "keypoints": keypoints,
            "angle": angle,
            "status": status,
            "score": score
        }
        self.frames_buffer.append(frame_data)
        self.current_session["frames"].append(frame_data)

    def get_buffer(self):
        return self.frames_buffer

    def clear_buffer(self):
        self.frames_buffer = []

    def stop_session(self):
        result = {
            "session_id": self.current_session_id,
            "frames": self.current_session["frames"] if self.current_session else []
        }
        self.current_session = None
        self.current_session_id = None
        self.current_user_id = None
        return result
