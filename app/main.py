from fastapi import FastAPI


app = FastAPI(title="API Project")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "API Project is running"}
