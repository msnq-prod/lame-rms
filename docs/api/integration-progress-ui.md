# Integration Progress UI

Новый модуль интерфейса `frontend/src/features/integration-progress/` обеспечивает ручной запуск интеграций и мониторинг их выполнения через существующий REST API.

## Компоненты
- **IntegrationProgressDashboard** — контейнер, объединяющий загрузку списка интеграций, постановку задач в очередь и polling их статусов.
- **IntegrationList** — список интеграций с кнопками запуска.
- **RunIntegrationButton** — кнопка запуска отдельной интеграции, блокируется во время отправки задачи.
- **IntegrationStatusPanel** — панель, отображающая состояние текущей задачи, сообщение и JSON результата.
- **useIntegrationProgress** — хук, инкапсулирующий работу с API и логику polling-а.

## Smoke-проверка
1. Установите зависимости фронтенда: `npm install --prefix frontend`.
2. Запустите юнит-тесты UI: `npm test --prefix frontend`.
3. (Опционально) В Storybook проект не подключён, поэтому визуальная проверка выполняется в рамках существующего приложения после сборки.

Хук использует REST-методы `GET /integrations`, `POST /integrations/:name/enqueue` и `GET /integrations/tasks/:task_id`. Для ускорения локальных тестов интервалы polling-а можно переопределять через проп `pollInterval` у `IntegrationProgressDashboard`.
