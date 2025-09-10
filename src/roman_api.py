from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text
from roman import roman_to_int_logic, int_to_roman_logic
from errors import RomanFormatError, ArabicRangeError, NumberError
from postgresql_db import get_connection

app = FastAPI()


@app.get("/")
def health():
    return {"ok": True}


@app.on_event("startup")
def init_db():
    ddl = """
    CREATE TABLE IF NOT EXISTS conversion_logs (
        id SERIAL PRIMARY KEY,
        input_value TEXT NOT NULL,
        result_value TEXT NOT NULL,
        conversion_direction TEXT NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
    """
    with get_connection() as conn:
        conn.execute(text(ddl))
        conn.commit()


@app.get("/to-int")
def to_int_endpoint(roman: str = Query(..., description="Roman numeral to convert")):
    try:
        result = roman_to_int_logic(roman)
        with get_connection() as conn:
            conn.execute(
                text("""INSERT INTO conversion_logs (input_value, result_value, conversion_direction)
                        VALUES (:input_value, :result_value, :direction)"""),
                {
                    "input_value": roman,
                    "result_value": str(result),
                    "direction": "to_int",
                },
            )
            conn.commit()
        return {"value": result}
    except RomanFormatError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NumberError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/to-roman")
def to_roman_endpoint(number: int = Query(..., description="Integer to convert")):
    try:
        result = int_to_roman_logic(number)
        with get_connection() as conn:
            conn.execute(
                text("""INSERT INTO conversion_logs (input_value, result_value, conversion_direction)
                        VALUES (:input_value, :result_value, :direction)"""),
                {
                    "input_value": str(number),
                    "result_value": result,
                    "direction": "to_roman",
                },
            )
            conn.commit()
        return {"value": result}
    except ArabicRangeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except NumberError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
