"""Neon configuration contracts, without connecting or reading an .env file."""
from app.core.config import Settings


def test_pooler_url_has_direct_ddl_and_ssl():
    config = Settings(_env_file=None,
        DATABASE_URL='postgresql+psycopg2://demo:fixture@ep-example-pooler.eu.neon.tech/insoft',
        DATABASE_URL_DDL='', SECRET_KEY='fixture-only-for-unit-test', DEV_AUTH_ENABLED=False,
        SEED_MODE='if_empty')
    assert '-pooler.' not in config.database_ddl_url
    assert config.database_ssl_args == {'sslmode': 'require'}
    assert config.seed_mode_efectivo == 'if_empty'


def test_explicit_ddl_url_is_preserved():
    direct = 'postgresql+psycopg2://demo:fixture@ep-direct.eu.neon.tech/insoft'
    config = Settings(_env_file=None,
        DATABASE_URL='postgresql+psycopg2://demo:fixture@ep-example-pooler.eu.neon.tech/insoft',
        DATABASE_URL_DDL=direct, SECRET_KEY='fixture-only-for-unit-test', DEV_AUTH_ENABLED=False)
    assert config.database_ddl_url == direct
