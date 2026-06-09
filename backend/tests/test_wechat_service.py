import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from app.services.wechat_service import get_miniprogram_state


class MiniprogramStateTest(unittest.TestCase):
    def test_defaults_to_formal(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_miniprogram_state(), "formal")

    def test_normalizes_configured_state(self):
        with patch.dict(os.environ, {"WECHAT_MINIPROGRAM_STATE": " FORMAL "}):
            self.assertEqual(get_miniprogram_state(), "formal")

    def test_rejects_invalid_state(self):
        with patch.dict(os.environ, {"WECHAT_MINIPROGRAM_STATE": "production"}):
            with self.assertRaises(HTTPException):
                get_miniprogram_state()


if __name__ == "__main__":
    unittest.main()
