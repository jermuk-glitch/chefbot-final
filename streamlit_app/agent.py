"""
ChefBot — логіка агента (заміна для агента з теми 8).

Якщо у вас є власний агент з теми 8, замініть у цьому файлі
інструменти та функцію build_agent() своїми. Застосунок (app.py)
звертається лише до двох речей: build_agent() і stream_reply().
"""

import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

MODEL_ID = "gemini-2.5-flash"

# ---------------------------------------------------------------------------
# Дані для інструментів
# ---------------------------------------------------------------------------

RECIPES = [
    {
        "name": "Запечена курка з картоплею",
        "time": "50 хв",
        "description": "Соковиті стегна з картоплею та часником у духовці.",
        "ingredients": ["курка", "картопля", "часник", "олія", "цибуля"],
        "vegetarian": False,
        "gluten_free": True,
        "steps": [
            "Наріжте картоплю часточками, цибулю — кільцями.",
            "Змішайте з олією, часником, сіллю та перцем.",
            "Викладіть курку зверху, запікайте 45 хв при 200 °C.",
        ],
    },
    {
        "name": "Курячий суп з рисом",
        "time": "40 хв",
        "description": "Легкий домашній суп, що зігріває.",
        "ingredients": ["курка", "рис", "морква", "цибуля", "картопля"],
        "vegetarian": False,
        "gluten_free": True,
        "steps": [
            "Зваріть бульйон з курки 20 хв.",
            "Додайте картоплю, моркву й цибулю.",
            "Всипте рис і варіть ще 15 хв.",
        ],
    },
    {
        "name": "Рис з овочами по-домашньому",
        "time": "25 хв",
        "description": "Швидкий вегетаріанський гарнір або окрема страва.",
        "ingredients": ["рис", "морква", "цибуля", "часник", "помідори", "олія"],
        "vegetarian": True,
        "gluten_free": True,
        "steps": [
            "Обсмажте цибулю й моркву на олії.",
            "Додайте помідори й часник, тушкуйте 5 хв.",
            "Змішайте з відвареним рисом.",
        ],
    },
    {
        "name": "Омлет із сиром і помідорами",
        "time": "10 хв",
        "description": "Ситний сніданок за кілька хвилин.",
        "ingredients": ["яйця", "молоко", "сир", "помідори", "олія"],
        "vegetarian": True,
        "gluten_free": True,
        "steps": [
            "Збийте яйця з молоком, посоліть.",
            "Вилийте на розігріту сковорідку з олією.",
            "Додайте помідори та тертий сир, накрийте кришкою на 3 хв.",
        ],
    },
    {
        "name": "Макарони з томатним соусом",
        "time": "20 хв",
        "description": "Класика на кожен день.",
        "ingredients": ["макарони", "помідори", "часник", "цибуля", "олія", "сир"],
        "vegetarian": True,
        "gluten_free": False,
        "steps": [
            "Відваріть макарони до стану al dente.",
            "Обсмажте цибулю й часник, додайте помідори, тушкуйте 10 хв.",
            "Змішайте з макаронами, посипте сиром.",
        ],
    },
    {
        "name": "Деруни",
        "time": "30 хв",
        "description": "Хрусткі картопляні пляцки, найкращі зі сметаною.",
        "ingredients": ["картопля", "цибуля", "яйця", "борошно", "олія"],
        "vegetarian": True,
        "gluten_free": False,
        "steps": [
            "Натріть картоплю й цибулю, відтисніть зайву рідину.",
            "Додайте яйце, борошно, сіль.",
            "Смажте на олії до золотистої скоринки з обох боків.",
        ],
    },
    {
        "name": "Тушкована яловичина з овочами",
        "time": "1 год 30 хв",
        "description": "Ніжне м'ясо в густій овочевій підливі.",
        "ingredients": ["яловичина", "картопля", "морква", "цибуля", "помідори", "часник"],
        "vegetarian": False,
        "gluten_free": True,
        "steps": [
            "Обсмажте шматочки яловичини до скоринки.",
            "Додайте цибулю, моркву, помідори та трохи води.",
            "Тушкуйте 1 год, додайте картоплю ще на 25 хв.",
        ],
    },
    {
        "name": "Риба, запечена з овочами",
        "time": "35 хв",
        "description": "Легка страва з білою рибою та овочами.",
        "ingredients": ["риба", "морква", "цибуля", "помідори", "олія", "часник"],
        "vegetarian": False,
        "gluten_free": True,
        "steps": [
            "Викладіть овочі в форму, полийте олією.",
            "Покладіть рибу зверху, приправте часником і сіллю.",
            "Запікайте 25 хв при 190 °C.",
        ],
    },
]

