
import pixellab
import inspect
from configs.api_keys import PIXELLAB_API_KEY

def inspect_sdk():
    client = pixellab.Client(secret=PIXELLAB_API_KEY)
    print(f"Methods: {[m for m in dir(client) if not m.startswith('_')]}")
    
    if hasattr(client, 'rotate'):
        sig = inspect.signature(client.rotate)
        print(f"client.rotate signature: {sig}")
        print(f"client.rotate doc: {client.rotate.__doc__}")

if __name__ == "__main__":
    inspect_sdk()
