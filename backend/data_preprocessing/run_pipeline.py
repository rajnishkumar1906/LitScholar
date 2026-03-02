import sys
import traceback

from pipeline_checks import (
    cleaned_csv_ready,
    neondb_has_books,
    chroma_has_embeddings,
)

def run_step(step_name, step_fn):
    print(f"\n🚀 {step_name}")
    try:
        step_fn()
        print(f"✅ Finished: {step_name}")
    except Exception:
        print(f"❌ Failed: {step_name}")
        traceback.print_exc()
        sys.exit(1)


def main():
    # Lazy imports (important: avoids side effects)
    from clean_books_csv import main as clean_csv
    from insert_cleaned_books import main as insert_neondb
    from build_chroma_embeddings import main as build_embeddings

    print("\n🧠 LitScholar — Data Preprocessing Pipeline")

    # ---------- STEP 1: CLEAN CSV ----------
    if cleaned_csv_ready():
        print("⏭ Cleaned CSV already exists — skipping")
    else:
        run_step("Cleaning raw CSV", clean_csv)

    # ---------- STEP 2: SUPABASE ----------
    if neondb_has_books():
        print("⏭ Neondb already populated — skipping")
    else:
        run_step("Inserting data into neon", insert_neondb)

    # ---------- STEP 3: CHROMA EMBEDDINGS ----------
    if chroma_has_embeddings():
        print("⏭ Chroma embeddings already exist — skipping")
    else:
        run_step("Building Chroma embeddings", build_embeddings)

    print("\n🎉 PIPELINE COMPLETE — ALL STEPS VERIFIED")


if __name__ == "__main__":
    main()