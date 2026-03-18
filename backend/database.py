"""
数据库配置和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 数据库路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'hi_tom_ai.db')}"

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 需要这个参数
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized")