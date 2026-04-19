import json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

data_file = Path(__file__).parent / "data.json"
with data_file.open("r", encoding="utf-8") as f:
    records = json.load(f)


def binary_search_records_by_prn_suffix(sorted_records: list[dict], target: int) -> list[dict]:
    keys = [int(rec.get("prn", "")[-2:]) if rec.get("prn", "").isdigit() and len(rec.get("prn", "")) >= 2 else -1 for rec in sorted_records]
    lo = 0
    hi = len(keys) - 1
    found_index = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if keys[mid] == target:
            found_index = mid
            break
        if keys[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    if found_index is None:
        return []
    start = found_index
    while start - 1 >= 0 and keys[start - 1] == target:
        start -= 1
    end = found_index
    while end + 1 < len(keys) and keys[end + 1] == target:
        end += 1
    return sorted_records[start : end + 1]


def search_records(query: str):
    query_text = query.strip().lower()
    if not query_text:
        return []

    digits = "".join(ch for ch in query_text if ch.isdigit())
    results = []

    for record in records:
        name = record.get("name", "").lower()
        prn = record.get("prn", "").lower()
        department = record.get("department", "").lower()
        year = record.get("year", "").lower()

        if query_text in name or query_text in prn or query_text in department or query_text in year:
            results.append(record)

    if results:
        return results

    if len(digits) >= 2:
        target_suffix = int(digits[-2:])
        sorted_records = sorted(
            records,
            key=lambda record: int(record.get("prn", "")[-2:]) if record.get("prn", "").isdigit() and len(record.get("prn", "")) >= 2 else -1,
        )
        return binary_search_records_by_prn_suffix(sorted_records, target_suffix)

    return []


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request, "message": "Welcome to PRN finder", "results": []})


@app.post("/", response_class=HTMLResponse)
async def search(request: Request):
    form = await request.form()
    query = form.get("query", "")
    results = search_records(query)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "results": results,
            "query": query,
            "message": "Welcome to PRN finder",
        },
    )

