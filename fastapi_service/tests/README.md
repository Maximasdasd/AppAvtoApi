# Юнит-тесты — Car Rental FastAPI

## Структура

```
fastapi_service/
├── app/
│   └── ...
└── tests/
    ├── conftest.py      ← настройка PYTHONPATH и env-переменных
    └── test_api.py      ← все тесты
```

## Установка зависимостей

```bash
pip install pytest httpx python-jose bcrypt
```

## Запуск

```bash
# из корня fastapi_service/
cd fastapi_service
pytest tests/test_api.py -v
```

## Что покрыто

|Модуль       |Тестов|Что проверяется                                                  |
|-------------|------|-----------------------------------------------------------------|
|`security.py`|6     |хэш пароля, верификация, JWT create/decode, невалидный токен     |
|`GET /`      |2     |статус 200, тело ответа                                          |
|`/car`       |7     |create, get by id, delete, валидация (плохая категория, нет поля)|
|`/client`    |6     |create, get found/not-found, валидация driver_license            |
|`/staff`     |7     |create, get found/not-found, login, info_me, невалидная роль     |
|`/rental`    |7     |create, list, cancel, complete, get by id/status, clear          |
|`/repair`    |7     |create, list, get, complete, delete one/all, валидация           |
|auth guard   |1     |запрос без токена → 401/403                                      |

**Итого: ~43 теста**

## Как это работает

Все тесты используют `unittest.mock.MagicMock` вместо реальной БД:

- контроллеры заменяются моками через `app.dependency_overrides`
- JWT-токен генерируется с тестовым секретом
- конфиг (`Settings`) патчится, `.env` файл **не нужен**