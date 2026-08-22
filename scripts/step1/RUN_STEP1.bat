@echo off
setlocal EnableExtensions
cd /d "%~dp0"
set "PROJECT_ROOT=%~dp0.."
set "ANALYSIS=%PROJECT_ROOT%\analysis"
set "LOG=%ANALYSIS%\RUN_STEP1.log"

if not exist "%PROJECT_ROOT%\raw" (
  echo ERROR: raw folder not found: %PROJECT_ROOT%\raw
  exit /b 1
)

if not exist "%ANALYSIS%" mkdir "%ANALYSIS%"
> "%LOG%" echo STEP 1 COMPUTATION STARTED %DATE% %TIME%
python --version >> "%LOG%" 2>&1
if errorlevel 1 (
  echo ERROR: Python is not available on PATH.
  exit /b 1
)

call :run "01_build_cohort.py"
if errorlevel 1 exit /b 1

call :run "02_extract_cif_chemistry.py"
if errorlevel 1 exit /b 1

call :run "03_build_candidate_pairs.py"
if errorlevel 1 exit /b 1

call :run "04_check_metal_coordination.py"
if errorlevel 1 exit /b 1

call :run "05_group_related_pairs.py"
if errorlevel 1 exit /b 1

call :run "06_integrate_adsorption.py.py"
if errorlevel 1 exit /b 1

call :run "07_analyze_adsorption_contrasts.py"
if errorlevel 1 exit /b 1

call :run "08_analyze_unordered_metal_changes.py"
if errorlevel 1 exit /b 1

call :run "09_build_reciprocal_matches.py"
if errorlevel 1 exit /b 1

call :run "10_test_matching_robustness.py"
if errorlevel 1 exit /b 1

call :run "11_audit_topology_sources.py"
if errorlevel 1 exit /b 1

call :run "12_test_topology_robustness.py"
if errorlevel 1 exit /b 1

call :run "13_test_residual_geometry.py"
if errorlevel 1 exit /b 1

call :run "14_test_geometry_limits.py"
if errorlevel 1 exit /b 1

call :run "15_define_primary_pairs.py"
if errorlevel 1 exit /b 1

call :run "16_build_same_chemistry_controls.py"
if errorlevel 1 exit /b 1

call :run "17_compare_same_chemistry_controls.py"
if errorlevel 1 exit /b 1

call :run "18_test_symmetric_control_matching.py"
if errorlevel 1 exit /b 1

call :run "19_audit_boundary_cases.py"
if errorlevel 1 exit /b 1

call :run "20_audit_process_data.py"
if errorlevel 1 exit /b 1

call :run "21_analyze_process_translation.py"
if errorlevel 1 exit /b 1

call :run "22_audit_working_capacity.py"
if errorlevel 1 exit /b 1

call :run "23_finalize_major_metal_results.py"
if errorlevel 1 exit /b 1

call :run "24_select_structure_cases.py"
if errorlevel 1 exit /b 1

call :run "25_inspect_structure_cases.py"
if errorlevel 1 exit /b 1

>> "%LOG%" echo STEP 1 COMPUTATION COMPLETED %DATE% %TIME%
echo.
echo STEP 1 COMPUTATION COMPLETED SUCCESSFULLY
echo Log: %LOG%
exit /b 0

:run
set "SCRIPT=%~1"
echo.
echo ============================================================
echo RUNNING %SCRIPT%
echo ============================================================
>> "%LOG%" echo.
>> "%LOG%" echo ============================================================
>> "%LOG%" echo RUNNING %SCRIPT%  %DATE% %TIME%
>> "%LOG%" echo ============================================================

if not exist "%SCRIPT%" (
  echo ERROR: Missing script %SCRIPT%
  >> "%LOG%" echo ERROR: Missing script %SCRIPT%
  exit /b 1
)

python "%SCRIPT%" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo FAILED: %SCRIPT%
  >> "%LOG%" echo FAILED: %SCRIPT%  %DATE% %TIME%
  echo See: %LOG%
  exit /b 1
)

echo COMPLETED: %SCRIPT%
>> "%LOG%" echo COMPLETED: %SCRIPT%  %DATE% %TIME%
exit /b 0