# Рецепти, збережені користувачкою (рецепти-постери), — у recipes_saved.json
from pathlib import Path as _Path

_SAVED = _Path(__file__).with_name("recipes_saved.json")
if _SAVED.exists():
    _known = {r["name"] for r in RECIPES}
    RECIPES += [r for r in json.loads(_SAVED.read_text(encoding="utf-8")) if r["name"] not in _known]

_IMAGES = _Path(__file__).with_name("images") / "index.json"
if _IMAGES.exists():
    _img = json.loads(_IMAGES.read_text(encoding="utf-8"))
    for _r in RECIPES:
        if _r["name"] in _img:
            _r["image"] = str(_Path(__file__).parent / _img[_r["name"]])

_USER = _Path(__file__).with_name("recipes_user.json")
if _USER.exists():
    RECIPES += json.loads(_USER.read_text(encoding="utf-8"))


def add_user_recipe(recipe: dict) -> None:
    """Додає рецепт користувача в базу і зберігає у recipes_user.json."""
    saved = json.loads(_USER.read_text(encoding="utf-8")) if _USER.exists() else []
    saved = [r for r in saved if r["name"] != recipe["name"]] + [recipe]
    _USER.write_text(json.dumps(saved, ensure_ascii=False, indent=1), encoding="utf-8")
    RECIPES[:] = [r for r in RECIPES if r["name"] != recipe["name"]] + [recipe]

# Скільки грамів важить 1 cup (240 мл) продукту — ті самі густини, що в ноутбуці
GRAMS_PER_CUP = {
    "борошно": 127.2,
    "цукор": 204,
    "рис": 185,
    "вершкове масло": 218.4,
    "масло": 218.4,
    "молоко": 245,
    "вода": 240,
    "олія": 218,
    "крупа": 180,
    "вершки": 240,
    "сметана": 240,
    "мед": 340,
    "крохмаль": 128,
    "какао": 85,
    "цукрова пудра": 120,
}

# склянка (250 мл) і американська cup (240 мл) — різні міри
VOLUME_ML = {"мл": 1, "л": 1000, "склянка": 250, "cup": 240, "ст. л.": 15, "ч. л.": 5}
WEIGHT_G = {"г": 1, "кг": 1000, "унція": 28.35, "фунт": 453.6}

UNIT_ALIASES = {
    "ml": "мл", "мілілітр": "мл", "мілілітри": "мл",
    "l": "л", "літр": "л", "літри": "л",
    "cups": "cup", "чашка": "cup", "чашки": "cup", "склянки": "склянка", "склянок": "склянка",
    "tbsp": "ст. л.", "ложка": "ст. л.", "столова ложка": "ст. л.", "ст.л.": "ст. л.",
    "tsp": "ч. л.", "чайна ложка": "ч. л.", "ч.л.": "ч. л.",
    "g": "г", "грам": "г", "грами": "г", "грамів": "г",
    "kg": "кг", "кілограм": "кг",
    "oz": "унція", "унції": "унція",
    "lb": "фунт", "фунти": "фунт",
}

SUBSTITUTIONS = {
    "яйця": {
        "випічка": [
            "1 яйце = 1 ст. л. меленого льону + 3 ст. л. води (настояти 10 хв)",
            "1 яйце = ½ стиглого банана (дає солодкуватий смак)",
            "1 яйце = 60 г яблучного пюре",
        ],
        "загалом": ["1 яйце = 50 г шовкового тофу (для запіканок)"],
    },
    "вершкове масло": {
        "випічка": ["рослинна олія — 80 % від маси масла", "кокосова олія 1:1"],
        "загалом": ["оливкова олія для смаження"],
    },
    "молоко": {
        "загалом": ["вівсяне, мигдальне чи соєве молоко 1:1", "вода з 1 ст. л. вершкового масла на склянку"],
    },
    "борошно": {
        "без глютену": [
            "суміш рисового борошна й крохмалю (3:1)",
            "мигдальне борошно — для печива й кексів",
            "кукурудзяне борошно — для млинців і дерунів",
        ],
        "загалом": ["цільнозернове борошно 1:1 (тісто буде щільнішим)"],
    },
    "цукор": {
        "загалом": ["мед — ¾ від маси цукру, рідини зменшити", "кленовий сироп — ¾ від маси цукру"],
    },
    "сметана": {"загалом": ["грецький йогурт 1:1"]},
    "вершки": {"загалом": ["вершковий сир, розведений молоком (1:1)", "кокосові вершки 1:1 — без лактози"]},
    "горіхи": {"загалом": ["насіння гарбуза чи соняшнику — при алергії на горіхи", "підсмажені пластівці вівса для хрусткості"]},
    "креветки": {"загалом": ["кальмари або біла риба — та сама вага"]},
    "макарони": {"без глютену": ["рисова локшина", "гречана локшина (перевіряйте склад)"]},
}


