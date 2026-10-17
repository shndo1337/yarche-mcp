# yarche-mcp

MCP-сервер для интернет-магазина «Ярче!» ([yarcheplus.ru](https://yarcheplus.ru)). Только чтение: поиск и каталог товаров. Регион по умолчанию — Томск.

Использует неофициальный GraphQL API сайта с гостевым токеном, он может измениться без предупреждения.

## Инструменты

- `search_products(query, page, limit)` — поиск товаров
- `get_product(product_id)` — карточка: цена, состав, КБЖУ на 100 г, срок хранения и др.
- `list_categories()` — дерево категорий
- `get_category_products(category_id, page, limit)` — товары категории

## Установка

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
claude mcp add yarche -- "$PWD/.venv/bin/python" "$PWD/server.py"
```
