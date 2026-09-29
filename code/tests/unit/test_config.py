from test_service.config import PostgresDatabaseSettings


class TestPostgresDatabaseSettings:
    def test_when_settings_are_explicit_expect_async_postgresql_url(self):
        settings = PostgresDatabaseSettings(
            host="database.example.com",
            port=5433,
            name="catalog",
            user="service-user",
            password="password",
        )

        url = settings.connection_url.render_as_string(hide_password=False)

        assert url == "postgresql+asyncpg://service-user:password@database.example.com:5433/catalog"

    def test_when_environment_variables_are_present_expect_values_override_env_file(
        self, monkeypatch
    ):
        monkeypatch.setenv("DATABASE_HOST", "environment.example.com")
        monkeypatch.setenv("DATABASE_PORT", "15432")
        monkeypatch.setenv("DATABASE_NAME", "environment_catalog")
        monkeypatch.setenv("DATABASE_USER", "environment-user")
        monkeypatch.setenv("DATABASE_PASSWORD", "environment-password")

        settings = PostgresDatabaseSettings()

        assert settings.host == "environment.example.com"
        assert settings.port == 15432
        assert settings.name == "environment_catalog"
        assert settings.user == "environment-user"
        assert settings.password.get_secret_value() == "environment-password"
