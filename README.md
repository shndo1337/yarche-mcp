# yarche-mcp

MCP-сервер для интернет-магазина «Ярче!» ([yarcheplus.ru](https://yarcheplus.ru)). Позволяет ИИ-ассистенту (Claude и другим MCP-клиентам) искать товары, смотреть цены, состав и КБЖУ. Регион по умолчанию — Томск.

- Только чтение: корзину и заказы сервер не трогает.
- Не нужны ни аккаунт, ни ключи. Сервер сам получает анонимный гостевой токен, как это делает сайт.
- Использует неофициальный GraphQL API сайта, он может измениться без предупреждения. Проект не связан с «Ярче!».

## Инструменты

| Инструмент | Что делает |
|---|---|
| `search_products(query, page, limit)` | Поиск товаров по тексту |
| `get_product(product_id)` | Карточка: цена, состав, КБЖУ на 100 г, срок хранения и др. |
| `list_categories()` | Дерево категорий |
| `get_category_products(category_id, page, limit)` | Товары категории |

Состав и КБЖУ есть не у всех товаров, это зависит от того, что заполнил магазин.

## Установка

Нужен Python 3.10+.

```bash
git clone https://github.com/shndo1337/yarche-mcp.git
cd yarche-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

На Windows вместо `.venv/bin/` используй `.venv\Scripts\`.

Проверить, что всё работает, можно так:

```bash
.venv/bin/python server.py
```

Сервер запустится и будет ждать запросы по stdio. Остановить: `Ctrl+C`.

## Подключение

Ниже везде нужны **абсолютные пути** к `python` из `.venv` и к `server.py`.

### Claude Code

```bash
claude mcp add yarche -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

Команду запускай из папки проекта. Проверка: `claude mcp list`.

### Claude Desktop

Открой файл конфигурации:

- Linux: `~/.config/Claude/claude_desktop_config.json`
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Добавь сервер и перезапусти приложение:

```json
{
  "mcpServers": {
    "yarche": {
      "command": "/абсолютный/путь/к/yarche-mcp/.venv/bin/python",
      "args": ["/абсолютный/путь/к/yarche-mcp/server.py"]
    }
  }
}
```

### Другие клиенты (Cursor, Cline и т.д.)

Подойдёт тот же блок `mcpServers`, он общий для большинства MCP-клиентов.

## Примеры запросов

- «Найди в Ярче гречку и покажи самую дешёвую».
- «Какой состав и сколько калорий в сгущённом молоке Волоконовское?»
- «Покажи, что есть в категории Овощи».

## Как это работает

Сайт — React-приложение, которое ходит в GraphQL API `api.yarcheplus.ru`. Токен выдаётся запросом `GET /api/auth/token?shop_code=yarche`. Каталог привязан к региону по умолчанию (Томск). Если токен протух (ответ 401), сервер обновляет его сам.

## Ограничения

- Не сортирует результаты на стороне магазина.
- Выбор другого адреса доставки не поддерживается.
- Используй в разумных объёмах и не создавай лишней нагрузки на чужой сервер.

## Лицензия

MIT
