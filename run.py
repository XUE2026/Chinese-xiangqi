import os
import sqlite3
import sys
from app.utils.file_flags import check_kill_flag, check_purge_flag, check_retain_flag, remove_purge_flag, remove_retain_flag

DB_PATH = os.path.join(os.path.dirname(__file__), "chess_platform.db")

def main():
    if check_kill_flag():
        print("系统紧急制动，请联系管理员删除.kill_flag")
        sys.exit(1)
    if check_purge_flag():
        print("检测到 PURGE_NOW.flag，正在清理数据...")
        if os.path.exists(DB_PATH):
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM user_sessions")
                cursor.execute("DELETE FROM temp_credentials")
                cursor.execute("UPDATE games SET is_deleted = 1 WHERE is_deleted = 0")
                conn.commit()
                conn.close()
                print("数据清理完成")
            except Exception as e:
                print(f"清理数据时出错: {e}")
        remove_purge_flag()
        print("PURGE_NOW.flag 已移除")
    if check_retain_flag():
        print("检测到 RETAIN_DATA.flag，保留数据...")
        remove_retain_flag()
        print("RETAIN_DATA.flag 已移除")
    import uvicorn
    from app import config
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=False)

if __name__ == "__main__":
    main()
