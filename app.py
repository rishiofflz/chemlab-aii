import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import re
from collections import Counter
from datetime import datetime

st.set_page_config(
    page_title="NEBULA CHEM | Molecular Universe",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- NEON INTERFACE ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
:root { --cyan:#5ef2ff; --violet:#a78bfa; --green:#8cffb5; --ink:#eef5ff; }
html, body, [class*="css"] { font-family:Inter,sans-serif; }
.stApp {
 background:
 radial-gradient(ellipse at 12% 8%, rgba(0,210,255,.15), transparent 30%),
 radial-gradient(ellipse at 88% 15%, rgba(139,92,246,.16), transparent 32%),
 linear-gradient(135deg,#050914 0%,#080d1b 55%,#09091a 100%);
 color:var(--ink);
}
[data-testid="stSidebar"] {
 background:linear-gradient(180deg,#0b1325,#101026);
 border-right:1px solid rgba(94,242,255,.22);
}
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; color:#f4f8ff; }
p, label, .stMarkdown { color:#c6d5ed; }
.hero {
 padding:28px 30px; border:1px solid rgba(94,242,255,.35);
 border-radius:24px; margin:10px 0 25px;
 background:linear-gradient(115deg,rgba(14,34,58,.88),rgba(34,20,65,.66));
 box-shadow:0 0 35px rgba(36,213,255,.09), inset 0 0 30px rgba(167,139,250,.05);
}
.eyebrow { color:var(--cyan); letter-spacing:3px; font-size:.75rem; font-weight:800; }
.gradient {
 background:linear-gradient(90deg,#5ef2ff,#a78bfa,#8cffb5);
 -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.subtle { color:#9aacca; }
.neon-card {
 background:linear-gradient(145deg,rgba(18,31,55,.92),rgba(15,16,39,.92));
 border:1px solid rgba(94,242,255,.24); border-radius:18px;
 padding:19px 21px; min-height:132px;
 box-shadow:0 0 22px rgba(94,242,255,.045);
}
.card-label { color:#8ea8cb; font-size:.74rem; letter-spacing:1.5px; text-transform:uppercase; }
.card-value { color:#f4f8ff; font-family:'Space Grotesk'; font-size:1.42rem; font-weight:700; margin-top:9px; }
.card-note { color:#9aacca; font-size:.83rem; margin-top:5px; }
div[data-testid="stMetric"] {
 background:rgba(15,27,48,.82); border:1px solid rgba(94,242,255,.22);
 padding:14px; border-radius:14px;
}
div[data-testid="stMetricLabel"] { color:#9aacca; }
.stButton>button {
 border:1px solid #5ef2ff; border-radius:11px;
 background:linear-gradient(100deg,#5ef2ff,#a78bfa);
 color:#06101c; font-weight:800; transition:.2s;
}
.stButton>button:hover { box-shadow:0 0 18px rgba(94,242,255,.45); border-color:#fff; }
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
 background:#0c1425 !important; color:#eef5ff !important;
 border-color:rgba(94,242,255,.28) !important;
}
.stTabs [data-baseweb="tab"] { background:#101a30; border-radius:10px 10px 0 0; }
hr { border-color:rgba(94,242,255,.2); }
div[data-testid="stAlert"] { border-radius:12px; }
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------- CHEMISTRY ENGINE ----------
ELEMENTS = {
    "H":("Hydrogen",1,1.008), "C":("Carbon",6,12.011), "N":("Nitrogen",7,14.007),
    "O":("Oxygen",8,15.999), "F":("Fluorine",9,18.998), "Na":("Sodium",11,22.990),
    "Mg":("Magnesium",12,24.305), "Al":("Aluminium",13,26.982), "Si":("Silicon",14,28.085),
    "P":("Phosphorus",15,30.974), "S":("Sulfur",16,32.06), "Cl":("Chlorine",17,35.45),
    "K":("Potassium",19,39.098), "Ca":("Calcium",20,40.078), "Fe":("Iron",26,55.845),
    "Cu":("Copper",29,63.546), "Zn":("Zinc",30,65.38), "Br":("Bromine",35,79.904),
    "Ag":("Silver",47,107.868), "I":("Iodine",53,126.904), "Ba":("Barium",56,137.327),
    "Au":("Gold",79,196.967), "Hg":("Mercury",80,200.592), "Pb":("Lead",82,207.2)
}

def parse_formula(formula):
    formula = formula.replace(" ", "")
    if not formula or not re.fullmatch(r"[A-Za-z0-9()]+", formula):
        raise ValueError("Use element symbols, subscripts as numbers, and parentheses only.")
    tokens = re.findall(r"[A-Z][a-z]?|\d+|[()]", formula)
    if "".join(tokens) != formula:
        raise ValueError("Check element capitalization and formula syntax.")
    stack, i = [Counter()], 0
    while i < len(tokens):
        token = tokens[i]
        if token == "(":
            stack.append(Counter())
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("Unmatched closing parenthesis.")
            group = stack.pop()
            i += 1
            mult = int(tokens[i]) if i < len(tokens) and tokens[i].isdigit() else 1
            if mult < 1: raise ValueError("Subscripts must be positive.")
            stack[-1].update({k:v*mult for k,v in group.items()})
            if i < len(tokens) and tokens[i].isdigit():
                pass
        elif token.isdigit():
            raise ValueError("A number must follow an element or closing parenthesis.")
        else:
            if token not in ELEMENTS:
                raise ValueError(f"'{token}' is not in this app's element dataset.")
            i += 1
            count = int(tokens[i]) if i < len(tokens) and tokens[i].isdigit() else 1
            if count < 1: raise ValueError("Subscripts must be positive.")
            stack[-1][token] += count
            if i < len(tokens) and tokens[i].isdigit():
                pass
        i += 1
    if len(stack) != 1: raise ValueError("Unmatched opening parenthesis.")
    if not stack[0]: raise ValueError("Could not read the formula.")
    return stack[0]

def formula_mass(counts):
    return sum(ELEMENTS[e][2] * n for e,n in counts.items())

def balance_equation(equation):
    try:
        import sympy as sp
        import math
    except Exception:
        return None, "SymPy is missing. Add sympy to requirements.txt and redeploy."
    parts = re.split(r"\s*(?:->|→|=)\s*", equation.strip())
    if len(parts) != 2: return None, "Use a format such as H2 + O2 -> H2O."
    left, right = [x.strip() for x in parts[0].split("+")], [x.strip() for x in parts[1].split("+")]
    if any(not x for x in left + right): return None, "Separate each substance with +."
    try:
        formulas = [parse_formula(x) for x in left + right]
        elements = sorted(set().union(*(set(f) for f in formulas)))
        matrix = [[f.get(el,0) * (1 if j < len(left) else -1)
                   for j,f in enumerate(formulas)] for el in elements]
        null = sp.Matrix(matrix).nullspace()
        if not null: return None, "No balance found. Check the formulas."
        vec = null[0]
        lcm = sp.ilcm(*[int(v.q) for v in vec])
        nums = [int(v*lcm) for v in vec]
        if all(n < 0 for n in nums): nums = [-n for n in nums]
        if any(n <= 0 for n in nums): return None, "This equation needs a different balancing method."
        gcd = math.gcd(*nums)
        nums = [n//gcd for n in nums]
        render = lambda fs, ns: " + ".join(("" if n == 1 else str(n)) + f for f,n in zip(fs,ns))
        return render(left,nums[:len(left)]) + " → " + render(right,nums[len(left):]), None
    except Exception as exc:
        return None, str(exc)

# ---------- OPTIONAL 3D ENGINE ----------
def make_3d_html(smiles, style):
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        import py3Dmol
        mol = Chem.MolFromSmiles(smiles)
        if mol is None: return None, "That SMILES string could not be parsed."
        mol = Chem.AddHs(mol)
        status = AllChem.EmbedMolecule(mol, randomSeed=7)
        if status != 0: return None, "3D coordinate generation failed for this molecule."
        AllChem.UFFOptimizeMolecule(mol, maxIters=200)
        block = Chem.MolToMolBlock(mol)
        viewer = py3Dmol.view(width=900, height=520)
        viewer.addModel(block, "mol")
        styles = {
            "Ball & stick":{"stick":{"radius":0.16},"sphere":{"scale":0.25}},
            "Space filling":{"sphere":{"scale":0.38}},
            "Stick":{"stick":{"radius":0.22}}
        }
        viewer.setStyle(styles[style])
        viewer.setBackgroundColor("#070d1b")
        viewer.zoomTo()
        return viewer._make_html(), None
    except ImportError:
        return None, "3D packages are not installed yet. Check requirements.txt and redeploy."
    except Exception as exc:
        return None, f"3D engine message: {exc}"

# ---------- SIDEBAR ----------
st.sidebar.markdown("# 🧬 NEBULA CHEM")
st.sidebar.markdown("<div class='subtle'>AI MOLECULAR UNIVERSE · STUDENT EDITION</div>", unsafe_allow_html=True)
page = st.sidebar.radio("NAVIGATION", [
    "Command Center", "3D Molecular Studio", "Molecular Intelligence",
    "Reaction Simulator", "Chemistry Assistant", "Research Report"
])
st.sidebar.markdown("---")
student_name = st.sidebar.text_input("Student name", placeholder="Enter your name")
reg_no = st.sidebar.text_input("Registration number", placeholder="Optional")
st.sidebar.markdown("---")
st.sidebar.caption("Digital chemistry learning environment. No physical laboratory procedures are performed here.")

# ---------- HERO ----------
st.markdown("""
<div class="hero">
 <div class="eyebrow">MOLECULES · COMPUTATION · DISCOVERY</div>
 <h1 style="font-size:3.15rem;line-height:1.05;margin:.55rem 0">
 Enter the <span class="gradient">Molecular Universe.</span>
 </h1>
 <p style="font-size:1.05rem;color:#a9bbd7;max-width:850px">
 A neon-lit computational chemistry workspace for exploring molecular geometry,
 chemical properties, reactions and scientific ideas.
 </p>
</div>
""", unsafe_allow_html=True)

# ---------- PAGES ----------
if page == "Command Center":
    st.subheader("◈ Mission Control")
    c1,c2,c3,c4 = st.columns(4)
    for col, label, value, note in [
        (c1,"CORE ENGINE","RDKit","Molecular structures"),
        (c2,"VISUAL MODE","3D / 2D","Interactive exploration"),
        (c3,"DATA TOOLS","Descriptors","Molecular properties"),
        (c4,"LEARNING MODE","Active","Concept-first workflow")
    ]:
        with col:
            st.markdown(f"<div class='neon-card'><div class='card-label'>{label}</div><div class='card-value'>{value}</div><div class='card-note'>{note}</div></div>",unsafe_allow_html=True)
    st.write("")
    left,right = st.columns([1.2,.8], gap="large")
    with left:
        st.markdown("### ✦ Welcome to your digital lab")
        st.write("Explore how molecular structure connects to measurable chemical properties. Enter a SMILES string, generate a 3D model, inspect descriptors, and compare your observations.")
        st.markdown("#### Suggested exploration path")
        st.markdown("**01** — Open the 3D Molecular Studio and load a sample molecule.  \n**02** — Inspect its shape and atom arrangement.  \n**03** — Review molecular descriptors.  \n**04** — Record findings in the research report.")
    with right:
        st.markdown("### ⚡ Quick launch")
        quick = st.selectbox("Choose a sample molecule", ["Water · O", "Ethanol · CCO", "Caffeine · Cn1c(=O)c2c(ncn2C)n(C)c1=O", "Glucose · C(C1C(C(C(C(O1)O)O)O)O)O"])
        if st.button("Open molecule in studio", use_container_width=True):
            st.session_state["smiles_input"] = quick.split(" · ",1)[1]
            st.session_state["selected_page"] = "3D Molecular Studio"
            st.info("Choose '3D Molecular Studio' from the sidebar to view it.")
    st.info("Presentation tip: demonstrate one molecule from input → 3D model → property report. This tells a clear scientific story.")

elif page == "3D Molecular Studio":
    st.subheader("✧ 3D Molecular Studio")
    st.write("Enter a SMILES string to generate a 3D molecular model. The 3D engine uses RDKit coordinates and py3Dmol rendering.")
    samples = {
        "Water":"O", "Methane":"C", "Ethanol":"CCO", "Acetic acid":"CC(=O)O",
        "Benzene":"c1ccccc1", "Caffeine":"Cn1c(=O)c2c(ncn2C)n(C)c1=O",
        "Glucose":"C(C1C(C(C(C(O1)O)O)O)O)O"
    }
    selected_sample = st.selectbox("Load an example", ["Custom"] + list(samples))
    default_smiles = samples[selected_sample] if selected_sample != "Custom" else st.session_state.get("smiles_input","CCO")
    smiles = st.text_input("SMILES notation", value=default_smiles, key="studio_smiles")
    style = st.selectbox("Rendering style", ["Ball & stick","Space filling","Stick"])
    if st.button("Generate 3D structure", type="primary"):
        html, error = make_3d_html(smiles, style)
        if error: st.error(error)
        else:
            st.success("3D structure generated.")
            components.html(html, height=550, scrolling=False)
            st.session_state["last_smiles"] = smiles
    st.caption("Tip: drag to rotate, scroll or pinch to zoom. 3D generation is a computational model, not an experimental structure.")

elif page == "Molecular Intelligence":
    st.subheader("◈ Molecular Intelligence")
    st.write("Calculate molecular descriptors from SMILES. Installations with RDKit enabled will show computed values.")
    smiles = st.text_input("SMILES notation", value=st.session_state.get("last_smiles","CCO"), key="descriptor_smiles")
    if st.button("Analyze molecular properties", type="primary"):
        try:
            from rdkit import Chem
            from rdkit.Chem import Descriptors, rdMolDescriptors
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                st.error("Invalid SMILES. Try CCO, c1ccccc1 or Cn1c(=O)c2c(ncn2C)n(C)c1=O.")
            else:
                data = {
                    "Molecular weight (g/mol)": Descriptors.MolWt(mol),
                    "LogP": Descriptors.MolLogP(mol),
                    "H-bond donors": Descriptors.NumHDonors(mol),
                    "H-bond acceptors": Descriptors.NumHAcceptors(mol),
                    "TPSA (Å²)": rdMolDescriptors.CalcTPSA(mol),
                    "Rotatable bonds": Descriptors.NumRotatableBonds(mol),
                    "Heavy atoms": mol.GetNumHeavyAtoms(),
                    "Formula": rdMolDescriptors.CalcMolFormula(mol)
                }
                a,b,c = st.columns(3)
                a.metric("Molecular weight",f"{data['Molecular weight (g/mol)']:.2f} g/mol")
                b.metric("LogP",f"{data['LogP']:.2f}")
                c.metric("Molecular formula",data["Formula"])
                st.markdown("#### Descriptor report")
                df = pd.DataFrame([{"Property":k,"Value":round(v,3) if isinstance(v,float) else v} for k,v in data.items()])
                st.dataframe(df,use_container_width=True,hide_index=True)
                numeric = {k:v for k,v in data.items() if isinstance(v,(int,float))}
                fig = px.bar(x=list(numeric.values()),y=list(numeric.keys()),orientation="h",
                             labels={"x":"Calculated value","y":"Descriptor"},
                             title="Molecular descriptor profile",template="plotly_dark")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig,use_container_width=True)
                st.session_state["last_report"] = {"smiles":smiles,**data}
        except ImportError:
            st.error("RDKit is unavailable. Check requirements.txt and redeploy the app.")
    st.caption("Descriptors are calculated estimates from the selected molecular representation. They are not a substitute for experimental measurements.")

elif page == "Reaction Simulator":
    st.subheader("⚡ Reaction Simulator")
    st.write("Balance a chemical equation by conserving the number of atoms of each element.")
    equation = st.text_input("Unbalanced equation", "H2 + O2 -> H2O")
    if st.button("Balance reaction",type="primary"):
        balanced,error = balance_equation(equation)
        if error: st.error(error)
        else:
            st.success(balanced)
            st.markdown("**Conservation principle:** the number of atoms of every element is equal on both sides. The formulas remain unchanged; only coefficients are adjusted.")
    st.markdown("#### Practice examples")
    st.code("Fe + O2 -> Fe2O3\nNa + Cl2 -> NaCl\nC3H8 + O2 -> CO2 + H2O")
    st.caption("Educational equation balancer for common classroom examples; unusual reaction systems may need a different method.")

elif page == "Chemistry Assistant":
    st.subheader("✦ Chemistry Concept Assistant")
    st.write("Ask a chemistry concept question. This built-in edition uses a curated knowledge bank and is not connected to a live AI model.")
    knowledge = {
        "bond": "A chemical bond is an attractive interaction that holds atoms or ions together. Common models include covalent, ionic and metallic bonding.",
        "smiles": "SMILES means Simplified Molecular Input Line Entry System. It represents a molecular structure as a text string.",
        "logp": "LogP estimates how a neutral compound partitions between an octanol-like phase and water. It is often used as one indicator of relative lipophilicity.",
        "tpsa": "Topological polar surface area (TPSA) is a calculated descriptor related to the polar surface contributions of atoms in a molecule.",
        "mole": "One mole contains exactly 6.02214076 × 10²³ specified entities. Molar mass is commonly expressed in grams per mole.",
        "geometry": "Molecular geometry describes the three-dimensional arrangement of atoms. Electron-pair repulsion models are often used for introductory predictions.",
        "reaction": "A chemical reaction rearranges atoms as reactants form products. A balanced equation represents conservation of each element."
    }
    question = st.text_input("Your question", placeholder="Example: What is molecular geometry?")
    if st.button("Explain concept"):
        q = question.lower()
        matches = [v for k,v in knowledge.items() if k in q]
        if matches: st.info(matches[0])
        elif any(w in q for w in ["acid","base","ph"]):
            st.info("In the Brønsted–Lowry model, acids donate protons and bases accept protons. pH is commonly used to describe acidity in aqueous solutions.")
        elif any(w in q for w in ["atom","element","proton"]):
            st.info("An element is defined by its number of protons. Atoms contain protons and neutrons in the nucleus, with electrons around the nucleus.")
        else:
            st.warning("I don't have a prepared explanation for that wording yet. Try asking about bonds, SMILES, LogP, TPSA, moles, geometry or reactions.")
    st.caption("For an actual generative AI chatbot, connect a trusted model API using Streamlit secrets. Never place API keys directly in public GitHub code.")

elif page == "Research Report":
    st.subheader("▤ Student Research Report")
    st.write("Create a concise project record from the information entered in this session.")
    title = st.text_input("Project title", "Computational Exploration of Molecular Structures")
    objective = st.text_area("Project objective", "To explore molecular structures and understand how molecular descriptors help describe chemical properties.")
    observation = st.text_area("Observations", "Record the molecule studied, its 3D shape, and the calculated molecular descriptors.")
    report = st.session_state.get("last_report", {})
    report_text = f"""NEBULA CHEM — STUDENT PROJECT REPORT
Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}

Student: {student_name or 'Not provided'}
Registration number: {reg_no or 'Not provided'}
Project: {title}

OBJECTIVE
{objective}

MOLECULE ANALYSIS
"""
    if report:
        report_text += "\n".join(f"{k}: {v}" for k,v in report.items())
    else:
        report_text += "No molecular descriptor analysis has been saved in this session."
    report_text += f"\n\nOBSERVATIONS\n{observation}\n\nNote: Computational learning output; verify scientific claims with course references."
    st.text_area("Report preview", report_text, height=360)
    st.download_button("⬇ Download report (.txt)", report_text,
                       file_name="nebula_chem_project_report.txt", mime="text/plain")
    st.info("Run a molecular analysis first to include calculated descriptors in this report.")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#7890b2;font-size:.8rem;letter-spacing:1px'>NEBULA CHEM · MOLECULAR UNIVERSE · BUILT FOR SCIENTIFIC LEARNING</div>", unsafe_allow_html=True)
