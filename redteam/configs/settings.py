# ============================================================
# Global Settings
# ============================================================
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Kafka
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:29092")

    # Redis
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_db: int = int(os.getenv("REDIS_DB", "0"))

    # PostgreSQL
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://redteam:redteam_secure_2026@localhost:5432/bling_redteam"
    )

    # Generator
    default_account_pool_size: int = int(os.getenv("DEFAULT_ACCOUNT_POOL_SIZE", "1000"))
    default_tps: float = float(os.getenv("DEFAULT_TPS", "5"))
    default_attack_depth: int = int(os.getenv("DEFAULT_ATTACK_DEPTH", "6"))
    default_mutation_rate: float = float(os.getenv("DEFAULT_MUTATION_RATE", "0.3"))
    simulation_mode: str = os.getenv("SIMULATION_MODE", "sandbox")

    # Graph Engine
    graph_max_nodes: int = int(os.getenv("GRAPH_MAX_NODES", "50000"))
    cycle_detection_depth: int = int(os.getenv("CYCLE_DETECTION_DEPTH", "10"))
    centrality_top_n: int = int(os.getenv("CENTRALITY_TOP_N", "20"))

    # Detector
    isolation_forest_contamination: float = float(
        os.getenv("ISOLATION_FOREST_CONTAMINATION", "0.1")
    )
    velocity_window_seconds: int = int(os.getenv("VELOCITY_WINDOW_SECONDS", "300"))
    structuring_threshold: float = float(os.getenv("STRUCTURING_THRESHOLD", "10000.0"))
    high_centrality_threshold: float = float(
        os.getenv("HIGH_CENTRALITY_THRESHOLD", "0.7")
    )

    # Mutator
    mutation_trigger_threshold: float = float(
        os.getenv("MUTATION_TRIGGER_THRESHOLD", "0.5")
    )
    max_mutation_generations: int = int(os.getenv("MAX_MUTATION_GENERATIONS", "20"))

    # Simulation Runner
    loop_interval_seconds: float = float(os.getenv("LOOP_INTERVAL_SECONDS", "10"))
    max_loop_iterations: int = int(os.getenv("MAX_LOOP_ITERATIONS", "100"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
