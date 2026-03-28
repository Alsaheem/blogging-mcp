import pytest

from blogging_mcp.config import Settings


@pytest.fixture
def settings_both() -> Settings:
    return Settings(
        devto_api_key="devto-test-key",
        hashnode_token="hn-test-token",
        hashnode_publication_host="writer.hashnode.dev",
    )
