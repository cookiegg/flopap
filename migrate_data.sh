PGPASSWORD=112358 pg_dump -U flopap_dev -h localhost -p 5433 -d flopap -t paper_translations -t paper_interpretations --data-only --inserts | docker exec -i flopap-db psql -U postgres -d flopap
