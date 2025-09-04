import redis
import json
from app.config import settings

redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def save_job_status(job_id: str, status: dict):
    redis_client.set(job_id, json.dumps(status))

def get_job_status(job_id: str):
    job_json = redis_client.get(job_id)
    if job_json is None:
        return None
    if isinstance(job_json, bytes):
        return job_json.decode()
    return job_json


def get_all_jobs():
    """
    Returns all job IDs in Redis.
    Assumes your job keys are prefixed like 'job:<id>'.
    """
    return [key for key in redis_client.keys("*")]
