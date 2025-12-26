import redis
from rq import Queue
from app.core.config import settings


class RedisClient:
    """Singleton Redis client and RQ queue manager."""
    
    _instance = None
    _redis_conn = None
    _queue = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def connect(self) -> None:
        """Establish Redis connection."""
        if self._redis_conn is None:
            self._redis_conn = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False
            )
    
    def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis_conn:
            self._redis_conn.close()
            self._redis_conn = None
            self._queue = None
    
    @property
    def connection(self) -> redis.Redis:
        """Get Redis connection, connecting if necessary."""
        if self._redis_conn is None:
            self.connect()
        return self._redis_conn
    
    @property
    def queue(self) -> Queue:
        """Get or create the default RQ queue."""
        if self._queue is None:
            self._queue = Queue(
                "default",
                connection=self.connection,
                default_timeout=settings.JOB_TIMEOUT
            )
        return self._queue
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and responding."""
        try:
            self.connection.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            return False


# Global singleton instance
redis_client = RedisClient()


def get_redis_client() -> RedisClient:
    """Dependency injection helper for Redis client."""
    return redis_client
