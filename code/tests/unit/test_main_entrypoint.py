from unittest.mock import patch

from test_service.__main__ import main


class TestMainEntrypoint:
    def test_when_main_runs_expect_uvicorn_started_with_asgi_application(self):
        with patch("test_service.__main__.uvicorn.run") as run:
            main()

        run.assert_called_once_with(
            "test_service.main:app",
            host="127.0.0.1",
            port=8000,
            log_level="info",
        )
