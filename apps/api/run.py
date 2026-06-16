from apps.api.app import create_app
import os

app = create_app()

def main():
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    app.run(host="0.0.0.0", port=port, debug=debug)

if __name__ == '__main__':
    main()
