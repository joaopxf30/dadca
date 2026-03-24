import logging

from typing import Any

from pydantic import BaseModel, ConfigDict

from src.dadca.domain.sender import Sender


class DefaultMessage(BaseModel):
    package_count: int
    sender: Sender

    model_config = ConfigDict(frozen=True)

