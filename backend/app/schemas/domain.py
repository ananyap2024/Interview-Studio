from pydantic import BaseModel

from ..domain_config import DomainName


class Domain(BaseModel):
    name: DomainName