from ..db import get_db_connection
from apscheduler.schedulers.background import BackgroundScheduler


def can_call_api(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT monthly_api_used, monthly_api_limit FROM usuarios WHERE id = %s', (int(user_id),))
    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return False
    print(user['monthly_api_limit'])

    return user["monthly_api_used"] < user['monthly_api_limit']


def oncrement_api_usage(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET monthly_api_used = monthly_api_used + 1 WHERE id = %s', (user_id,))
    conn.commit()
    cursor.close()
    conn.close()

def log_api_usage(user_id, api_name, status='success'):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO api_usage (user_id, api_name, statur) VALUES (%s, %s, %s)',(user_id, api_name, status))
    conn.commit()
    cursor.close()
    conn.close()


'''def reset_api_usage():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET monthly_api_used = 0')
    conn.commit()
    cursor.close()
    conn.close()

scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_api_usage, trigger='cron', day=1, hour =0 )
scheduler.start()'''



