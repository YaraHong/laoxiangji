from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.core.config import settings
from app.core.logger_handle import logger

_CONNECTED = False


def _ensure_connection():
    global _CONNECTED
    if not _CONNECTED:
        logger.info("连接 Milvus: %s:%d", settings.milvus.host, settings.milvus.port)
        connections.connect(host=settings.milvus.host, port=settings.milvus.port)
        _CONNECTED = True


def get_collection() -> Collection:
    _ensure_connection()
    name = settings.milvus.collection
    dim = settings.milvus.dim
    if utility.has_collection(name):
        col = Collection(name)
        existing_dim = col.schema.fields[-1].params["dim"]
        if existing_dim != dim:
            logger.warning("集合维度不匹配，删除重建: 已有=%d, 期望=%d", existing_dim, dim)
            utility.drop_collection(name)
        else:
            logger.debug("加载已有 Milvus 集合: %s", name)
            col.load()
            return col

    logger.info("创建新 Milvus 集合: %s, dim=%d", name, settings.milvus.dim)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="doc_id", dtype=DataType.INT64),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=settings.milvus.dim),
    ]
    schema = CollectionSchema(fields, description="老乡鸡知识库")
    col = Collection(name, schema)
    col.create_index(
        field_name="vector",
        index_params={"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 128}},
        index_name="vector_idx",
    )
    col.load()
    return col
