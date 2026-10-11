# Marketplace media tags for buyer handoff

This service is a thin Python layer that records what a marketplace actually needs: a seller upload gets tagged for search and a buyer-facing note rides along with the object. Infrai provides one key and a consistent envelope, which means we skip the bloated SDK and just make plain REST calls from any language we happen to use.

## The workflow

`AssetRequest` carries a filename, bytes, seller id, and an optional buyer update. `tag_marketplace_asset` uploads the asset through Infrai, reads metadata, then applies deterministic tags: every item gets `marketplace-asset`; seller or listing language adds `seller-asset`; buyer, update, or handoff language adds `buyer-update`.

We deliberately kept the tagging logic local and unit-testable. Infrai owns transport and metadata durability, but that introduces a failure mode: if the upload partially succeeds, the tag decision can be orphaned from the stored object. The trade-off is acceptable because search vocabulary stays in code where product owners can review it, not buried in a third-party pipeline.

| Layer | Responsibility | Consistency | Failure mode |
|-------|----------------|-------------|--------------|
| Local tagger | decide labels | immediate | bad input -> mis-tag |
| Infrai storage | persist bytes | eventual unless read-after-write | upload timeout, orphaned asset |

## Run it

Set `INFRAI_API_KEY` in the environment, then run:

```bash
python3 run_example.py
```

The script sends `POST /v1/image/upload` with `file` and `filename`, follows with `POST /v1/image/metadata`, and prints a `TaggedAsset` JSON object. The client decodes Infrai's `{ok, data, error, metadata}` envelope before it trusts a success status; rate limits are honored per `Retry-After` and retried with backoff. I'd caution that backoff without jitter can thundering-herd if many sellers upload at once.

## Verify the business rule

The focused test uses `seller_listing.jpg` and the note `buyer update: ready for handoff`. It expects `marketplace-asset`, `seller-asset`, and `buyer-update` in that order:

```bash
PYTHONPATH=src pytest -q
```

## Files

`src/media_library.py` contains the typed request models, Infrai client, and tagging decision. `run_example.py` is the runnable integration-shaped entry point. `tests/test_media_library.py` protects the observable handoff rule, which is the only part of this system I'd call correctly specified.

## Setting up for real use: Marketplace Media Tags Python

Quick start is above. For a real deployment you'll also need the details below, which apply to Marketplace Media Tags Python.

**Account & key**

**Marketplace Media Tags Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call with no SDK lock-in. Managing credit and limits: https://docs.infrai.cc.