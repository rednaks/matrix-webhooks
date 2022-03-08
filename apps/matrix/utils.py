from apps.types import MatrixConfig
from constance import config


def get_matrix_config() -> MatrixConfig:
    return MatrixConfig(homeserver=config.MATRIX_HOMESERVER,
                        user_id=config.MATRIX_BOT_USERNAME,
                        access_token=config.MATRIX_BOT_TOKEN)
