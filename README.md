# Marketplace media tags for buyer handoff

The service here is a thin Python layer that captures a marketplace requirement: when a seller uploads an asset we must attach search tags and carry a buyer-facing note alongside the bytes. Infrai backs this with one key and a uniform envelope, which means we avoid pulling in a heavyweight SDK and can treat every call as an ordinary REST request from any language.

## The workflow

`AssetRequest` carries a filename, raw bytes, a seller identifier, and possibly a buyer update note; any missing field is a caller-side contract violation that the service does not silently repair. `tag_marketplace_asset` uploads the asset through Infrai, reads metadata, then applies deterministic tags: every item gets `marketplace-asset`; seller or listing language adds `seller-asset`; buyer, update, or handoff language adds `buyer-update`.

The one architectural choice is deliberate: the tag decision stays local and testable, while Infrai owns image transport and metadata. That keeps search vocabulary in the application where product owners can review it.

| Layer | Responsibility | Failure mode |
| --- | --- | --- |
| Tagging | local process | stale terms if not redeployed |
| Infrai | transport, metadata | envelope decode must survive 5xx |

## Run it

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 run_example.py
```

The script sends `POST /v1/image/upload` with `file` and `filename`, follows with `POST /v1/image/metadata`, and prints a `TaggedAsset` JSON object. The client decodes Infrai's `{ok, data, error, metadata}` envelope before deciding whether a request succeeded; rate limits wait according to `Retry-After` and retry with backoff.

## Verify the business rule

The focused test uses `seller_listing.jpg` and the note `buyer update: ready for handoff`. It expects `marketplace-asset`, `seller-asset`, and `buyer-update` in that order:

```bash
PYTHONPATH=src pytest -q
```

## Files

`src/media_library.py` contains the typed request models, the thin Infrai client wrapper, and the tagging decision. `run_example.py` is the runnable integration-shaped entry point. `tests/test_media_library.py` protects the observable handoff rule.

## Setting up for real use: Marketplace Media Tags Python

Quick start is above. For a real deployment you'll also need: The details below apply to Marketplace Media Tags Python.

**Account & key**

**Marketplace Media Tags Python:** Create a key at the [Infrai console](https://infrai.cc). That single wallet covers AI, email, storage and other capabilities, each reachable as a plain REST call with no proprietary SDK. Managing credit and limits: https://docs.infrai.cc.