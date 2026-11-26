"""
ChefBot — кулінарний асистент у Streamlit.
Запуск:  streamlit run app.py
"""

import json
from pathlib import Path

import streamlit as st

from agent import build_agent, stream_reply

st.set_page_config(page_title="ChefBot — Кулінарний асистент", page_icon="🍳", layout="wide")

# ---------------------------------------------------------------------------
# Оформлення: ар-деко (смарагд, слонова кістка, античне золото)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Rubik:wght@400;500&display=swap');
h1, h2, h3, h4 { font-family: 'Cormorant Garamond', Georgia, serif !important; font-weight: 600 !important;
  color: #0F2E24; letter-spacing: .3px; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #F2EDE4; }
section[data-testid="stSidebar"] { border-right: 1px solid #C9A84C55; }
.cb-hero { padding: 6px 0 18px; }
.cb-eyebrow { font-size: 13px; letter-spacing: 4px; text-transform: uppercase; color: #8A6424; margin: 0; }
.cb-hero .cb-title { font-family: 'Cormorant Garamond', Georgia, serif !important; font-size: 72px !important; font-weight: 500;
  color: #0F2E24; line-height: 1 !important; margin: 10px 0 4px !important; }
[data-testid="stChatMessageAvatarAssistant"] { background: #1B4D3E !important; color: #C9A84C !important; }
[data-testid="stChatMessageAvatarUser"] { background: #B5843A !important; }
.cb-rule { width: 150px; border-top: 3px double #B5843A; margin: 10px 0 14px; }
.cb-sub { font-family: 'Cormorant Garamond', Georgia, serif; font-style: italic; font-size: 22px; color: #5E5A50; margin: 0; }
[data-testid="stColumn"] [data-testid="stLayoutWrapper"] > [data-testid="stVerticalBlock"] { background: #FAF7F1;
  border-color: #E2DACB !important; border-top: 3px solid #B5843A !important; border-radius: 6px; }
section[data-testid="stSidebar"] .stButton > button { color: #F2EDE4; border-color: #C9A84C; }
section[data-testid="stSidebar"] .stButton > button:hover { background: #C9A84C; color: #0F2A22; }
.cb-context { background: #FAF7F1; border: 1px solid #E2DACB; border-left: 3px solid #1B4D3E; border-radius: 4px;
  padding: 12px 18px; margin-bottom: 18px; color: #2A2A26; }
.cb-context b { color: #0F2E24; font-weight: 600; }
.cb-context .lbl { font-size: 12px; letter-spacing: 3px; text-transform: uppercase; color: #8A6424; margin-right: 8px; }
.stButton > button { border: 1px solid #B5843A; color: #0F2E24; background: transparent; border-radius: 4px; }
.stButton > button:hover { background: #B5843A; color: #FAF7F1; border-color: #B5843A; }
</style>
""", unsafe_allow_html=True)

AVAILABLE_INGREDIENTS = [
    "курка", "яловичина", "свинина", "фарш", "риба", "лосось", "креветки",
    "рис", "макарони", "картопля", "морква", "цибуля", "часник", "помідори",
    "капуста", "перець", "шпинат", "гриби", "кабачок",
    "сир", "сир кисломолочний", "молоко", "вершки", "сметана", "яйця",
    "вершкове масло", "олія", "борошно", "цукор", "мед", "гірчиця", "лимон",
]

QUICK_PROMPTS = [
    "Що приготувати з того, що є в холодильнику?",
    "Скільки грамів борошна в одній склянці?",
    "Чим замінити яйця у випічці?",
    "Знайди швидкий вегетаріанський рецепт",
]

# ---------------------------------------------------------------------------
# Стан
# ---------------------------------------------------------------------------
defaults = {
    "messages": [],
    "suggested_recipes": [],
    "shopping_list": [],
    "fridge": [],
    "vegetarian": False,
    "gluten_free": False,
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def get_api_key() -> str | None:
    try:
        key = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        return None
    # Ігноруємо заглушку з шаблону secrets.toml
    return key if key and not key.startswith("вставте") else None


@st.cache_resource(show_spinner=False)
def get_agent(api_key: str):
    return build_agent(api_key)


def diet_state() -> dict:
    return {"vegetarian": st.session_state.vegetarian, "gluten_free": st.session_state.gluten_free}


# ---------------------------------------------------------------------------
# Sidebar: холодильник, обмеження, список покупок
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🧊 Мій холодильник")
    st.multiselect(
        "Що є в наявності",
        options=AVAILABLE_INGREDIENTS,
        key="fridge",
        placeholder="Оберіть інгредієнти",
    )
    st.caption("Зміни враховуються одразу в наступній відповіді.")

    st.divider()
    st.subheader("🥗 Дієтичні обмеження")
    st.checkbox("Вегетаріанське", key="vegetarian")
    st.checkbox("Без глютену", key="gluten_free")

    st.divider()
    st.subheader("🛒 Список покупок")
    if st.session_state.shopping_list:
        for item in st.session_state.shopping_list:
            st.write(f"• {item}")
        if st.button("Очистити список", use_container_width=True):
            st.session_state.shopping_list = []
            st.rerun()
    else:
        st.caption("Порожньо. Додайте відсутні інгредієнти з картки рецепта.")

    st.divider()
    if st.button("🗑️ Почати розмову заново", use_container_width=True):
        st.session_state.messages = []
        st.session_state.suggested_recipes = []
        st.rerun()

# ---------------------------------------------------------------------------
# Головна область
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="cb-hero"><p class="cb-eyebrow">Кулінарний AI-асистент для родинної кухні</p>'
    '<div class="cb-title">ChefBot</div><div class="cb-rule"></div>'
    '<p class="cb-sub">Рецепти з того, що є під рукою, перерахунок мір і замінники інгредієнтів</p></div>',
    unsafe_allow_html=True,
)

# Активний контекст: користувач бачить те саме, що бачить агент
fridge = st.session_state.fridge
restrictions = [n for f, n in [(st.session_state.vegetarian, "вегетаріанське"),
                               (st.session_state.gluten_free, "без глютену")] if f]
st.markdown(
    f'<div class="cb-context"><span class="lbl">Холодильник</span>{", ".join(fridge) if fridge else "порожній"}'
    f'<br><span class="lbl">Обмеження</span>{", ".join(restrictions) if restrictions else "немає"}</div>',
    unsafe_allow_html=True,
)

# Картки рецептів
recipes = st.session_state.suggested_recipes
if recipes:
    st.subheader("Рекомендовані рецепти")
    cols = st.columns(min(len(recipes), 3))
    for i, recipe in enumerate(recipes):
        with cols[i % 3]:
            with st.container(border=True):
                if recipe.get("image"):
                    st.image(recipe["image"], use_container_width=True)
                st.markdown(f"#### {recipe['name']}")
                tags = ["⏱️ " + recipe.get("time", "—")]
                if recipe.get("vegetarian"):
                    tags.append("🌱 вегетаріанське")
                if recipe.get("gluten_free"):
                    tags.append("🌾 без глютену")
                st.caption(" · ".join(tags))
                st.write(recipe.get("description", ""))

                with st.expander("📋 Інгредієнти"):
                    if recipe.get("amounts"):
                        for item, qty in recipe["amounts"]:
                            st.write(f"• {item} — **{qty}**")
                        st.caption("Немає вдома: " + (", ".join(i for i in recipe.get("ingredients", []) if i not in fridge) or "усе є"))
                    else:
                        for ing in recipe.get("ingredients", []):
                            mark = "✅" if ing in fridge else "🛒"
                            st.write(f"{mark} {ing}")

                with st.expander("👩‍🍳 Приготування"):
                    for n, step in enumerate(recipe.get("steps", []), 1):
                        st.write(f"{n}. {step}")

                missing = [ing for ing in recipe.get("ingredients", []) if ing not in fridge]
                if missing:
                    if st.button(f"🛒 Додати відсутнє ({len(missing)})", key=f"shop_{i}_{recipe['name']}",
                                 use_container_width=True):
                        for ing in missing:
                            if ing not in st.session_state.shopping_list:
                                st.session_state.shopping_list.append(ing)
                        st.rerun()
                else:
                    st.success("Усе є в холодильнику", icon="✅")
    st.divider()

# Додати власний рецепт (зберігається в recipes_user.json поруч із застосунком)
with st.expander("➕ Додати свій рецепт"):
    with st.form("add_recipe", clear_on_submit=True):
        n_name = st.text_input("Назва страви")
        c1, c2 = st.columns(2)
        n_time = c1.text_input("Час", placeholder="45 хв")
        n_serv = c2.number_input("Порції", 1, 24, 4)
        n_desc = st.text_input("Короткий опис")
        n_ing = st.text_area("Інгредієнти — кожен з нового рядка: «Назва — кількість»")
        n_steps = st.text_area("Приготування — кожен крок з нового рядка")
        f1, f2, f3 = st.columns(3)
        n_veg = f1.checkbox("Вегетаріанське"); n_gf = f2.checkbox("Без глютену"); n_nut = f3.checkbox("Містить горіхи")
        n_img = st.file_uploader("Фото страви", type=["jpg", "jpeg", "png", "webp"])
        if st.form_submit_button("Зберегти рецепт"):
            amounts = [[p.split("—")[0].strip(), (p.split("—", 1)[1].strip() if "—" in p else "за смаком")] for p in n_ing.splitlines() if p.strip()]
            steps = [s.strip() for s in n_steps.splitlines() if s.strip()]
            if not n_name.strip() or not amounts or not steps:
                st.error("Вкажіть назву, хоча б один інгредієнт і один крок.")
            else:
                from agent import add_user_recipe
                img_path = ""
                if n_img is not None:
                    img_dir = Path(__file__).with_name("images"); img_dir.mkdir(exist_ok=True)
                    img_path = str(img_dir / f"user_{abs(hash(n_name))}.{n_img.name.rsplit('.', 1)[-1]}")
                    Path(img_path).write_bytes(n_img.getvalue())
                add_user_recipe({"name": n_name.strip(), "time": n_time or "—", "servings": int(n_serv), "category": "Мої рецепти",
                                 "description": n_desc, "amounts": amounts, "ingredients": [a[0].lower() for a in amounts],
                                 "steps": steps, "vegetarian": n_veg, "gluten_free": n_gf, "contains_nuts": n_nut, "image": img_path})
                st.success(f"Рецепт «{n_name}» додано — ChefBot уже знаходить його в пошуку.")

# Бібліотека: соуси й кухонний довідник
_lib = Path(__file__).with_name("sauces_tips.json")
if _lib.exists():
    LIB = json.loads(_lib.read_text(encoding="utf-8"))
    tab_s, tab_d, tab_h = st.tabs(["Соуси", "Напої", "Довідник"])
    with tab_s:
        scols = st.columns(4)
        for k, s in enumerate(LIB["sauces"]):
            with scols[k % 4]:
                with st.container(border=True):
                    img = Path(__file__).with_name("images") / s["img"]
                    if img.exists():
                        st.image(str(img), use_container_width=True)
                    st.markdown(f"**{s['name']}**")
                    st.caption(f"До страв: {s['for']} · {s['time']}")
                    with st.expander("Склад і кроки"):
                        for item, qty in s["amounts"]:
                            st.write(f"• {item} — **{qty}**")
                        for n, step in enumerate(s["steps"], 1):
                            st.write(f"{n}. {step}")
    with tab_d:
        for g in LIB.get("drinkGroups", []):
            c1, c2 = st.columns([1, 2])
            with c1:
                img = Path(__file__).with_name("images") / g["img"]
                if img.exists():
                    st.image(str(img), use_container_width=True)
            with c2:
                st.markdown(f"**{g['name']}**")
                st.caption(g["note"])
                for d in [d for d in LIB["drinks"] if d["group"] == g["id"]]:
                    st.write(f"• **{d['name']}** · {d['temp']} — {d['note']}")
        st.caption("Алкогольні напої — лише для дорослих 18+.")
    with tab_h:
        st.markdown("**Міри: склянка (250 мл), cup (240 мл), столова ложка**")
        st.table([{"Продукт": r[0], "Склянка": r[1].split("≈ ")[1], "Cup": r[2].split("≈ ")[1], "Ст. л.": r[3].split("≈ ")[1]} for r in LIB["measures"]])
        st.markdown("**Температура духовки**")
        st.table([{"Режим": r[0], "°C": r[1], "°F": r[2], "Для чого": r[3]} for r in LIB["oven"]])
        st.markdown("**Маленькі секрети**")
        for title, text in LIB["tips"]:
            st.write(f"• **{title}.** {text}")
    st.divider()

# Історія чату
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

quick_prompt = None
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.markdown(
            "Привіт! Я ChefBot 🍳 Відмітьте ліворуч, що є в холодильнику, "
            "і я підкажу, що з цього приготувати. А ще перерахую міри й підберу замінники."
        )
    st.caption("Спробуйте одразу:")
    qcols = st.columns(len(QUICK_PROMPTS))
    for col, text in zip(qcols, QUICK_PROMPTS):
        if col.button(text, use_container_width=True):
            quick_prompt = text

# ---------------------------------------------------------------------------
# Обробка запиту
# ---------------------------------------------------------------------------
api_key = get_api_key()
typed = st.chat_input("Запитайте про рецепт, міри або замінники…", disabled=not api_key)
if not api_key:
    st.warning("Додайте GOOGLE_API_KEY у файл .streamlit/secrets.toml і перезапустіть застосунок.", icon="🔑")

prompt = typed or quick_prompt
if prompt and api_key:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    tool_results: list[dict] = []
    with st.chat_message("assistant"):
        try:
            with st.spinner("ChefBot шукає відповідь…"):
                response = st.write_stream(
                    stream_reply(get_agent(api_key), st.session_state.messages,
                                 st.session_state.fridge, diet_state(), tool_results)
                )
            if not response:
                response = "Не вдалося сформулювати відповідь. Спробуйте перефразувати запит."
                st.markdown(response)
        except Exception as error:
            response = "⚠️ Не вдалося отримати відповідь. Перевірте API-ключ і з'єднання, потім спробуйте ще раз."
            st.error(response)
            st.caption(f"Технічна деталь: {type(error).__name__}")

    st.session_state.messages.append({"role": "assistant", "content": response})

    # Знайдені рецепти показуємо картками над чатом
    for result in tool_results:
        if result["name"] == "recipe_search":
            try:
                found = json.loads(result["content"]).get("recipes", [])
            except (json.JSONDecodeError, AttributeError):
                found = []
            # Страховка: картка не покаже страву, що порушує активні обмеження,
            # навіть якщо модель забула передати прапорець в інструмент
            diet = diet_state()
            found = [r for r in found
                     if not (diet["vegetarian"] and not r.get("vegetarian"))
                     and not (diet["gluten_free"] and not r.get("gluten_free"))]
            if found:
                st.session_state.suggested_recipes = found
                st.rerun()
