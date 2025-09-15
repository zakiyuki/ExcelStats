from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float

USER_NAME = "root"
PASSWORD = "yuki"
HOST = "localhost:3306"
DATABASE = "mydatabase"

# url = 'mysql+pymysql://root:password@host/database?charset=utf8'
url = "mysql+pymysql://{}:{}@{}/{}?charset=utf8".format(
    USER_NAME, PASSWORD, HOST, DATABASE
)
# Base.metadata.create_all(bind=engine)

# エンジン設定：mysql+pymysqlを使用
engine = create_engine(url, pool_recycle=10)
Base = declarative_base()

# Sessionの作成
session =  scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine
    )
)

# modelで使用する
Base = declarative_base()
Base.query = session.query_property()


# テーブルを定義する
# Baseを継承
