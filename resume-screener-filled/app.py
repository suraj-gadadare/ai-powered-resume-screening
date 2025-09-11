import streamlit as st
import pandas as pd
import numpy as np
import re
import qrcode
from io import BytesIO
import matplotlib.pyplot as plt

from utils.extract import extract_text_from_file
from utils.nlp import compute_match_score, extract_skills, summarize_candidate
from utils.pdf_export import export_report_pdf

st.set_page_config(page_title="AI Resume Screener", layout="wide")
st.title("📄 AI-Powered Resume Screening Tool")

# --- SIDEBAR ------------------------------------------------------------------
st.sidebar.header("⚙️ Scoring Weights")
weight_similarity = st.sidebar.slider("Weight: Semantic Similarity", 0.0, 1.0, 0.6)
weight_skills = st.sidebar.slider("Weight: Skills Match", 0.0, 1.0, 0.3)
weight_experience = st.sidebar.slider("Weight: Experience Match", 0.0, 1.0, 0.1)
shortlist_threshold = st.sidebar.slider("Shortlist Threshold (%)", 0, 100, 70)

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Adjust weights to reflect the role emphasis (skills vs. experience).")

# --- TABS ---------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Screening", "📊 Results", "📈 Analytics", "⚡ Insights", "🆚 Compare"
])

# --- TAB 1: SCREENING ---------------------------------------------------------
with tab1:
    st.subheader("Upload Job Description & Resumes")
    col_a, col_b = st.columns([1,1])

    with col_a:
        jd_file = st.file_uploader("Upload Job Description (TXT / DOCX / PDF)", type=["txt", "docx", "pdf"])
    with col_b:
        resumes = st.file_uploader("Upload Resumes (PDF / DOCX)", type=["pdf", "docx"], accept_multiple_files=True)

    run = st.button("▶️ Analyze Resumes", type="primary", use_container_width=True)

    if run and jd_file and resumes:
        jd_text = extract_text_from_file(jd_file)
        jd_skills = extract_skills(jd_text)

        results = []
        for resume in resumes:
            resume_text = extract_text_from_file(resume)

            # Scores
            semantic = compute_match_score(resume_text, jd_text)
            cand_skills = extract_skills(resume_text)
            overlap = len(set(cand_skills) & set(jd_skills))
            skill_score = round((overlap / max(1, len(set(jd_skills)))) * 100, 2)

            exp_match = re.findall(r"(\\d+)\\s*\\+?\\s*(?:years?|yrs)\\b", resume_text.lower())
            exp_years = int(exp_match[0]) if exp_match else 0

            final = round(
                semantic * weight_similarity +
                skill_score * weight_skills +
                min(exp_years, 10) * 10 * weight_experience, 2
            )

            summary = summarize_candidate(resume.name, exp_years, cand_skills[:6], final)

            results.append({
                "Resume": resume.name,
                "Semantic Match %": semantic,
                "Skill Match %": skill_score,
                "Experience (yrs)": exp_years,
                "Final Score": final,
                "Top Skills": ", ".join(cand_skills[:12]),
                "Summary": summary
            })

        df = pd.DataFrame(results).sort_values("Final Score", ascending=False).reset_index(drop=True)
        st.session_state["results"] = df
        st.session_state["jd_text"] = jd_text
        st.session_state["jd_skills"] = jd_skills

        st.success("✅ Screening complete! Open the other tabs to explore results.")
    elif run and (not jd_file or not resumes):
        st.error("Please upload both a Job Description and at least one resume.")

# --- TAB 2: RESULTS + HR NOTES ------------------------------------------------
with tab2:
    if "results" in st.session_state:
        df = st.session_state["results"]
        st.subheader("📊 Ranked Candidates")

        # Initialize notes store
        if "notes" not in st.session_state:
            st.session_state["notes"] = {name: "" for name in df["Resume"]}

        # Render profile cards with expandable notes
        for _, row in df.iterrows():
            with st.expander(f"👤 {row['Resume']} — {row['Final Score']}%"):
                c1, c2, c3 = st.columns([1,1,2])
                with c1:
                    st.metric("Final Score", f"{row['Final Score']}%")
                    st.metric("Experience", f"{row['Experience (yrs)']} yrs")
                with c2:
                    st.metric("Semantic Match", f"{row['Semantic Match %']}%")
                    st.metric("Skill Match", f"{row['Skill Match %']}%")
                with c3:
                    st.write("**Top Skills:**", row["Top Skills"] or "—")
                    st.caption(row["Summary"])

                note = st.text_area(
                    f"✍️ HR Notes — {row['Resume']}",
                    value=st.session_state['notes'].get(row['Resume'], ""),
                    key=f"notes_{row['Resume']}"
                )
                st.session_state["notes"][row["Resume"]] = note

        # Prepare exportable dataframe with notes
        df_notes = df.copy()
        df_notes["HR Notes"] = df_notes["Resume"].map(st.session_state["notes"])
        st.session_state["results_with_notes"] = df_notes

        cdl, cdp = st.columns(2)
        with cdl:
            st.download_button(
                "📥 Download Results + Notes (CSV)",
                df_notes.to_csv(index=False).encode("utf-8"),
                "results_with_notes.csv",
                "text/csv",
                use_container_width=True
            )
        with cdp:
            pdf_bytes = export_report_pdf(df_notes, st.session_state.get("jd_text",""))
            st.download_button(
                "📄 Download Results + Notes (PDF)",
                data=pdf_bytes,
                file_name="results_with_notes.pdf",
                use_container_width=True
            )

