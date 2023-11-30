import logging
from .screenView import ScreenAPIView

logger = logging.getLogger('backend')

class DynamicAPIView(ScreenAPIView):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    