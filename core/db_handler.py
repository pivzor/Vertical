import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime, timezone
import hashlib
import logging
from utils.resource_path import resource_path

logging.basicConfig(level=logging.INFO, filename=resource_path("app.log"))
logger = logging.getLogger(__name__)

class DBHandler:
    def __init__(self, dbname="pose_db", user="postgres", password="12345678",
                 host="localhost", port=5432):
        self.conn_params = {
            'dbname': dbname,
            'user': user,
            'password': password,
            'host': host,
            'port': port
        }
        self.connection = None

    def connect(self):
        try:
            self.connection = psycopg2.connect(**self.conn_params)
            logger.info("Connected to database")
        except psycopg2.Error as e:
            logger.error(f"DB connection error: {e}")
            raise

    def close(self):
        if self.connection:
            self.connection.close()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register_user(self, username, password, email):
        """Регистрация нового пользователя"""
        try:
            cursor = self.connection.cursor()
            hashed_pw = self.hash_password(password)
            cursor.execute(
                'INSERT INTO "user" (username, password, email, roleid) VALUES (%s, %s, %s, 1) RETURNING userid',
                (username, hashed_pw, email)
            )
            user_id = cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"User {username} registered")
            return user_id
        except psycopg2.IntegrityError:
            self.connection.rollback()
            logger.warning(f"User {username} already exists")
            return None
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Register error: {e}")
            return None

    def authenticate_user(self, username, password):
        """Аутентификация пользователя"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            hashed_pw = self.hash_password(password)
            cursor.execute(
                'SELECT userid, username FROM "user" WHERE username = %s AND password = %s',
                (username, hashed_pw)
            )
            result = cursor.fetchone()
            if result:
                logger.info(f"User {username} authenticated")
            return result
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return None

    def start_session(self, user_id):
        """Начало сессии"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'INSERT INTO session (userid, status) VALUES (%s, %s) RETURNING sessionid',
                (user_id, 'active')
            )
            session_id = cursor.fetchone()[0]
            self.connection.commit()
            logger.info(f"Session {session_id} started for user {user_id}")
            return session_id
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Start session error: {e}")
            return None

    def add_pose_data(self, session_id, neck_angle, posture_status, keypoints):
        try:
            cursor = self.connection.cursor()
            keypoints_json = json.dumps(keypoints)

            cursor.execute(
                'INSERT INTO posedata (sessionid, "timestamp", neck_angle, posture_status, keypoints) '
                'VALUES (%s, %s, %s, %s, %s)',
                (
                    session_id,
                    datetime.now(timezone.utc),
                    neck_angle,
                    posture_status,
                    keypoints_json
                )
            )
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            print("DB ERROR:", e)

    def end_session(self, session_id):
        """Завершение сессии"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'UPDATE session SET endtime = %s, status = %s WHERE sessionid = %s',
                (datetime.now(), 'completed', session_id)
            )
            self.connection.commit()
            logger.info(f"Session {session_id} ended")
            return True
        except Exception as e:
            self.connection.rollback()
            logger.error(f"End session error: {e}")
            return False

    def get_session_data(self, session_id):
        """Получение всех данных поз для сессии"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                'SELECT * FROM posedata WHERE sessionid = %s ORDER BY "timestamp"',
                (session_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Get session data error: {e}")
            return []

    def create_report(self, session_id, summary, pdf_path, good_posture_percent):
        """Создание отчёта по сессии"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                'INSERT INTO report (sessionid, summary, pdfpath, good_posture_percent) '
                'VALUES (%s, %s, %s, %s)',
                (session_id, summary, pdf_path, good_posture_percent)
            )
            self.connection.commit()
            logger.info(f"Report created for session {session_id}")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Create report error: {e}")

    def get_user_sessions(self, user_id):
        """Получение всех сессий пользователя"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                'SELECT * FROM session WHERE userid = %s ORDER BY starttime DESC',
                (user_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Get user sessions error: {e}")
            return []

    def get_report(self, session_id):
        """Получение отчёта по сессии"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute('SELECT * FROM report WHERE sessionid = %s', (session_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get report error: {e}")
            return None

    def save_daily_score(self, user_id, score):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO daily_stats (userid, score, date)
            VALUES (%s, %s, CURRENT_DATE)
        """, (user_id, score))
        self.connection.commit()

    def add_log(self, user_id, message):
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO logs (user_id, message)
            VALUES (%s, %s)
        """, (user_id, message))
        self.connection.commit()

    def get_sessions_stats(self, user_id, period):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)

        interval_map = {
            "day": "1 day",
            "week": "7 days",
            "month": "1 month",
            "year": "1 year"
        }

        cursor.execute(f"""
            SELECT 
                s.sessionid,
                s.starttime,
                AVG(100 - pd.neck_angle * 2) as avg_score,
                COUNT(pd.poseid) as total_frames
            FROM session s
            JOIN posedata pd ON s.sessionid = pd.sessionid
            WHERE s.userid = %s
            AND s.starttime >= NOW() - INTERVAL %s
            AND s.status = 'completed'
            GROUP BY s.sessionid, s.starttime
            ORDER BY s.starttime
        """, (user_id, interval_map[period]))

        return cursor.fetchall()

    def get_pose_data(self, session_id):
        """Получение данных поз для сессии"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT timestamp, neck_angle, posture_status, keypoints
                FROM posedata
                WHERE sessionid = %s
                ORDER BY timestamp
            """, (session_id,))

            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Get pose data error: {e}")
            return []

    def get_user_by_id(self, user_id):
        """Получение информации о пользователе по ID"""
        try:
            cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                'SELECT userid, username, email, created_at FROM "user" WHERE userid = %s',
                (user_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Get user by id error: {e}")
            return None
        
    def init_db():
        try:
            conn = psycopg2.connect(
                dbname="pose_db",
                user="postgres",
                password="12345678",
                host="localhost",
                port=5432
            )

            cursor = conn.cursor()

            from utils.resource_path import resource_path

            with open(resource_path("database/init.sql"), "r", encoding="utf-8") as f:
                cursor.execute(f.read())

            conn.commit()

            cursor.close()
            conn.close()

            print("DB INIT SUCCESS")

        except Exception as e:
            print("DB INIT ERROR:", e)