from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import sys

# Add pipeline tools to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.platforms import PLATFORMS, NESConfig
from pipeline.ai import AIAnalyzer, GenerativeResizer

app = FastAPI(title="ARDK Studio API")

class ConvertRequest(BaseModel):
    input_path: str
    output_dir: str
    platform: str = "nes"
    mode: str = "default"  # default, generative
    optimize: bool = True
    reserved_status_height: int = 0
    
from unified_pipeline import UnifiedPipeline

@app.get("/platforms")
def get_platforms():
    return {k: v.name for k, v in PLATFORMS.items()}

@app.post("/convert")
def convert_asset(req: ConvertRequest):
    try:
        # Initialize Pipeline
        pipeline = UnifiedPipeline(
            target_size=32, # Default
            platform=req.platform,
            use_ai=True,
            mode=req.mode,
            strict=False
        )
        
        # Override pipeline settings dynamically based on request
        pipeline.optimize_tiles = req.optimize
        pipeline.reserved_status_height = req.reserved_status_height
        
        # Run Process
        result = pipeline.process(req.input_path, req.output_dir)
        
        if not result:
             raise HTTPException(status_code=500, detail="Pipeline processing failed")
             
        return {
            "status": "success",
            "message": f"Processed {os.path.basename(req.input_path)}",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnalyzeRequest(BaseModel):
    input_path: str
    prompt: str = "Describe this sprite"
    provider: str = None

@app.post("/analyze")
def analyze_asset(req: AnalyzeRequest):
    try:
        analyzer = AIAnalyzer(preferred_provider=req.provider)
        if not analyzer.available:
             raise HTTPException(status_code=503, detail="No AI provider available")
             
        from PIL import Image
        img = Image.open(req.input_path)
        
        result = analyzer.analyze_prompt(img, req.prompt)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
