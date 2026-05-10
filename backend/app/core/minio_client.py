from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.core.logger_handle import logger

_client: Minio | None = None


def get_minio() -> Minio:
    global _client
    if _client is None:
        logger.info("连接 MinIO: %s, bucket=%s", settings.minio.endpoint, settings.minio.bucket)
        _client = Minio(
            settings.minio.endpoint,
            access_key=settings.minio.access_key,
            secret_key=settings.minio.secret_key,
            secure=settings.minio.secure,
        )
        _ensure_bucket(_client)
    return _client


def _ensure_bucket(client: Minio) -> None:
    if not client.bucket_exists(settings.minio.bucket):
        client.make_bucket(settings.minio.bucket)
        logger.info("创建 MinIO bucket: %s", settings.minio.bucket)


def upload_file(object_name: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    client = get_minio()
    client.put_object(
        settings.minio.bucket,
        object_name,
        BytesIO(data),
        length=len(data),
        content_type=content_type,
    )
    logger.info("文件上传到 MinIO: %s, size=%d", object_name, len(data))


def download_file(object_name: str) -> bytes:
    client = get_minio()
    try:
        response = client.get_object(settings.minio.bucket, object_name)
        data = response.read()
        response.close()
        response.release_conn()
        return data
    except S3Error:
        logger.warning("MinIO 文件不存在: %s", object_name)
        raise FileNotFoundError(f"文件不存在: {object_name}")


def delete_file(object_name: str) -> None:
    client = get_minio()
    try:
        client.remove_object(settings.minio.bucket, object_name)
        logger.info("MinIO 文件已删除: %s", object_name)
    except S3Error:
        logger.warning("删除 MinIO 文件失败(可能不存在): %s", object_name)
