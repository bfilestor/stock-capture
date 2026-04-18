"""本地 Umi-OCR 连通性测试脚本。"""

from __future__ import annotations

import argparse
import base64
import json
import logging
from pathlib import Path
from typing import Any

import httpx


LOGGER = logging.getLogger("umi_ocr_smoke_test")


def setup_logging(debug: bool) -> None:
    """初始化日志配置，便于排查请求细节。"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def find_latest_capture(capture_dir: Path) -> Path:
    """从截图目录中选择最新图片作为测试输入。"""
    if not capture_dir.exists():
        raise FileNotFoundError(f"截图目录不存在: {capture_dir}")
    candidates = sorted(
        [
            path
            for path in capture_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp"}
        ],
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"截图目录中未找到图片文件: {capture_dir}")
    return candidates[0]


def image_to_base64(image_path: Path) -> str:
    """将图片内容转换为 base64 字符串。"""
    data = image_path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


def build_payload(image_base64: str, data_format: str, parser: str) -> dict[str, Any]:
    """组装 Umi-OCR 请求体。"""
    return {
        "base64": image_base64,
        "options": {
            "data.format": data_format,
            "tbpu.parser": parser,
        },
    }


def extract_ocr_text(response_json: dict[str, Any]) -> str:
    """从 Umi-OCR 返回体提取识别文本。"""
    code = int(response_json.get("code", -1))
    if code != 100:
        raise RuntimeError(f"OCR 返回码异常: {code}, body={response_json}")
    data_field = response_json.get("data")
    if isinstance(data_field, str):
        return data_field.strip()
    if isinstance(data_field, dict):
        return str(data_field.get("text", "")).strip()
    return ""


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="Umi-OCR 本地连通性测试脚本")
    parser.add_argument("--image", type=str, default="", help="待识别图片路径；为空时自动读取 runtime/captures 最新图片")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:1224", help="Umi-OCR 基础地址")
    parser.add_argument("--timeout", type=float, default=45.0, help="请求超时秒数")
    parser.add_argument("--data-format", type=str, default="text", help="Umi-OCR data.format 配置")
    parser.add_argument("--parser", type=str, default="single_line", help="Umi-OCR tbpu.parser 配置")
    parser.add_argument("--print-json", action="store_true", help="打印完整 OCR 返回 JSON")
    parser.add_argument("--debug", action="store_true", help="开启 DEBUG 日志")
    return parser.parse_args()


def main() -> int:
    """执行连通性测试并输出结果。"""
    args = parse_args()
    setup_logging(args.debug)

    try:
        image_path = Path(args.image).expanduser().resolve() if args.image else find_latest_capture(Path("runtime/captures").resolve())
    except Exception as exc:
        LOGGER.error("准备测试图片失败: %s", exc)
        return 1

    if not image_path.exists():
        LOGGER.error("测试图片不存在: %s", image_path)
        return 1

    url = f"{args.url.rstrip('/')}/api/ocr"
    LOGGER.info("开始测试 Umi-OCR，url=%s", url)
    LOGGER.info("使用图片: %s", image_path)
    LOGGER.debug("请求参数: data.format=%s, tbpu.parser=%s, timeout=%s", args.data_format, args.parser, args.timeout)

    try:
        image_base64 = image_to_base64(image_path)
        payload = build_payload(image_base64, args.data_format, args.parser)
        LOGGER.debug("图片大小=%s bytes, base64长度=%s", image_path.stat().st_size, len(image_base64))
        timeout = httpx.Timeout(args.timeout)
        response = httpx.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        LOGGER.exception("HTTP 请求失败: %s", exc)
        return 2
    except Exception as exc:  # pragma: no cover - 脚本兜底
        LOGGER.exception("请求阶段出现未预期异常: %s", exc)
        return 2

    try:
        body = response.json()
    except json.JSONDecodeError as exc:
        LOGGER.exception("响应不是合法 JSON: %s", exc)
        LOGGER.error("原始响应文本: %s", response.text)
        return 3

    LOGGER.info("HTTP 状态码: %s", response.status_code)
    if args.print_json:
        LOGGER.info("OCR 原始响应: %s", json.dumps(body, ensure_ascii=False))

    try:
        text = extract_ocr_text(body)
    except Exception as exc:
        LOGGER.error("解析 OCR 返回失败: %s", exc)
        return 4

    if not text:
        LOGGER.warning("OCR 返回成功但文本为空")
        return 5

    LOGGER.info("OCR 识别成功，文本长度=%s", len(text))
    print("==== OCR TEXT BEGIN ====")
    print(text)
    print("==== OCR TEXT END ====")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
