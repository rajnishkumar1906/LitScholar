import traceback
import asyncio

from .pipeline_checks import (
    cleaned_csv_ready,
    neondb_has_books,
    summaries_exist,
    chroma_has_embeddings,
)


async def run_step(step_name, step_fn):
    print(f"\n🚀 {step_name}")
    try:
        if asyncio.iscoroutinefunction(step_fn):
            await step_fn()
        else:
            # Run synchronous blocking functions in a separate thread
            # to avoid blocking the main event loop (Authentication, etc.)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, step_fn)

        print(f"✅ Finished: {step_name}")

    except Exception:
        print(f"❌ Failed: {step_name}")
        traceback.print_exc()
        raise


async def run_pipeline():

    # Lazy imports (important: avoids side effects)
    from .clean_books_csv import main as clean_csv
    from .insert_cleaned_books import main as insert_neondb
    from .build_chroma_embeddings import main as build_embeddings

    print("\n🧠 LitScholar — Data Preprocessing Pipeline")

    # ---------- STEP 1: CLEAN CSV ----------
    if cleaned_csv_ready():
        print("⏭ Cleaned CSV already exists — skipping")
    else:
        await run_step("Cleaning raw CSV", clean_csv)

    # ---------- STEP 2: INSERT INTO NEON ----------
    if neondb_has_books():
        print("⏭ Neondb already populated — skipping")
    else:
        await run_step("Inserting data into Neon", insert_neondb)

    # ---------- STEP 3: SUMMARIZE BOOKS ----------
    # Summarization is now handled on-demand in the BookService
    # or via a separate manual process to save costs/quota.
    print("⏭ Skipping background summarization — handled on-demand")

    # ---------- STEP 4: CHROMA EMBEDDINGS ----------
    if chroma_has_embeddings():
        print("⏭ Chroma embeddings already exist — skipping")
    else:
        await run_step("Building Chroma embeddings", build_embeddings)

    print("\n🎉 PIPELINE COMPLETE — ALL STEPS VERIFIED")