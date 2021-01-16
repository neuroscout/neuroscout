python manage.py setup_test_db
/usr/local/bin/gunicorn -b :4000 neuroscout.core:app --log-level debug --timeout 120 &
cd neuroscout/frontend
mv src/config.ts src/config.ts.example
cp src/config.ts.example src/config.ts
wait-on http://0.0.0.0:4000/api/datasets
yarn start&
