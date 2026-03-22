#!/bin/bash
# Tối ưu luồng CPU cho máy tính trên xe
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4}
exec uvicorn app:app --host 0.0.0.0 --port 8000 --reload
