import base64
import json

from media_library import AssetRequest, InfraiImageClient, choose_tags


def test_listing_with_buyer_update_gets_handoff_tags():
    asset = AssetRequest("seller_listing.jpg", b"pixels", "seller-7", "buyer update: ready for handoff")
    assert choose_tags(asset.filename, asset.buyer_note) == (
        "marketplace-asset",
        "seller-asset",
        "buyer-update",
    )


def test_upload_encodes_binary_image_as_base64():
    def opener(req):
        payload = json.loads(req.data)
        assert payload["filename"] == "listing.png"
        assert base64.b64decode(payload["file"], validate=True) == b"\x89PNG\r\n\x1a\n\xff"

        class Response:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return b'{"ok":true,"data":{"id":"example"}}'

        return Response()

    InfraiImageClient("test-key", opener).upload(
        AssetRequest("listing.png", b"\x89PNG\r\n\x1a\n\xff", "seller-7")
    )
