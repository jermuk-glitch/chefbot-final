# ChefBot — кулінарний AI-асистент

Фінальний проєкт курсу з AI-застосунків · **Команіч Надія Миколаївна**

ChefBot допомагає вдома біля плити: знаходить рецепт у перевіреній базі, точно перераховує міри й порції, підбирає замінники, соуси й напої, враховує алергії родини і складає список покупок.

Головний принцип: **модель розуміє — код рахує.** Мовна модель інтерпретує запит, обирає інструмент і формулює відповідь. Рецепти, грами, градуси, калорії, фільтр алергенів і перевірка чисел — у коді.

## Посилання

| Що | Де |
|---|---|
| Ноутбук (Colab) | [Final_Komanich_ChefBot.ipynb](https://colab.research.google.com/drive/1uCtRfBXa78VRb9Gx939Abd2KPnJ_-UNm) |
| Презентація | [claude.ai/artifact/1mq3xPMbVJhdC6zeLvFcvy](https://claude.ai/artifact/1mq3xPMbVJhdC6zeLvFcvy) · PDF у `presentation/` |
| Демо (веб-ChefBot) | [claude.ai/artifact/G55pdsjBEi92KtutRKNqar](https://claude.ai/artifact/G55pdsjBEi92KtutRKNqar) |
| Веб-ChefBot як файл | `web/index.html` — відкривається в будь-якому браузері без інтернету й ключів (офлайн-режим: пошук, міри, замінники кодом) |
| Agno-версія (ДЗ 11) | [Colab](https://colab.research.google.com/drive/1xmp0pOkfANyXrZX4zRuci4iFqONz_fVJ) · копія в `notebooks/` |

## Структура

```
chefbot-final/
├── notebooks/
│   ├── Final_Komanich_ChefBot.ipynb   # основний ноутбук: LangChain-агент, тести, ChefBot+
│   └── Agno_agents_reasoning.ipynb    # Agno: веб-пошук, власні інструменти, команда, reasoning
├── streamlit_app/
│   ├── app.py                         # інтерфейс: чат, картки рецептів, соуси, напої, довідник
│   ├── agent.py                       # агент LangGraph + Gemini 2.5 Flash та інструменти
│   ├── recipes_saved.json             # база рецептів
│   ├── sauces_tips.json               # соуси, міри, напої, поради
│   ├── images/                        # фото страв, соусів і напоїв
│   ├── requirements.txt
│   └── .streamlit/secrets.toml.example
├── web/
│   └── index.html                     # веб-ChefBot одним файлом: фото, рецепти, соуси, напої, режим готування
└── presentation/
    └── Final_Komanich_ChefBot_slides.pdf
```

## Основний ноутбук

| Розділ | Зміст |
|---|---|
| 1–6 | Модель `gpt-4o-mini` (t 0,2), інструменти `search_recipes`, `convert_units`, `find_substitute`, системний промпт, агент `create_agent`, діалог із контекстом |
| 7–9 | 13 автоматичних тестів за категоріями ризику, таблиця тестування, продуктова таблиця й висновки |
| 10 | **ChefBot+**: профіль родини з фільтром алергенів, `get_recipe` з масштабуванням порцій, `get_nutrition`, `get_sauce`, `pair_drinks`, `add_to_shopping`, валідатор чисел; 8 модульних тестів і тести T14–T19 з моделлю |

Результати останнього запуску: інструменти обрано правильно в 13 з 13 базових тестів і 5 з 6 тестів ChefBot+; модульні тести — 8 з 8. Валідатор позначив ⚠ вигадане моделлю «170–180 грамів» у тесті з кіноа. Знахідки тестування і виправлення описано в коментарі в кінці ноутбука.

**Запуск:** відкрийте ноутбук у Colab, додайте `OPENAI_API_KEY` у Secrets (🔑) і виберіть «Виконати все».

## Streamlit-застосунок

```bash
cd streamlit_app
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # і вставте ключ Gemini
streamlit run app.py
```

Ключ API не зберігається в репозиторії: `secrets.toml` додано до `.gitignore`.

## Межі продукту

ChefBot відповідає лише на кулінарні теми, не дає медичних і дієтологічних порад, не вигадує рецептів і пропорцій. Калорійність — оцінка за таблицею продуктів; фільтр алергенів бачить лише склад, записаний у рецепті, тож це підказка, а не гарантія.
