# Entry point; the actual loop lives in core/pipeline.py
from wraith_app.core.pipeline import Pipeline

def run() -> None:
    print("Starting app...")
    Pipeline().run()

if __name__ == "__main__":
    run()
