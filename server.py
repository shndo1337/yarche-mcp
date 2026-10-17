"""MCP-сервер для интернет-магазина «Ярче!» (yarcheplus.ru).

Использует тот же GraphQL API, что и сайт, с гостевым токеном.
Только чтение: каталог, поиск, карточка товара. Корзину и заказы не трогает.
"""
import asyncio

import httpx
from fastmcp import FastMCP

API = "https://api.yarcheplus.ru"
SHOP = "yarche"
SITE = "https://yarcheplus.ru"

mcp = FastMCP("yarche")

_client = httpx.AsyncClient(
    base_url=API,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=20,
)
_token: str | None = None
_token_lock = asyncio.Lock()

PRODUCT_FIELDS = """
  id code name description price previousPrice isAvailable isNew isHit
  brand rating numberOfRatings weightUnit volumeUnit
  categories { id name code }
  quant { unit pricePerUnit }
"""


async def _refresh_token() -> str:
    global _token
    async with _token_lock:
        r = await _client.get("/api/auth/token", params={"shop_code": SHOP})
        r.raise_for_status()
        _token = r.headers["token"]
        return _token


async def _gql(query: str, variables: dict | None = None) -> dict:
    """GraphQL-запрос с гостевым токеном; при 401 токен обновляется один раз."""
    for attempt in range(2):
        token = _token or await _refresh_token()
        r = await _client.post(
            "/api/graphql",
            json={"query": query, "variables": variables or {}},
            headers={"token": token},
        )
        if r.status_code == 401 and attempt == 0:
            await _refresh_token()
            continue
        r.raise_for_status()
        body = r.json()
        if body.get("errors") and not body.get("data"):
            raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))
        return body["data"]
    raise RuntimeError("Не удалось авторизоваться в API Ярче")


def _product(p: dict) -> dict:
    return {
        "id": p["id"],
        "name": p["name"],
        "price": p["price"],
        "old_price": p.get("previousPrice"),
        "in_stock": p.get("isAvailable"),
        "weight": p.get("weightUnit") or p.get("volumeUnit"),
        "brand": p.get("brand"),
        "rating": p.get("rating"),
        "ratings_count": p.get("numberOfRatings"),
        "is_new": p.get("isNew"),
        "is_hit": p.get("isHit"),
        "categories": [c["name"] for c in p.get("categories") or []],
        "url": f"{SITE}/product/{p['code']}-{p['id']}",
    }


@mcp.tool()
async def search_products(query: str, page: int = 1, limit: int = 20) -> dict:
    """Поиск товаров в «Ярче!» по тексту.

    Args:
        query: Что искать, например "молоко" или "гречка".
        page: Номер страницы (с 1).
        limit: Товаров на странице (макс 48).
    """
    data = (await _gql(
        f"""query($s: String!, $p: PageInput) {{
          search(search: $s, page: $p) {{
            products {{ {PRODUCT_FIELDS} }}
            page {{ total limit page }}
          }}
        }}""",
        {"s": query, "p": {"page": page, "limit": min(limit, 48)}},
    ))["search"]
    return {
        "total": data["page"]["total"],
        "page": data["page"]["page"],
        "products": [_product(p) for p in data["products"]],
    }


PROPERTY_FIELDS = """
  propertyValues {
    property { name title unit }
    ... on BooleanPropertyValue { boolValue }
    ... on IntegerPropertyValue { intValue }
    ... on StringPropertyValue { strValue }
    ... on ItemOfListPropertyValue { item { label } }
    ... on ListPropertyValue { list { label } }
  }
"""

# свойства карточки, которые выносим в отдельные поля
NUTRITION_KEYS = {
    "energy_value": "kcal",
    "protein_content": "protein_g",
    "fat_content": "fat_g",
    "carbohydrate_content": "carbs_g",
}


def _property_value(pv: dict):
    for key in ("strValue", "intValue", "boolValue"):
        if pv.get(key) is not None:
            return pv[key]
    if pv.get("item"):
        return pv["item"]["label"]
    if pv.get("list"):
        return ", ".join(i["label"] for i in pv["list"])
    return None


@mcp.tool()
async def get_product(product_id: int) -> dict:
    """Подробная карточка товара по id: состав, КБЖУ, срок хранения и др.

    КБЖУ указано на 100 г/мл продукта (если магазин его заполнил).

    Args:
        product_id: Числовой id товара (из поиска или каталога).
    """
    data = await _gql(
        f"""query($id: Int!) {{
          product(id: $id) {{ {PRODUCT_FIELDS} {PROPERTY_FIELDS} }}
        }}""",
        {"id": product_id},
    )
    p = data["product"]
    if not p:
        raise ValueError(f"Товар {product_id} не найден")
    result = _product(p)
    result["description"] = p.get("description")

    nutrition, composition, attributes = {}, None, {}
    for pv in p.get("propertyValues") or []:
        prop, value = pv["property"], _property_value(pv)
        if value in (None, "", "код не указан"):
            continue
        if prop["name"] in NUTRITION_KEYS:
            nutrition[NUTRITION_KEYS[prop["name"]]] = value
        elif prop["name"] == "composition":
            composition = value
        elif prop["name"] not in ("brand", "weight_unit"):
            unit = f" {prop['unit']}" if prop.get("unit") else ""
            attributes[prop["title"]] = f"{value}{unit}"
    result["composition"] = composition
    result["nutrition_per_100g"] = nutrition or None
    result["attributes"] = attributes
    return result


@mcp.tool()
async def list_categories() -> list[dict]:
    """Дерево категорий каталога. У подкатегорий заполнен parent_tree_id."""
    data = await _gql("{ categories { id name code treeId parentTreeId amount } }")
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "tree_id": c["treeId"],
            "parent_tree_id": c["parentTreeId"],
            "products_count": c["amount"],
        }
        for c in data["categories"]
    ]


@mcp.tool()
async def get_category_products(category_id: int, page: int = 1, limit: int = 20) -> dict:
    """Товары категории (id из list_categories).

    Args:
        category_id: Поле id категории.
        page: Номер страницы (с 1).
        limit: Товаров на странице (макс 48).
    """
    data = (await _gql(
        f"""query($i: ProductsRequest) {{
          products(input: $i) {{
            list {{ {PRODUCT_FIELDS} }}
            page {{ total limit page }}
          }}
        }}""",
        {"i": {
            "filter": {"byCategoryIds": [category_id]},
            "page": {"page": page, "limit": min(limit, 48)},
        }},
    ))["products"]
    return {
        "total": data["page"]["total"],
        "page": data["page"]["page"],
        "products": [_product(p) for p in data["list"]],
    }


if __name__ == "__main__":
    mcp.run()
