# Yarche MCP Server

Сервер [Model Context Protocol](https://modelcontextprotocol.io) для интернет-магазина «Ярче!» ([yarcheplus.ru](https://yarcheplus.ru)). Даёт LLM доступ к каталогу: поиск товаров, цены, состав и КБЖУ. Регион по умолчанию — Томск.

> [!NOTE]
> Сервер использует неофициальный GraphQL API сайта, который может измениться без предупреждения. Проект не связан с «Ярче!». Доступ только на чтение: корзина и заказы не затрагиваются. Аккаунт и API-ключи не нужны, сервер сам получает анонимный гостевой токен.

### Доступные инструменты

- `search_products` — поиск товаров по тексту.
    - `query` (string, обязательный): поисковый запрос
    - `page` (integer, необязательный): номер страницы, с 1 (по умолчанию 1)
    - `limit` (integer, необязательный): товаров на странице, максимум 48 (по умолчанию 20)

- `get_product` — карточка товара: цена, наличие, рейтинг, состав, КБЖУ на 100 г, срок хранения и другие свойства.
    - `product_id` (integer, обязательный): id товара из поиска или каталога

- `list_categories` — дерево категорий каталога. У подкатегорий заполнен `parent_tree_id`.

- `get_category_products` — товары категории.
    - `category_id` (integer, обязательный): id категории из `list_categories`
    - `page` (integer, необязательный): номер страницы, с 1 (по умолчанию 1)
    - `limit` (integer, необязательный): товаров на странице, максимум 48 (по умолчанию 20)

Состав и КБЖУ возвращаются, только если магазин заполнил их в карточке.

## Установка

Требуется Python 3.10 или новее.

```
git clone https://github.com/shndo1337/yarche-mcp.git
cd yarche-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

На Windows используйте `.venv\Scripts\` вместо `.venv/bin/`.

Проверить запуск можно командой `.venv/bin/python server.py`. Сервер работает через stdio и ждёт запросов клиента.

## Конфигурация

Во всех примерах укажите абсолютные пути к `python` из `.venv` и к `server.py`.

### Claude Code

```
claude mcp add yarche -- /путь/к/yarche-mcp/.venv/bin/python /путь/к/yarche-mcp/server.py
```

### Claude Desktop

Добавьте в `claude_desktop_config.json` и перезапустите приложение.

<details>
<summary>Расположение файла</summary>

- Linux: `~/.config/Claude/claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
</details>

```json
{
  "mcpServers": {
    "yarche": {
      "command": "/путь/к/yarche-mcp/.venv/bin/python",
      "args": ["/путь/к/yarche-mcp/server.py"]
    }
  }
}
```

### Cursor, Cline и другие клиенты

Подойдёт тот же блок `mcpServers`.

## Примеры запросов

- «Найди в Ярче гречку и покажи самую дешёвую»
- «Какой состав и сколько калорий в сгущённом молоке Волоконовское?»
- «Что есть в категории Овощи?»

## Как это работает

Сайт обращается к GraphQL API `api.yarcheplus.ru`. Гостевой токен выдаёт `GET /api/auth/token?shop_code=yarche`; при ответе 401 сервер запрашивает новый токен. Каталог привязан к региону по умолчанию (Томск).

## Ограничения

- Нет сортировки на стороне магазина.
- Нельзя выбрать другой адрес доставки.

## Лицензия

MIT, см. [LICENSE](LICENSE).
