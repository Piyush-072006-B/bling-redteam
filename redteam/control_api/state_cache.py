import json
# pyrefly: ignore [missing-import]
import redis
import os
# pyrefly: ignore [missing-import]
import structlog
from typing import Dict, Any, List

log = structlog.get_logger()

class GraphStateCache:
    def __init__(self):
        self.use_redis = False
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self._memory_cache = {
            "nodes": {},
            "links": {},
            "metrics": {},
            "lineage": []
        }
        try:
            self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
            self.redis.ping()
            self.use_redis = True
            log.info("State cache connected to Redis.")
        except Exception as e:
            log.warning(f"Redis unavailable, using in-memory cache: {e}")

    def update_node(self, node_id: str, data: Dict[str, Any]):
        if self.use_redis:
            self.redis.hset("graph:nodes", node_id, json.dumps(data))
        else:
            self._memory_cache["nodes"][node_id] = data

    def update_link(self, link_id: str, data: Dict[str, Any]):
        if self.use_redis:
            self.redis.hset("graph:links", link_id, json.dumps(data))
        else:
            self._memory_cache["links"][link_id] = data

    def update_metrics(self, metrics: Dict[str, Any]):
        if self.use_redis:
            self.redis.set("graph:metrics", json.dumps(metrics))
        else:
            self._memory_cache["metrics"] = metrics

    def add_lineage(self, event: Dict[str, Any]):
        if self.use_redis:
            self.redis.rpush("graph:lineage", json.dumps(event))
        else:
            self._memory_cache["lineage"].append(event)

    def get_full_state(self) -> Dict[str, Any]:
        if self.use_redis:
            nodes = {k: json.loads(v) for k, v in self.redis.hgetall("graph:nodes").items()}
            links = {k: json.loads(v) for k, v in self.redis.hgetall("graph:links").items()}
            metrics_raw = self.redis.get("graph:metrics")
            metrics = json.loads(metrics_raw) if metrics_raw else {}
            lineage_raw = self.redis.lrange("graph:lineage", 0, -1)
            lineage = [json.loads(x) for x in lineage_raw]
            return {"nodes": list(nodes.values()), "links": list(links.values()), "metrics": metrics, "lineage": lineage}
        else:
            return {
                "nodes": list(self._memory_cache["nodes"].values()),
                "links": list(self._memory_cache["links"].values()),
                "metrics": self._memory_cache["metrics"],
                "lineage": self._memory_cache["lineage"]
            }

    def clear(self):
        if self.use_redis:
            self.redis.delete("graph:nodes", "graph:links", "graph:metrics", "graph:lineage")
        else:
            self._memory_cache = {"nodes": {}, "links": {}, "metrics": {}, "lineage": []}
