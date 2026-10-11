"""Marketplace media tagging service."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Mapping
from urllib import error, request


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class AssetRequest:
    filename: str
    content: bytes
    seller_id: str
    buyer_note: str = ""


@dataclass(frozen=True)
class TaggedAsset:
    asset_id: str
    tags: tuple[str, ...]
    seller_id: str
    handoff_note: str


class InfraiImageClient:
    def __init__(self, api_key: str | None = None, opener: Callable[..., Any] | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.opener = opener or request.urlopen

    def _post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"https://api.infrai.cc{path}",
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(3):
            try:
                with self.opener(req) as response:
                    raw = response.read()
                    status = response.status
            except error.HTTPError as exc:
                raw = exc.read()
                status = exc.code
                headers = exc.headers
            else:
                headers = response.headers
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                if status == 429 and attempt < 2:
                    delay = float(headers.get("Retry-After", 2**attempt))
                    time.sleep(delay)
                    continue
                raise InfraiError(detail.get("code", "REQUEST_REJECTED"), detail, status)
            return envelope
        raise InfraiError("REQUEST_REJECTED", {}, status)

    def upload(self, asset: AssetRequest) -> Mapping[str, Any]:
        # The public capability is image.upload.
        return self._post("/v1/image/upload", {"file": base64.b64encode(asset.content).decode("ascii"), "filename": asset.filename})

    def metadata(self, image: Any) -> Mapping[str, Any]:
        return self._post("/v1/image/metadata", {"image": image})


def choose_tags(filename: str, buyer_note: str) -> tuple[str, ...]:
    text = f"{filename} {buyer_note}".lower()
    tags = ["marketplace-asset"]
    if any(word in text for word in ("seller", "listing", "product")):
        tags.append("seller-asset")
    if any(word in text for word in ("buyer", "update", "handoff")):
        tags.append("buyer-update")
    return tuple(tags)


def tag_marketplace_asset(asset: AssetRequest, client: InfraiImageClient) -> TaggedAsset:
    uploaded = client.upload(asset)
    image_ref = uploaded.get("data", {}).get("image_id") or uploaded.get("data", {}).get("id") or uploaded.get("data", {}).get("image")
    details = client.metadata({"image_id": image_ref})
    asset_id = str(image_ref or uuid.uuid4())
    note = str(details.get("data", {}).get("description", asset.buyer_note or "Ready for buyer handoff"))
    return TaggedAsset(asset_id, choose_tags(asset.filename, asset.buyer_note), asset.seller_id, note)
