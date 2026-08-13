#!/bin/sh
set -e

mkdir -p /app/.streamlit

cat > /app/.streamlit/secrets.toml <<EOF
[auth]
redirect_uri = "${STREAMLIT_REDIRECT_URI}"
cookie_secret = "${STREAMLIT_COOKIE_SECRET}"
client_id = "${STREAMLIT_CLIENT_ID}"
client_secret = "${STREAMLIT_CLIENT_SECRET}"
server_metadata_url = "${STREAMLIT_METADATA_URL}"
EOF

chmod 600 /app/.streamlit/secrets.toml

exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0