def _normalize_unit(unit: str) -> str:
    unit = unit.strip().lower()
    return UNIT_ALIASES.get(unit, unit)


# ---------------------------------------------------------------------------
# Інструменти агента
# ---------------------------------------------------------------------------


@tool
def recipe_search(
    query: str = "",
    ingredients: list[str] | None = None,
    vegetarian: bool = False,
    gluten_free: bool = False,
) -> str:
    """Шукає рецепти за назвою страви або інгредієнтами.

    Args:
        query: назва страви або ключове слово (можна порожнє).
        ingredients: список інгредієнтів, що є в користувача.
        vegetarian: лише вегетаріанські рецепти.
        gluten_free: лише рецепти без глютену.
    """
    ingredients = [i.strip().lower() for i in (ingredients or []) if i.strip()]
    query = query.strip().lower()

    scored = []
    for recipe in RECIPES:
        if vegetarian and not recipe["vegetarian"]:
            continue
        if gluten_free and not recipe["gluten_free"]:
            continue

        matches = [i for i in ingredients if any(i in r for r in recipe["ingredients"])]
        name_hit = bool(query) and query in recipe["name"].lower()
        if ingredients and not matches and not name_hit:
            continue
        if query and not ingredients and not name_hit:
            continue

        missing = [r for r in recipe["ingredients"] if not any(i in r for i in ingredients)]
        scored.append((len(matches) + (3 if name_hit else 0), recipe, matches, missing))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = [
        {**recipe, "matched": matches, "missing": missing}
        for _, recipe, matches, missing in scored[:4]
    ]
    if not results:
        return json.dumps({"recipes": [], "note": "Рецептів не знайдено. Спробуйте інші інгредієнти."}, ensure_ascii=False)
    return json.dumps({"recipes": results}, ensure_ascii=False)


@tool
def unit_converter(amount: float, from_unit: str, to_unit: str, ingredient: str = "") -> str:
    """Конвертує кулінарні одиниці: г, кг, мл, л, склянка (250 мл), cup (240 мл), ст. л., ч. л., унція, фунт.

    Передавай одиницю ДОСЛІВНО так, як її назвав користувач: «склянка» — це не cup.

    Для переходу між об'ємом і вагою (наприклад, склянки → грами)
    обов'язково вкажіть інгредієнт: борошно, цукор, рис, масло, молоко тощо.
    """
    src, dst = _normalize_unit(from_unit), _normalize_unit(to_unit)
    ingredient = ingredient.strip().lower()

    def to_grams(value, unit):
        if unit in WEIGHT_G:
            return value * WEIGHT_G[unit]
        if unit in VOLUME_ML:
            density = GRAMS_PER_CUP.get(ingredient)
            if density is None:
                return None
            return value * VOLUME_ML[unit] / 240 * density
        return None

    for u in (src, dst):
        if u in ("°f", "f", "°c", "c"):
            break
    if {src, dst} <= {"°f", "f", "°c", "c"}:
        c = (amount - 32) * 5 / 9 if src in ("°f", "f") else amount
        result = c if dst in ("°c", "c") else c * 9 / 5 + 32
        return f"{amount:g} {from_unit} ≈ {round(result)} {to_unit}"
    if src in VOLUME_ML and dst in VOLUME_ML:
        result = amount * VOLUME_ML[src] / VOLUME_ML[dst]
    elif src in WEIGHT_G and dst in WEIGHT_G:
        result = amount * WEIGHT_G[src] / WEIGHT_G[dst]
    else:
        grams = to_grams(amount, src)
        if grams is None or (dst in VOLUME_ML and ingredient not in GRAMS_PER_CUP):
            known = ", ".join(GRAMS_PER_CUP)
            return f"Не можу конвертувати без відомого інгредієнта. Доступні: {known}."
        if dst in WEIGHT_G:
            result = grams / WEIGHT_G[dst]
        elif dst in VOLUME_ML:
            result = grams / GRAMS_PER_CUP[ingredient] * 240 / VOLUME_ML[dst]
        else:
            return f"Невідома одиниця: {to_unit}"

    label = f" ({ingredient})" if ingredient else ""
    return f"{amount:g} {src}{label} ≈ {result:.1f} {dst}"


