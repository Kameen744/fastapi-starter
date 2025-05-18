from .base_table import BaseTable


class Course(BaseTable, table=True):
  title: str 
  description: str 
  file: str
  tema: str