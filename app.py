import streamlit as st
import pandas as pd
import json
import pathlib
from datetime import date, datetime, timedelta

# Importeer alles uit planner_core (inclusief get_weather)
from planner_core import Task, greedy_plan, weighted_plan, summarize, sensitivity_analysis, get_weather, sample_tasks, clothing_advice

# --- Data persistentie (opslaan tussen sessies) ---
DATA_FILE = pathlib.Path("tasks.json")
REFLECTION_FILE = pathlib.Path("reflections.json")

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_data(tasks):
    DATA_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

def load_reflections():
    if REFLECTION_FILE.exists():
        try:
            return json.loads(REFLECTION_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_reflections(reflections):
    REFLECTION_FILE.write_text(json.dumps(reflections, ensure_ascii=False, indent=2), encoding="utf-8")

# --- Pagina instellingen ---
st.set_page_config(page_title="LIFE OS | Dagkompas", page_icon="🧭", layout="wide")

# --- Styles ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif}
.block-container{max-width:1250px;padding-top:2rem}
.hero{background:#202820;color:#f4f1e9;padding:2rem 2.2rem;border-radius:18px;margin-bottom:1.2rem}
.hero h1{font-family:'Playfair Display',serif;font-size:3.1rem;margin:.3rem 0;color:#f4f1e9}
.kicker{font-family:'DM Mono',monospace;letter-spacing:.15em;color:#c8e58b;font-size:.75rem}
.hero p{color:#d9dfd3;max-width:760px}
.note{background:#e8eddf;border-left:4px solid #8ba765;padding:1rem;border-radius:0 10px 10px 0}
.ai-card{background:#e0f0d0;border-radius:12px;padding:1.5rem;margin-bottom:1.5rem;border:1px solid #c8e58b}
</style>
""", unsafe_allow_html=True)

# --- State initialiseren ---
if "tasks" not in st.session_state:
    st.session_state.tasks = load_data()
if "reflections" not in st.session_state:
    st.session_state.reflections = load_reflections()

# --- Live weer ophalen ---
weather_cond, temp, wind, weather_vibe = get_weather()

st.markdown(f"""
<div class="hero">
<div class="kicker">VWO 6 · PYTHON PROJECT · EXPERIMENT 02</div>
<h1>LIFE OS <span style="color:#c8e58b">/</span> Dagkompas</h1>
<p>Een dagelijkse planner die tijd, deadlines, belang en energie combineert. <b>Met AI-weerintegratie en slimme taken-suggesties.</b></p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="note"><b>Belangrijk:</b> Dit prototype gebruikt live data van Open-Meteo om je planning aan te passen aan het weer en je energielevel. De taken die je invoert worden hierop beconciderd.</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("🧭 Jouw dag")
    chosen_date = st.date_input("Datum", value=date.today())
    start_time = st.time_input("Starttijd", value=datetime(2026, 1, 1, 9, 0))
    end_time = st.time_input("Eindtijd", value=datetime(2026, 1, 1, 12, 0))
    total_minutes = int((end_time.hour * 60 + end_time.minute) - (start_time.hour * 60 + start_time.minute))
    if total_minutes <= 0:
        st.error("Eindtijd moet later zijn dan de starttijd.")
        total_minutes = 0
    else:
        st.caption(f"Vrij: {total_minutes} minuten ({total_minutes // 60}u {total_minutes % 60:02d}m)")
    energy = st.slider("Energie / concentratie", 1, 5, 3, help="1 = weinig energie, 5 = veel energie")
    
    # Weer automatisch geladen (één keer!)
    weather = st.selectbox("Weer (Live data)", [weather_cond], index=0)
    
    st.caption(f"Huidige temperatuur: {temp}°C · Wind: {wind} km/u")


# --- Taken inlezen ---
tasks = []
for item in st.session_state.tasks:
    try:
        tasks.append(Task(
            name=item["name"], duration=int(item["duration"]), importance=int(item["importance"]),
            urgency=int(item["urgency"]), energy=int(item["energy"]), category=item["category"],
            deadline_days=int(item["deadline_days"]), flexible=bool(item["flexible"])
        ))
    except (KeyError, TypeError, ValueError):
        continue

# --- Tabs ---
tab_plan, tab_tasks, tab_lab, tab_reflect = st.tabs(["📅 Dagplan", "🧩 Taken beheren", "🧪 Wat-als-lab", "🪞 Reflectie & export"])

# --- Tab 1: Plan ---
with tab_plan:
    # --- AI & Kledingadvies ---
    advice = clothing_advice(weather_cond, temp)

    weer_extra = ""
    if "regen" in weather.lower() or "sneeuw" in weather.lower() or "onweer" in weather.lower():
        weer_extra = "<p style='color:#a33;margin:.4rem 0 0'><b>Slecht weer: focus op taken die binnenshuis kunnen!</b></p>"

    energie_tip = ""
    if energy <= 2:
        energie_tip = "<p style='margin:.4rem 0 0'>Begin met een snelle win-taak (klein en eenvoudig) om op gang te komen.</p>"
    elif energy >= 4:
        energie_tip = "<p style='margin:.4rem 0 0'>Veel energie! Plan de zwaarste taak nu, nog voor je moe wordt.</p>"

    # Bouw de HTML op met + in plaats van f-string
    html = (
        '<div class="ai-card">'
        '<h3 style="margin-top:0">AI Assistent &amp; Context</h3>'
        '<div style="display:flex;gap:2rem;flex-wrap:wrap">'
        '<div style="flex:1;min-width:260px">'
        '<b>Huidig Weer:</b> ' + weather + ' (' + str(temp) + '&deg;C)'
        '<p style="color:#555;font-size:.85rem">' + weather_vibe + '</p>'
        + weer_extra +
        '</div>'
        '<div style="flex:1;min-width:260px">'
        '<b>Jouw Energie:</b> ' + str(energy) + '/5'
        + energie_tip +
        '</div>'
        '</div>'
        '</div>'
        '<div class="note" style="margin-bottom:1.5rem">'
        '<b>Kledingadvies:</b> ' + advice +
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

    st.subheader(f"Jouw plan voor {chosen_date.strftime('%d-%m-%Y')}")
    c1, c2, c3 = st.columns(3)
    plan = greedy_plan(tasks, total_minutes, energy)
    summary = summarize(plan, total_minutes)
    c1.metric("Taken ingepland", summary["tasks_done"])
    c2.metric("Tijd ingepland", f"{summary['planned_minutes']} min")
    c3.metric("Ruimte over", f"{summary['free_minutes']} min")
    
    if plan:
        st.write("### Aanbevolen volgorde")
        for idx, item in enumerate(plan, start=1):
            task = item["task"]
            start = item["start_minute"]
            end = start + task.duration
            with st.container(border=True):
                a, b, c = st.columns([0.6, 4, 1.2])
                a.markdown(f"## {idx:02d}")
                b.markdown(f"**{task.name}**")
                b.caption(f"{task.category} · belang {task.importance}/5 · urgentie {task.urgency}/5 · benodigde energie {task.energy}/5")
                start_dt = datetime(2026, 1, 1, start_time.hour, start_time.minute) + timedelta(minutes=start)
                end_dt = start_dt + timedelta(minutes=task.duration)
                c.markdown(f"**{start_dt.strftime('%H:%M')}–{end_dt.strftime('%H:%M')}**")
    else:
        st.warning("Geen taken ingepland. Voeg taken toe in tab 'Taken beheren' om een plan te genereren.")
        
    st.write("### Contextcheck")
st.write(f"Weer: **{weather}** · Energie: **{energy}/5**")

# --- Tab 2: Taken Beheren ---
with tab_tasks:
    st.subheader("Takenlijst")
    if st.session_state.tasks:
        for idx, task in enumerate(st.session_state.tasks):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"**{task['name']}**")
                st.caption(f"{task['duration']} min · {task['category']} · belang {task['importance']}/5 · urgentie {task['urgency']}/5 · energie {task['energy']}/5 · deadline over {task['deadline_days']} dagen · {'verplaatsbaar' if task['flexible'] else 'vast'}")
            with col2:
                pass
            with col3:
                if st.button("🗑️ Verwijderen", key=f"del_{idx}"):
                    st.session_state.tasks.pop(idx)
                    save_data(st.session_state.tasks)
                    st.rerun()
    else:
        st.info("Nog geen taken toegevoegd. Voeg hieronder je eigen taken toe.")

    st.write("### Voeg een taak toe")
    with st.form("add_task", clear_on_submit=True):
        name = st.text_input("Naam taak")
        col1, col2, col3 = st.columns(3)
        duration = col1.number_input("Duur (minuten)", 5, 300, 30, step=5)
        importance = col2.slider("Belang (1–5)", 1, 5, 3)
        urgency = col3.slider("Urgentie (1–5)", 1, 5, 3)
        col4, col5, col6 = st.columns(3)
        task_energy = col4.slider("Benodigde energie (1–5)", 1, 5, 3)
        category = col5.selectbox("Categorie", ["School", "Werk", "Thuis", "Gezondheid", "Sociaal", "Overig"])
        deadline = col6.number_input("Deadline over (dagen)", 0, 30, 1)
        flexible = st.checkbox("Deze taak kan worden verplaatst", value=True)
        submitted = st.form_submit_button("Taak toevoegen", type="primary")
        if submitted:
            if name.strip():
                st.session_state.tasks.append({
                    "name":name.strip(), "duration":int(duration), "importance":importance,
                    "urgency":urgency, "energy":task_energy, "category":category,
                    "deadline_days":int(deadline), "flexible":flexible
                })
                save_data(st.session_state.tasks)
                st.success(f"'{name}' toegevoegd. Ga naar 'Dagplan' om te zien hoe de AI dit inpland.")
                st.rerun()
            else:
                st.error("Geef de taak eerst een naam.")

# --- Tab 3: Lab ---
with tab_lab:
    st.subheader("🧪 Wat-als-lab: verandert één variabele de uitkomst?")
    baseline = greedy_plan(tasks, total_minutes, energy)
    simple = weighted_plan(tasks, total_minutes, energy)
    names_a = [x["task"].name for x in baseline]
    names_b = [x["task"].name for x in simple]
    a, b = st.columns(2)
    with a:
        st.markdown("#### LIFE OS-algoritme")
        st.write(" → ".join(names_a) if names_a else "Geen taken ingepland")
        st.caption(f"{len(names_a)} taken · {sum(x['task'].duration for x in baseline)} minuten")
    with b:
        st.markdown("#### Baseline: belang/urgentie per minuut")
        st.write(" → ".join(names_b) if names_b else "Geen taken ingepland")
        st.caption(f"{len(names_b)} taken · {sum(x['task'].duration for x in simple)} minuten")
    st.metric("Zelfde takenvolgorde?", "Ja" if names_a == names_b else "Nee")
    st.write("### Gevoeligheidsanalyse")
    scenarios = sensitivity_analysis(tasks, total_minutes, energy)
    scenario_rows = []
    for s in scenarios:
        scenario_rows.append({
            "Scenario":s["scenario"], "Aanpassing":s["change"],
            "Nieuwe volgorde":" → ".join(s["order"]) if s["order"] else "Geen taken",
            "Volgorde verschilt": "Ja" if s["changed"] else "Nee"
        })
    st.dataframe(pd.DataFrame(scenario_rows), use_container_width=True, hide_index=True)

# --- Tab 4: Reflectie ---
with tab_reflect:
    st.subheader("🪞 Onderzoekslogboek")
    with st.form("reflection_form", clear_on_submit=True):
        experiment = st.text_input("Experiment / datum", value=str(chosen_date))
        hypothesis = st.text_area("Hypothese", placeholder="Ik verwacht dat ... omdat ...")
        change = st.text_area("Wat heb je veranderd?", placeholder="Ik veranderde alleen ... en hield ... gelijk.")
        observation = st.text_area("Wat gebeurde er?", placeholder="De planning veranderde wel/niet doordat ...")
        limitation = st.text_area("Beperking of verrassing", placeholder="Het model houdt geen rekening met ...")
        next_step = st.text_area("Volgende verbetering", placeholder="De volgende versie moet ...")
        save = st.form_submit_button("Reflectie opslaan", type="primary")
        if save:
            st.session_state.reflections.append({
                "experiment":experiment, "hypothesis":hypothesis, "change":change,
                "observation":observation, "limitation":limitation, "next_step":next_step
            })
            save_reflections(st.session_state.reflections)  # Opslaan naar bestand
            st.success("Reflectie opgeslagen in deze sessie.")
            st.rerun()
    if st.session_state.reflections:
        st.write("### Eerdere reflecties")
        st.dataframe(pd.DataFrame(st.session_state.reflections), use_container_width=True, hide_index=True)
    
    export = {
        "date": str(chosen_date),
        "context": {"available_minutes": total_minutes, "energy": energy, "weather": weather},
        "tasks": st.session_state.tasks,
        "reflections": st.session_state.reflections,
        "model_note": "Heuristisch prototype; scores zijn aannames en geen gevalideerde voorspellingen."
    }
    st.download_button("⬇ Download je data en reflecties (JSON)",
                       data=json.dumps(export, ensure_ascii=False, indent=2),
                       file_name="life_os_logboek.json", mime="application/json")
    st.download_button("⬇ Download taken (CSV)",
                       data=pd.DataFrame(st.session_state.tasks).to_csv(index=False).encode("utf-8-sig"),
                       file_name="life_os_taken.csv", mime="text/csv")

st.divider()
st.caption("LIFE OS is een prototype. De gegevens worden opgeslagen in je projectmap (tasks.json en reflections.json).")