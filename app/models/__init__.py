from .category import Category
from .products import Product

from sqlalchemy.schema import CreateTable

print(CreateTable(Product.__table__))