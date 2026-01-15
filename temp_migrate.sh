PGPASSWORD=postgres pg_dump -U postgres -h localhost -d flopap_dev -t paper_translations -t paper_interpretations --data-only --inserts | docker exec -i flopap-db psql -U postgres -d flopap
