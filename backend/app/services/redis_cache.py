import json

from app.core.redis import get_redis

MESSAGES_KEY = "chat:session:{session_id}:messages"
SUMMARY_KEY = "chat:session:{session_id}:summary"
PROFILE_HINT_KEY = "chat:session:{session_id}:profile_hint"
MAX_ROUNDS = 10
MAX_MESSAGES = MAX_ROUNDS * 2
TTL = 86400


async def _r() -> "aioredis.Redis":
    return await get_redis()


def _msg_key(session_id: int) -> str:
    return MESSAGES_KEY.format(session_id=session_id)


def _sum_key(session_id: int) -> str:
    return SUMMARY_KEY.format(session_id=session_id)


def _serialize_message(msg) -> dict:
    meta = msg.message_metadata or {}
    return {
        "id": msg.id,
        "session_id": msg.session_id,
        "role": msg.role,
        "content": msg.content,
        "message_type": msg.message_type,
        "citations": meta.get("citations", []),
        "created_at": msg.created_at.isoformat(),
    }


async def push_message(session_id: int, msg) -> None:
    r = await _r()
    key = _msg_key(session_id)
    data = json.dumps(_serialize_message(msg), ensure_ascii=False)
    await r.rpush(key, data)
    await r.ltrim(key, -MAX_MESSAGES, -1)
    await r.expire(key, TTL)


async def get_messages(session_id: int) -> list[dict]:
    r = await _r()
    key = _msg_key(session_id)
    raw = await r.lrange(key, 0, -1)
    if not raw:
        return []
    return [json.loads(item) for item in raw]


async def set_summary(session_id: int, summary: str) -> None:
    r = await _r()
    key = _sum_key(session_id)
    await r.set(key, summary, ex=TTL)


async def get_summary(session_id: int) -> str | None:
    r = await _r()
    key = _sum_key(session_id)
    return await r.get(key)


async def delete_session(session_id: int) -> None:
    r = await _r()
    await r.delete(_msg_key(session_id), _sum_key(session_id))


def _profile_key(session_id: int) -> str:
    return PROFILE_HINT_KEY.format(session_id=session_id)


async def set_profile_hint(session_id: int, profile: dict) -> None:
    """缓存客户特征提取结果"""
    r = await _r()
    key = _profile_key(session_id)
    await r.set(key, json.dumps(profile, ensure_ascii=False), ex=TTL)


async def get_profile_hint(session_id: int) -> dict | None:
    """获取缓存的客户特征"""
    r = await _r()
    key = _profile_key(session_id)
    raw = await r.get(key)
    if raw:
        return json.loads(raw)
    return None


async def delete_profile_hint(session_id: int) -> None:
    """删除客户特征缓存"""
    r = await _r()
    await r.delete(_profile_key(session_id))
