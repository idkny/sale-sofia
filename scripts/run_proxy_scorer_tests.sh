#!/bin/bash
cd /home/wow/Projects/sale-sofia
python -m pytest tests/test_proxy_scorer.py -v --tb=short
