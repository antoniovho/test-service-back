from test_service.main import create_app


class TestCreateApp:
    def test_when_application_is_created_expect_contract_metadata(self) -> None:
        application = create_app()

        assert application.title == "Test Service"
        assert application.version == "0.1.0"
