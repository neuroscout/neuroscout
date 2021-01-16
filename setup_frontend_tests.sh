python manage.py setup_test_db
gunicorn -b :4000 neuroscout.core:app --log-level debug --timeout 120 &
cd neuroscout/frontend
cp src/config.ts.example src/config.ts
wait-on http://0.0.0.0:4000/api/datasets
yarn start&
