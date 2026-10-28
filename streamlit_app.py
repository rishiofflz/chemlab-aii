import streamlit as st
import re
from collections import Counter

st.set_page_config(
    page_title="ChemLab AI | Chemistry Explorer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root { --ink:#edf5ff; --muted:#9babc5; --cyan:#70e7f2; --violet:#a99bff; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background: radial-gradient(ellipse at 85% 0%, #202052 0%, transparent 38%), #080d19; color:var(--ink); }
[data-testid="stSidebar"] { background:#0d1425; border-right:1px solid #28334c; }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.7px; color:#f2f6ff; }
p, label, .stMarkdown { color:#c7d4e9; }
.hero { padding:1.6rem 0 1rem; }
.eyebrow { color:#70e7f2; letter-spacing:2px; font-size:.76rem; font-weight:700; }
.gradient { background:linear-gradient(100deg,#70e7f2,#b2a1ff); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }
.lead { color:#9babc5; font-size:1.06rem; max-width:780px; }
.panel { background:linear-gradient(145deg,#151f35,#0e1526); border:1px solid #2b3854; border-radius:18px; padding:20px 22px; min-height:130px; }
.panel-label { color:#91a5c8; font-size:.78rem; text-transform:uppercase; letter-spacing:1px; }
.panel-value { color:#f5f8ff; font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:700; margin-top:9px; }
.panel-note { color:#91a5c8; font-size:.83rem; margin-top:4px; }
div[data-testid="stMetric"] { background:#121b2e; border:1px solid #2b3854; padding:14px; border-radius:14px; }
div[data-testid="stMetricLabel"] { color:#9babc5; }
.stButton>button { border-radius:10px; border:1px solid #5dd7e5; background:linear-gradient(100deg,#70e7f2,#b2a1ff); color:#09111e; font-weight:700; }
.stTabs [data-baseweb="tab-list"] { gap:10px; }
.stTabs [data-baseweb="tab"] { background:#111a2d; border-radius:10px 10px 0 0; }
hr { border-color:#28334c; }
.small { font-size:.82rem; color:#91a5c8; }
</style>
""", unsafe_allow_html=True)

ELEMENTS = {
    "H": ("Hydrogen", 1, 1.008), "He": ("Helium", 2, 4.0026),
    "Li": ("Lithium", 3, 6.94), "Be": ("Beryllium", 4, 9.0122),
    "B": ("Boron", 5, 10.81), "C": ("Carbon", 6, 12.011),
    "N": ("Nitrogen", 7, 14.007), "O": ("Oxygen", 8, 15.999),
    "F": ("Fluorine", 9, 18.998), "Ne": ("Neon", 10, 20.180),
    "Na": ("Sodium", 11, 22.990), "Mg": ("Magnesium", 12, 24.305),
    "Al": ("Aluminium", 13, 26.982), "Si": ("Silicon", 14, 28.085),
    "P": ("Phosphorus", 15, 30.974), "S": ("Sulfur", 16, 32.06),
    "Cl": ("Chlorine", 17, 35.45), "Ar": ("Argon", 18, 39.948),
    "K": ("Potassium", 19, 39.098), "Ca": ("Calcium", 20, 40.078),
    "Fe": ("Iron", 26, 55.845), "Cu": ("Copper", 29, 63.546),
    "Zn": ("Zinc", 30, 65.38), "Br": ("Bromine", 35, 79.904),
    "Ag": ("Silver", 47, 107.868), "I": ("Iodine", 53, 126.904),
    "Ba": ("Barium", 56, 137.327), "Au": ("Gold", 79, 196.967),
    "Hg": ("Mercury", 80, 200.592), "Pb": ("Lead", 82, 207.2),
}

def parse_formula(formula):
    """Parse common chemical formulas with parentheses, e.g. Ca(OH)2."""
    formula = formula.replace(" ", "")
    if not formula or not re.fullmatch(r"[A-Za-z0-9()]+", formula):
        raise ValueError("Enter a formula using element symbols, numbers, and parentheses only.")
    token_pattern = re.compile(r"([A-Z][a-z]?|\d+|\(|\))")
    tokens = token_pattern.findall(formula)
    if "".join(tokens) != formula:
        raise ValueError("Check the formula's capitalization and symbols.")
    stack = [Counter()]
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "(":
            stack.append(Counter())
        elif tok == ")":
            if len(stack) == 1:
                raise ValueError("There is an unmatched closing parenthesis.")
            group = stack.pop()
            i += 1
            multiplier = int(tokens[i]) if i < len(tokens) and tokens[i].isdigit() else 1
            if multiplier < 1:
                raise ValueError("Subscripts must be positive integers.")
            stack[-1].update({el: n * multiplier for el, n in group.items()})
            if i < len(tokens) and tokens[i].isdigit():
                pass
        elif tok.isdigit():
            raise ValueError("A number must follow an element or a closing parenthesis.")
        else:
            if tok not in ELEMENTS:
                raise ValueError(f"Element symbol '{tok}' is not in this demo's element list.")
            i += 1
            count = int(tokens[i]) if i < len(tokens) and tokens[i].isdigit() else 1
            if count < 1:
                raise ValueError("Subscripts must be positive integers.")
            stack[-1][tok] += count
            if i < len(tokens) and tokens[i].isdigit():
                pass
        i += 1
    if len(stack) != 1:
        raise ValueError("There is an unmatched opening parenthesis.")
    if not stack[0]:
        raise ValueError("Could not read the formula.")
    return stack[0]

def formula_mass(counts):
    return sum(ELEMENTS[el][2] * n for el, n in counts.items())

def balance_equation(equation):
    # Educational balancer for simple equations using non-negative integer search.
    # It uses sympy if available; otherwise explain the limitation.
    try:
        from sympy import symbols
        from sympy.parsing.sympy_parser import parse_expr
        from sympy import Matrix
        from functools import reduce
        import math
    except Exception:
        return None, "Install sympy to use equation balancing."
    parts = re.split(r"\s*(?:->|→|=)\s*", equation.strip())
    if len(parts) != 2:
        return None, "Use an equation like H2 + O2 -> H2O."
    def side_formulas(side):
        fs = [x.strip() for x in side.split("+")]
        if not fs or any(not x for x in fs):
            raise ValueError("Separate formulas with + and use -> between sides.")
        return fs
    try:
        left, right = side_formulas(parts[0]), side_formulas(parts[1])
        formulas = [parse_formula(f) for f in left + right]
        elements = sorted(set().union(*(set(f.keys()) for f in formulas)))
        import sympy as sp
        mat = []
        for el in elements:
            mat.append([f.get(el, 0) for f in formulas[:len(left)]] +
                       [-f.get(el, 0) for f in formulas[len(left):]])
        null = sp.Matrix(mat).nullspace()
        if not null:
            return None, "No balance found. Check that the formulas are correct."
        vec = null[0]
        denoms = [int(v.q) for v in vec]
        lcm = sp.ilcm(*denoms)
        nums = [int(v*lcm) for v in vec]
        if all(n < 0 for n in nums):
            nums = [-n for n in nums]
        if any(n <= 0 for n in nums):
            return None, "This equation needs a different balancing approach."
        gcd = math.gcd(*nums)
        nums = [n//gcd for n in nums]
        def render(fs, ns):
            return " + ".join((("" if n == 1 else str(n)) + f) for f, n in zip(fs, ns))
        return render(left, nums[:len(left)]) + " → " + render(right, nums[len(left):]), None
    except Exception as e:
        return None, str(e)

st.sidebar.markdown("## 🧪 ChemLab AI")
st.sidebar.caption("Chemistry learning studio")
page = st.sidebar.radio("Navigate", ["Overview", "Formula Analyzer", "Equation Balancer", "Periodic Table", "Learn & Quiz"])
st.sidebar.markdown("---")
st.sidebar.markdown("**Learning first**")
st.sidebar.caption("Use this app to explore chemistry concepts. Always follow your teacher's and laboratory's safety instructions.")
st.sidebar.markdown('<p class="small">Student project • Chemistry + code</p>', unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="eyebrow">CHEMISTRY • DATA • DISCOVERY</div><h1 style="font-size:3.25rem;line-height:1.08">Explore the science<br><span class="gradient">behind every reaction.</span></h1><p class="lead">Welcome to ChemLab AI — an interactive chemistry learning app with a molecular formula analyzer, equation balancing, periodic table explorer, and quick concept checks.</p></div>', unsafe_allow_html=True)

if page == "Overview":
    a,b,c = st.columns(3)
    with a: st.markdown('<div class="panel"><div class="panel-label">01 / Analyze</div><div class="panel-value">Formula Explorer</div><div class="panel-note">Count atoms and estimate molar mass.</div></div>', unsafe_allow_html=True)
    with b: st.markdown('<div class="panel"><div class="panel-label">02 / Understand</div><div class="panel-value">Equation Balancer</div><div class="panel-note">Explore conservation of atoms.</div></div>', unsafe_allow_html=True)
    with c: st.markdown('<div class="panel"><div class="panel-label">03 / Discover</div><div class="panel-value">Periodic Table</div><div class="panel-note">Look up selected element properties.</div></div>', unsafe_allow_html=True)
    st.write("")
    st.subheader("Your chemistry workspace")
    left,right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown("### 🧬 From symbols to structure")
        st.write("A chemical formula tells you which elements are present and how many atoms of each element appear in a substance. The formula analyzer breaks a formula into its elemental counts and estimates its molar mass.")
        st.markdown("### ⚖️ Matter is conserved")
        st.write("A balanced chemical equation has the same number of atoms of each element on both sides. The equation tool helps illustrate this principle for common classroom examples.")
    with right:
        st.markdown("### ✨ Try a quick example")
        example = st.selectbox("Choose a formula", ["H2O", "CO2", "NaCl", "Ca(OH)2", "C6H12O6"])
        if st.button("Analyze example", use_container_width=True):
            try:
                counts = parse_formula(example)
                st.success(f"{example}: " + ", ".join(f"{el} = {n}" for el,n in counts.items()))
                st.metric("Approx. molar mass", f"{formula_mass(counts):.3f} g/mol")
            except ValueError as e:
                st.error(str(e))
    st.info("This is a chemistry-learning tool, not a substitute for a textbook, teacher, or laboratory safety guidance.")

elif page == "Formula Analyzer":
    st.subheader("🧬 Molecular Formula Analyzer")
    st.write("Enter a formula such as `H2O`, `CO2`, `NaCl`, or `Ca(OH)2`. Use correct element capitalization.")
    formula = st.text_input("Chemical formula", value="H2O", max_chars=80)
    if st.button("Analyze formula", type="primary"):
        try:
            counts = parse_formula(formula)
            total = sum(counts.values())
            mass = formula_mass(counts)
            x,y,z = st.columns(3)
            x.metric("Different elements", len(counts))
            y.metric("Total atoms per formula unit", total)
            z.metric("Molar mass", f"{mass:.3f} g/mol")
            st.markdown("#### Element breakdown")
            rows = [{"Symbol": el, "Element": ELEMENTS[el][0], "Atom count": n,
                     "Atomic mass (u)": ELEMENTS[el][2],
                     "Mass contribution (g/mol)": ELEMENTS[el][2]*n} for el,n in counts.items()]
            st.dataframe(rows, use_container_width=True, hide_index=True)
            st.caption("Masses are approximate standard atomic weights. This demo supports a selected set of elements and parentheses; it does not interpret hydrates, ionic charges, or isotope notation.")
        except ValueError as e:
            st.error(str(e))

elif page == "Equation Balancer":
    st.subheader("⚖️ Chemical Equation Balancer")
    st.write("Balance common equations by conserving each element's atom count.")
    equation = st.text_input("Unbalanced equation", value="H2 + O2 -> H2O")
    st.caption("Use + between substances and ->, →, or = between reactants and products.")
    if st.button("Balance equation", type="primary"):
        result, err = balance_equation(equation)
        if result:
            st.success(result)
            st.markdown("**Why it works:** each element has the same total number of atoms on both sides. Only coefficients change; chemical formulas stay the same.")
        else:
            st.error(err or "Unable to balance this equation.")
    st.markdown("#### Try these examples")
    st.code("H2 + O2 -> H2O\nFe + O2 -> Fe2O3\nNa + Cl2 -> NaCl\nC3H8 + O2 -> CO2 + H2O")
    st.caption("The balancer is intended for educational practice and may not handle every unusual equation or reaction type.")

elif page == "Periodic Table":
    st.subheader("🔎 Selected Element Explorer")
    st.write("Search the included set of common elements by symbol or name.")
    choice = st.selectbox("Choose an element", list(ELEMENTS.keys()), format_func=lambda x: f"{x} — {ELEMENTS[x][0]}")
    name, number, mass = ELEMENTS[choice]
    x,y,z = st.columns(3)
    x.metric("Atomic number", number)
    y.metric("Atomic mass", f"{mass:g} u")
    z.metric("Symbol", choice)
    st.markdown(f"### {name} ({choice})")
    st.write(f"**Atomic number:** {number}  \n**Approximate atomic mass:** {mass:g} u  \n**Element symbol:** {choice}")
    st.caption("This is a selected-element lookup, not a complete periodic table. Values are approximate and intended for learning.")

else:
    st.subheader("📚 Learn & Quiz")
    topics = {
        "Atoms and elements": "An atom is the smallest unit of an element that retains its chemical identity. The number of protons determines the element.",
        "Chemical formulas": "Subscripts show how many atoms of an element are represented in a formula. For example, H2O contains two hydrogen atoms and one oxygen atom per molecule.",
        "Conservation of mass": "In an ordinary chemical reaction, atoms are rearranged rather than created or destroyed. A balanced equation reflects this by keeping atom counts equal on both sides.",
        "Moles and molar mass": "One mole contains Avogadro's number of specified entities. Molar mass is the mass of one mole, commonly expressed in grams per mole (g/mol).",
        "Acids and bases": "In the Brønsted–Lowry model, acids donate protons and bases accept protons. The pH scale is commonly used to describe aqueous acidity."
    }
    topic = st.selectbox("Choose a topic", list(topics))
    st.markdown(f'<div class="panel"><div class="panel-label">Study note</div><p style="font-size:1rem;color:#e5edff">{topics[topic]}</p></div>', unsafe_allow_html=True)
    st.write("")
    questions = [
        ("What does the subscript 2 mean in H₂O?", ["Two oxygen atoms", "Two hydrogen atoms", "Two water molecules", "Two elements"], 1, "The 2 applies to H, so each water molecule has two hydrogen atoms."),
        ("What must be equal when an equation is balanced?", ["Molecule colour", "Number of atoms of each element on both sides", "Temperature", "Number of compounds only"], 1, "Balancing conserves the count of each type of atom."),
        ("What is the usual unit of molar mass?", ["g/mol", "cm", "L/s", "°C"], 0, "Molar mass is commonly expressed in grams per mole (g/mol)."),
        ("Which particle determines an element's atomic number?", ["Neutron", "Electron", "Proton", "Molecule"], 2, "The atomic number equals the number of protons in the nucleus.")
    ]
    q, opts, answer, explain = questions[st.session_state.get("quiz_index", 0)]
    st.markdown("### Quick knowledge check")
    st.write(q)
    selected = st.radio("Choose one answer", opts, key=f"quiz_{st.session_state.get('quiz_index',0)}")
    if st.button("Check answer"):
        if opts.index(selected) == answer:
            st.success("Correct! " + explain)
        else:
            st.warning("Not quite. " + explain)
    if st.button("Next question"):
        st.session_state.quiz_index = (st.session_state.get("quiz_index",0) + 1) % len(questions)
        st.rerun()

st.markdown("---")
st.markdown('<p class="small">ChemLab AI · Made for learning and exploration · Verify important calculations with your course materials.</p>', unsafe_allow_html=True)
