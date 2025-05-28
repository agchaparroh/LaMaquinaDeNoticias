from fastapi import FastAPI

app = FastAPI(
    title="Connector Module",
    description="API for the Supabase Connector Module of La Máquina de Noticias.",
    version="0.1.0"
)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Connector Module API"}

@app.get("/health")
async def health_check():
    return {"status": "Connector module is healthy"}

# Add more endpoints specific to the connector module
# For example, to interact with Supabase tables, storage, etc.
