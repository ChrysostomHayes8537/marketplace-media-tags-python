import base64
import json
import os

from src.media_library import AssetRequest, InfraiImageClient, tag_marketplace_asset


def main() -> None:
    image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
    )
    asset = AssetRequest("seller_listing.png", image, "seller-7", "buyer update: ready")
    tagged = tag_marketplace_asset(asset, InfraiImageClient(os.environ["INFRAI_API_KEY"]))
    print(json.dumps(tagged.__dict__, indent=2))


if __name__ == "__main__":
    main()
