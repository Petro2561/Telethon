from dataclasses import dataclass

from environs import Env


@dataclass
class TgBot:
    token: str


@dataclass
class Redis:
    redis_host: str
    redis_port: int
    redis_db: int
    redis_data: str

@dataclass
class Config:
    tg_bot: TgBot
    redis_db: Redis

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(token=env("BOT_TOKEN")),
        redis_db=Redis(
            redis_host=env("REDIS_HOST"),
            redis_port=env("REDIS_PORT"),
            redis_db=env("REDIS_DB"),
            redis_data=env("REDIS_DATA"),
        ),
    )
