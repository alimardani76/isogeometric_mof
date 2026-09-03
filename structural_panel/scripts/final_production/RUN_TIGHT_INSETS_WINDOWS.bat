@echo off
python 01_check_paths_and_environment.py || goto :eof
python 20_run_tight_insets.py || goto :eof
python 30_collect_tight_insets.py || goto :eof
python 40_validate_tight_insets.py || goto :eof
python 50_zip_for_review.py || goto :eof
echo DONE. Send OVITO_final_insets_tight_REVIEW.zip back to ChatGPT.
