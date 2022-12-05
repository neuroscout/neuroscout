cd neuroscout/
python manage.py setup_test_db
cd ../
gunicorn -b :4000 neuroscout.core:app --log-level debug --timeout 120 &
cd neuroscout/frontend
cp cypress-test.json cypress.json
cp src/config.ts.example src/config.ts
echo "Starting web server"
yarn start&
