from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry

@compiles(Geometry, 'sqlite')
def compile_geometry_sqlite(type_, compiler, **kw):
    return 'TEXT'

from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr
import re

@as_declarative()
class Base:
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically (e.g. InfrastructureAsset -> infrastructure_assets)
    @declared_attr
    def __tablename__(cls) -> str:
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower() + "s"