# --- TAB 3: ANALYTICS ---------------------------------------------------------
with tab3:
    if "results" in st.session_state:
        df = st.session_state["results"]
        st.subheader("📈 Candidate Analytics")

        col1, col2 = st.columns(2)

        # Score distribution
        with col1:
            st.markdown("**Score Distribution**")
            fig1, ax1 = plt.subplots()
            ax1.hist(df["Final Score"], bins=10)
            ax1.set_xlabel("Final Score (%)")
            ax1.set_ylabel("Count")
            st.pyplot(fig1)

        # Experience distribution
        with col2:
            st.markdown("**Experience Distribution (years)**")
            fig2, ax2 = plt.subplots()
            ax2.hist(df["Experience (yrs)"], bins=10)
            ax2.set_xlabel("Years")
            ax2.set_ylabel("Count")
            st.pyplot(fig2)

        # Skill coverage
        st.markdown("**Skills Coverage vs JD**")
        all_cand_skills = set()
        for s in df["Top Skills"]:
            if isinstance(s, str) and s.strip():
                all_cand_skills.update([x.strip() for x in s.split(",") if x.strip()])
        jd_skills = set(st.session_state.get("jd_skills", []))
        covered = sorted(list(jd_skills & all_cand_skills))
        missing = sorted(list(jd_skills - all_cand_skills))

        col3, col4 = st.columns(2)
        with col3:
            st.success("✅ Covered Skills")
            st.write(", ".join(covered) if covered else "—")
        with col4:
            st.warning("❌ Missing Skills")
            st.write(", ".join(missing) if missing else "—")

# --- TAB 4: INSIGHTS (Auto Shortlist + QR) -----------------------------------
with tab4:
    if "results" in st.session_state:
        df = st.session_state["results"]
        st.subheader("⚡ Insights & Auto Shortlist")

        # Best candidate
        best = df.iloc[0]
        st.markdown(f"**🏆 Best Candidate:** `{best['Resume']}` — **{best['Final Score']}%**")

        # Auto shortlist
        top_n = max(3, int(len(df) * 0.2))
        shortlist = df.nlargest(top_n, "Final Score")
        shortlist = shortlist[shortlist["Final Score"] >= shortlist_threshold]

        if not shortlist.empty:
            st.success(f"✅ Auto-shortlisted {len(shortlist)} candidate(s) (threshold ≥ {shortlist_threshold}%)")
            st.dataframe(shortlist, use_container_width=True)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "📥 Download Shortlist (CSV)",
                    shortlist.to_csv(index=False).encode("utf-8"),
                    "shortlist.csv",
                    "text/csv",
                    use_container_width=True
                )
            with c2:
                shortlist_pdf = export_report_pdf(shortlist, st.session_state.get("jd_text",""))
                st.download_button(
                    "📄 Download Shortlist (PDF)",
                    shortlist_pdf,
                    "shortlist.pdf",
                    use_container_width=True
                )
        else:
            st.warning("No candidates met the current threshold. Try lowering it from the sidebar.")

        st.markdown("---")
        st.subheader("📱 Share App with HR")
        url = st.text_input("App URL (for QR)", value="https://share.streamlit.io/your-username/your-repo/main/app.py")
        qr = qrcode.QRCode(version=1, box_size=6, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = BytesIO()
        img.save(buf, format="PNG")
        st.image(buf.getvalue(), caption="Scan to open this app")

# --- TAB 5: COMPARE -----------------------------------------------------------
with tab5:
    if "results" in st.session_state:
        df = st.session_state["results"]
        st.subheader("🆚 Compare Candidates")

        selected = st.multiselect("Select up to 3 candidates", df["Resume"].tolist())
        if selected:
            compare_df = df[df["Resume"].isin(selected)]

            # Summary table
            st.dataframe(compare_df.set_index("Resume")[
                ["Final Score", "Semantic Match %", "Skill Match %", "Experience (yrs)", "Top Skills"]
            ], use_container_width=True)

            # Final Score bar chart
            st.markdown("### 📊 Final Score Comparison")
            fig3, ax3 = plt.subplots()
            ax3.bar(compare_df["Resume"], compare_df["Final Score"])
            ax3.set_ylabel("Final Score (%)")
            st.pyplot(fig3)

            # Skill vs Semantic grouped bar
            st.markdown("### 📊 Skill vs Semantic Match")
            idx = np.arange(len(compare_df))
            width = 0.35
            fig4, ax4 = plt.subplots()
            ax4.bar(idx - width/2, compare_df["Skill Match %"], width, label="Skill Match %")
            ax4.bar(idx + width/2, compare_df["Semantic Match %"], width, label="Semantic Match %")
            ax4.set_xticks(idx)
            ax4.set_xticklabels(compare_df["Resume"])
            ax4.set_ylabel("%")
            ax4.legend()
            st.pyplot(fig4)

            # Radar chart
            st.markdown("### 🕸️ Strength Profile (Radar)")
            categories = ["Final Score", "Skill Match %", "Semantic Match %", "Experience (yrs)"]
            num_vars = len(categories)
            angles = np.linspace(0, 2*np.pi, num_vars, endpoint=False).tolist()
            angles += angles[:1]

            fig5, ax5 = plt.subplots(figsize=(6,6), subplot_kw=dict(polar=True))
            for _, r in compare_df.iterrows():
                values = [
                    r["Final Score"],
                    r["Skill Match %"],
                    r["Semantic Match %"],
                    r["Experience (yrs)"] * 10
                ]
                values += values[:1]
                ax5.plot(angles, values, label=r["Resume"])
                ax5.fill(angles, values, alpha=0.15)
            ax5.set_xticks(np.linspace(0, 2*np.pi, num_vars, endpoint=False))
            ax5.set_xticklabels(categories)
            ax5.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
            st.pyplot(fig5)