@tool
def substitution_finder(ingredient: str, context: str = "загалом") -> str:
    """Підбирає замінники інгредієнта.

    Args:
        ingredient: що потрібно замінити (яйця, масло, молоко, борошно...).
        context: для чого заміна — "випічка", "без глютену" або "загалом".
    """
    key = ingredient.strip().lower()
    options = next((v for k, v in SUBSTITUTIONS.items() if k in key or key in k), None)
    if not options:
        return f"Для «{ingredient}» замінників у довіднику немає."
    context = context.strip().lower()
    chosen = options.get(context) or options.get("загалом") or next(iter(options.values()))
    lines = [f"• {o}" for o in chosen]
    return f"Замінники для «{ingredient}» ({context}):\n" + "\n".join(lines)


TOOLS = [recipe_search, unit_converter, substitution_finder]

# ---------------------------------------------------------------------------
# Агент
# ---------------------------------------------------------------------------


def build_system_prompt(fridge: list[str], diet: dict) -> str:
    """Перетворює стан інтерфейсу (sidebar) на контекст для агента."""
    fridge_text = ", ".join(fridge) if fridge else "не вказано"
    restrictions = [name for flag, name in [
        (diet.get("vegetarian"), "вегетаріанське"),
        (diet.get("gluten_free"), "без глютену"),
    ] if flag]
    diet_text = ", ".join(restrictions) if restrictions else "немає"

    return (
        "Ти ChefBot — дружній кулінарний асистент. Відповідай українською, коротко й практично: "
        "людина часто готує прямо зараз, тож пиши кроками й без зайвих вступів.\n\n"
        "Інструменти:\n"
        "- recipe_search — для будь-якого запиту про те, що приготувати;\n"
        "- unit_converter — для перерахунку мір (не рахуй сам);\n"
        "- substitution_finder — для замінників.\n\n"
        f"Холодильник користувача: {fridge_text}.\n"
        f"Дієтичні обмеження: {diet_text}.\n\n"
        "Під час пошуку рецептів завжди передавай у recipe_search інгредієнти з холодильника "
        "(якщо користувач не назвав інші) і прапорці обмежень. Ніколи не пропонуй страви, "
        "що порушують обмеження. Якщо користувач просить щось запам'ятати (наприклад, "
        "«я не їм глютен»), підтверди й порадь увімкнути відповідний прапорець ліворуч, "
        "щоб налаштування зберігалося. Не вигадуй рецептів, яких немає в результатах пошуку; "
        "картки знайдених рецептів користувач побачить над чатом, тож у тексті достатньо "
        "коротко пояснити вибір."
    )


def build_agent(api_key: str, temperature: float = 0.3):
    model = ChatGoogleGenerativeAI(model=MODEL_ID, google_api_key=api_key, temperature=temperature)
    return create_react_agent(model, TOOLS)


def _chunk_text(content) -> str:
    """Gemini може повертати content як рядок або як список частин."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
            if not isinstance(part, dict) or part.get("type", "text") == "text"
        )
    return ""


def to_langchain(history: list[dict], window: int = 12) -> list:
    """Історія зі session_state → повідомлення LangChain (лише останні N)."""
    messages = []
    for m in history[-window:]:
        cls = HumanMessage if m["role"] == "user" else AIMessage
        messages.append(cls(content=m["content"]))
    return messages


def stream_reply(agent, history: list[dict], fridge: list[str], diet: dict, tool_results: list):
    """Генератор для st.write_stream().

    Віддає текст відповіді по шматочках, а результати інструментів
    складає в tool_results, щоб застосунок міг показати їх як картки.
    """
    messages = [SystemMessage(content=build_system_prompt(fridge, diet))] + to_langchain(history)

    for message, _meta in agent.stream({"messages": messages}, stream_mode="messages"):
        if isinstance(message, ToolMessage):
            tool_results.append({"name": message.name, "content": message.content})
        elif isinstance(message, AIMessageChunk):
            text = _chunk_text(message.content)
            if text:
                yield text
