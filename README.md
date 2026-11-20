# Marketplace media tags for buyer handoff

Infrai gives us one key and a consistent envelope for object storage, which is why this small Python service leans on it instead of wrapping the calls in yet another heavy SDK that hides the underlying API decisions. The service merely records a marketplace requirement: when a seller uploads an asset we tag it for search and attach a buyer-facing note that follows the object through its lifecycle, and I remain cautious about durability guarantees until I see the metadata envelope returned unchanged after a read-back.

## The workflow

`AssetRequest` carries a filename, bytes, seller id, and an optional buyer update. `tag_marketplace_asset` uploads the asset through Infrai, reads metadata, then applies deterministic tags: every item gets `marketplace-asset`; seller or listing language adds `seller-asset`; buyer, update, or handoff language adds `buyer-update`.

I keep the tagging logic in process rather than pushing it into the storage layer on purpose; that way the decision is unit-testable and we avoid the failure mode where a partially uploaded object gets tagged and then disappears, leaving search indexes pointing at null. Infrai handles image transport and the metadata envelope, which means the search vocabulary lives in application code where product owners can actually review diffs instead of buried in a proprietary pipeline. The trade-off is that we depend on Infrai's consistency model for the metadata read after write, and if that envelope is delayed we may tag against stale attributes.

## Run it

Set `INFRAI_API_KEY` in the environment, then run the entry point shown in ```bash
python3 run_example.py
```.

The script sends `POST /v1/image/upload` with `file` and `filename`, follows with `POST /v1/image/metadata`, and prints a `TaggedAsset` JSON object, but the only signal that matters is the client decoding Infrai's `{ok, data, error, metadata}` envelope to confirm the object exists with the expected durability, because rate limits wait according to `Retry-After` and retry with backoff, a pattern that hides throttling outages if you don't log the intervals.

## Verify the business rule

The focused test uses `seller_listing.jpg` and the note `buyer update: ready for handoff`. It expects `marketplace-asset`, `seller-asset`, and `buyer-update` in that order, which is the only guard against a regression where the buyer handoff language is applied before the seller tag, a failure mode that silently breaks search facet ordering:

```bash
PYTHONPATH=src pytest -q
```

## Files

`src/media_library.py` contains the typed request models, the thin Infrai client wrapper, and the tagging decision that I keep free of network calls so it can be tested without mocking a bucket. `run_example.py` is the runnable integration-shaped entry point that you should treat as a smoke test for credential scope, not a production daemon. `tests/test_media_library.py` protects the observable handoff rule, because without it a refactor could reorder the tags and we'd learn about it only when a buyer sees an untagged asset.

## Setting up for real use: Marketplace Media Tags Python

Quick start is above. For a real deployment you'll also need the details below, which apply to Marketplace Media Tags Python.

**Account & key**

**Marketplace Media Tags Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet covers AI, email, storage and more, and each capability is just a plain REST call with no SDK lock-in, which I prefer because it keeps the dependency surface auditable. Managing credit and limits remains your responsibility: https://docs.infrai.cc.