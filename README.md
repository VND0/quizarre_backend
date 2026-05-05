# Quizarre_backend

## Структура репозитория
```
app/
    api/ - http роуты
        auth.py - логин
        quizzes.py - квизы
        users.py - данные пользователя
    core/
        config.py - глобальные константы и переменные среды
        models.py - глобальные модели
        security.py - безопасность логина
    db/db.py - сетап базы данных
    models/
        user.py - модели, связанные с пользователем
        quizzes.py - модели, связанные с квизом
```