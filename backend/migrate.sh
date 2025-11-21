#!/bin/bash

echo "Running database migrations..."
alembic upgrade head
echo "Migrations completed!"
