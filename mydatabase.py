from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from dbAccessor import Base, engine


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column("id", Integer, primary_key=True, nullable=False)
    file_hash = Column("file_hash", String(128), nullable=False, unique=True)
    created_at = Column("created_at", DateTime, nullable=False, default=datetime.utcnow)
    name = Column("name", String(128), nullable=True)

    files = relationship("Files", back_populates="dataset", cascade="all, delete-orphan")


class Files(Base):
    __tablename__ = "files"

    id = Column("id", Integer, primary_key=True, nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    time_code = Column("time_code", String(45), nullable=False)
    age = Column("age", String(45), nullable=False)
    total = Column("total", Integer, nullable=False)
    male = Column("male", Integer, nullable=False)
    female = Column("female", Integer, nullable=False)

    dataset = relationship("Dataset", back_populates="files")

    def __init__(self, time_code=None, age=None, total=None, male=None, female=None, dataset_id=None):
        self.time_code = time_code
        self.age = age
        self.total = total
        self.male = male
        self.female = female
        self.dataset_id = dataset_id


Base.metadata.create_all(bind=engine)